# Odoo → Airbyte → MinIO Integration Plan

## Background

Your stack already has:
- **Odoo** running against a **PostgreSQL 15** database (port `5434` on the host)
- **MinIO** as a data lake/staging layer (port `9000`)
- **Airflow** for orchestration
- A rich `data_engineering_spec.md` defining all source tables and relationships

The goal is to wire Airbyte OSS into this stack so it reads all CRUI tables from the Odoo PostgreSQL database and lands raw JSON/Parquet files in MinIO for the next dbt transform stage.

---

## Architecture

```
Odoo PostgreSQL (port 5434)
        │
        │  WAL Logical Replication (CDC)  ← preferred
        │  OR write_date incremental       ← fallback
        ▼
Airbyte OSS (port 8000 UI / 8001 API)
   ├── Source: source-postgres (airbyte/source-postgres:3.8.4)
   └── Destination: destination-s3 → MinIO
        │
        ▼
MinIO  (s3://crui-raw/  bucket)
        │
        ▼
  dbt Core (already wired in Airflow)
        │
        ▼
  warehouse-db (PostgreSQL analytical)
```

---

## User Review Required

> [!IMPORTANT]
> **PostgreSQL WAL / Logical Replication**: CDC (the recommended sync mode) requires enabling `wal_level = logical` in the Odoo PostgreSQL container. This means adding a custom `postgresql.conf` or command-line override in `docker-compose.yml`. The Odoo database will need to be **restarted once** for the setting to take effect. All existing data is preserved; this only changes how Postgres writes its WAL logs.

> [!WARNING]
> **Airbyte OSS resource usage**: Airbyte OSS (the open-source self-hosted version) requires several Docker containers (`airbyte-server`, `airbyte-webapp`, `airbyte-temporal`, `airbyte-db`, `airbyte-connector-runner`). On a development machine this adds roughly **2–4 GB RAM** usage. Make sure your Docker Desktop has enough memory allocated.

> [!IMPORTANT]
> **Port conflicts**: Airbyte OSS uses ports `8000` (UI) and `8001` (API). If those are already taken on your machine, we can remap them.

---

## Open Questions

> [!IMPORTANT]
> 1. **CDC vs. Incremental?**  Do you want full CDC (WAL logical replication — near real-time, captures deletes) or timestamp-based incremental (simpler, no WAL config needed, but misses hard deletes)?  The plan below defaults to **CDC** but can easily be switched.
> 2. **MinIO bucket name?** Defaulting to `crui-raw`. Change if needed.
> 3. **Sync schedule?** Defaulting to **every 6 hours** via Airbyte's built-in scheduler + an Airflow trigger DAG. Adjust as needed.

---

## Proposed Changes

### Component 1 — PostgreSQL WAL Configuration

#### [MODIFY] [docker-compose.yml](file:///c:/Users/AYMANE/Desktop/odoo-docker/docker-compose.yml)
Add `command` override to the `db` service to enable logical replication:
```yaml
command: >
  postgres
  -c wal_level=logical
  -c max_replication_slots=4
  -c max_wal_senders=4
```

---

### Component 2 — Airbyte OSS Docker Services

#### [MODIFY] [docker-compose.yml](file:///c:/Users/AYMANE/Desktop/odoo-docker/addons/crui/docker-compose.yml)
Add the full Airbyte OSS service block (using the official `airbyte/airbyte-bootloader` + `airbyte/server` + `airbyte/webapp` + `temporal` pattern) to the existing crui stack.

---

### Component 3 — Airbyte Connection Configuration Files

These JSON files are used to register the source and destination programmatically (via Airbyte API or manually in the UI).

#### [NEW] `airbyte/configs/source_odoo_postgres.json`
Source connector config pointing at the Odoo PostgreSQL DB:
```json
{
  "host": "db",
  "port": 5432,
  "database": "postgres",
  "username": "odoo",
  "password": "odoo",
  "replication_method": {
    "method": "CDC",
    "replication_slot": "airbyte_slot",
    "publication": "airbyte_publication"
  },
  "schemas": ["public"],
  "ssl_mode": {"mode": "disable"}
}
```

#### [NEW] `airbyte/configs/destination_minio.json`
Destination connector config for MinIO (S3-compatible):
```json
{
  "s3_endpoint": "http://minio:9000",
  "s3_bucket_name": "crui-raw",
  "s3_bucket_region": "us-east-1",
  "access_key_id": "minio_admin",
  "secret_access_key": "minio_admin_password_secret",
  "format": {
    "format_type": "JSONL",
    "compression": {"compression_type": "GZIP"}
  },
  "s3_path_format": "${NAMESPACE}/${STREAM_NAME}/${YEAR}/${MONTH}/${DAY}/${EPOCH}"
}
```

#### [NEW] `airbyte/configs/streams_catalog.json`
Declares all 22 streams (tables + M2M join tables) to sync, with `incremental` + `append` sync mode for fact tables and `full_refresh` for dimension tables.

---

### Component 4 — PostgreSQL CDC Setup Script

#### [NEW] `airbyte/scripts/setup_cdc.sql`
SQL script to run once against the Odoo PostgreSQL to create the replication slot and publication:
```sql
-- Run as superuser (odoo user has SUPERUSER in this setup)
SELECT pg_create_logical_replication_slot('airbyte_slot', 'pgoutput');

CREATE PUBLICATION airbyte_publication FOR TABLE
  projet, dossier, soumission, enquete, commission_crui,
  action, act, commune, prefecture, secteur, macrosecteur,
  foncier, conseiller, visite, res_partner, res_users,
  projet_secteur_rel, projet_foncier_rel, projet_macrosecteur_rel,
  dossier_act_rel, dossier_action_rel, soumission_act_rel,
  commission_crui_res_partner_rel;
```

---

### Component 5 — MinIO Bucket Init Script

#### [NEW] `airbyte/scripts/init_minio_bucket.sh`
Shell script (runs via a one-shot Docker container) to create the `crui-raw` bucket in MinIO on first startup.

---

### Component 6 — Airflow DAG: Airbyte Trigger

#### [NEW] `airflow/dags/airbyte_trigger_dag.py`
An Airflow DAG that uses the `AirbyteTriggerSyncOperator` to programmatically trigger Airbyte connection syncs on a schedule, so Airflow remains the single orchestration point:
```python
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator

airbyte_sync = AirbyteTriggerSyncOperator(
    task_id='sync_odoo_to_minio',
    airbyte_conn_id='airbyte_conn',
    connection_id='<AIRBYTE_CONNECTION_UUID>',  # filled after first setup
    asynchronous=False,
)
```

---

### Component 7 — Airbyte API Bootstrap Script

#### [NEW] `airbyte/scripts/bootstrap_connection.py`
A Python script using the Airbyte API to automatically:
1. Create the Odoo PostgreSQL source
2. Create the MinIO destination
3. Create and configure the connection with the full streams catalog
4. Save the generated `connection_id` back to a config file for Airflow

---

## Verification Plan

### Automated Tests
- Run `setup_cdc.sql` against the Odoo PostgreSQL and verify the replication slot and publication are created.
- Run the bootstrap script and verify the Airbyte connection appears in the UI at `http://localhost:8000`.
- Trigger a manual sync and verify files appear in MinIO at `http://localhost:9001` (MinIO console).

### Manual Verification
1. Open Airbyte UI → `http://localhost:8000` → confirm source and destination are healthy.
2. Trigger a sync and check MinIO console (`http://localhost:9001`) → `crui-raw` bucket for incoming JSONL.gz files.
3. Make a change in Odoo (edit a `projet`) and verify the next sync picks it up via CDC.
