"""
Script de chargement MinIO (S3 Data Lake) -> PostgreSQL Data Warehouse (raw_odoo)
Ce script extrait les fichiers JSONL synchronisés par Airbyte dans MinIO
et les charge directement dans le schéma 'raw_odoo' de PostgreSQL (warehouse-db)
afin de permettre l'exécution des transformations dbt.
"""

import json
import gzip
import io
import os
import psycopg2
from psycopg2 import sql
import urllib.request
import urllib.parse
import hmac
import hashlib
from datetime import datetime

# --- Configuration MinIO ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio_admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio_admin_password_secret")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "crui-raw")

# --- Configuration PostgreSQL Warehouse ---
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5433"))
PG_DB = os.getenv("PG_DB", "warehouse")
PG_USER = os.getenv("PG_USER", "analytical_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "analytical_password_secret")

TABLES_TO_SYNC = [
    "projet",
    "dossier",
    "soumission",
    "enquete",
    "prefecture",
    "commune",
    "foncier",
    "secteur",
    "macrosecteur",
    "act",
    "action",
    "commission_crui",
    "res_partner",
    "res_users"
]

def get_s3_headers(method, path, body=b""):
    """Génère les en-têtes d'authentification AWS V4 / MinIO simples pour l'API REST."""
    # Authentification Basic fallback pour MinIO API
    import base64
    auth_str = f"{MINIO_ACCESS_KEY}:{MINIO_SECRET_KEY}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {b64_auth}"}

def get_pg_connection():
    """Établit la connexion à PostgreSQL Warehouse."""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )

def ensure_schema_exists(cursor):
    """Crée le schéma raw_odoo s'il n'existe pas."""
    cursor.execute("CREATE SCHEMA IF NOT EXISTS raw_odoo;")

def flatten_and_load_table(cursor, table_name, records):
    """Charge une liste de dictionnaires JSON dans la table PostgreSQL correspondante."""
    if not records:
        print(f"  [INFO] Aucun enregistrement trouvé pour la table {table_name}.")
        return

    # Extraire toutes les colonnes uniques
    columns = set()
    for row in records:
        # Airbyte peut stocker la ligne sous _airbyte_data ou directement les clés
        data = row.get("_airbyte_data", row)
        columns.update(data.keys())

    columns = sorted(list(columns))
    
    # Nettoyer les noms de colonnes
    safe_cols = [c.replace("-", "_").lower() for c in columns]

    # Créer la table si elle n'existe pas
    col_definitions = [f'"{col}" TEXT' for col in safe_cols]
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS raw_odoo."{table_name}" (
        _airbyte_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        {', '.join(col_definitions)}
    );
    """
    cursor.execute(create_table_query)

    # Vider la table pour un rechargement complet (Full Refresh de la couche raw)
    cursor.execute(f'TRUNCATE TABLE raw_odoo."{table_name}";')

    # Insérer les données
    insert_sql = sql.SQL(
        'INSERT INTO raw_odoo.{table} ({fields}) VALUES ({values})'
    ).format(
        table=sql.Identifier(table_name),
        fields=sql.SQL(', ').join(map(sql.Identifier, safe_cols)),
        values=sql.SQL(', ').join(sql.Placeholder() * len(safe_cols))
    )

    insert_rows = []
    for row in records:
        data = row.get("_airbyte_data", row)
        row_values = [
            json.dumps(data[col]) if isinstance(data.get(col), (dict, list))
            else (str(data.get(col)) if data.get(col) is not None else None)
            for col in columns
        ]
        insert_rows.append(row_values)

    cursor.executemany(insert_sql, insert_rows)
    print(f"  [SUCCES] Table raw_odoo.{table_name} : {len(insert_rows)} lignes insérées.")

def list_and_read_minio_objects():
    """Lit les objets JSONL depuis MinIO en utilisant docker mc."""
    try:
        import subprocess
        # Configurer l'alias MinIO en premier
        subprocess.run(
            ["docker", "exec", "minio", "mc", "alias", "set", "local", "http://localhost:9000", MINIO_ACCESS_KEY, MINIO_SECRET_KEY],
            capture_output=True,
            text=True
        )
        print("[INFO] Récupération de la liste des fichiers dans MinIO...")
        cmd = ["docker", "exec", "minio", "mc", "ls", "--recursive", f"local/{MINIO_BUCKET}/"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        lines = result.stdout.strip().split("\n")
        table_files = {}

        for line in lines:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 5:
                filepath = parts[-1]
                for tbl in TABLES_TO_SYNC:
                    if f"/{tbl}/" in filepath or filepath.endswith(f"_{tbl}.jsonl"):
                        table_files.setdefault(tbl, []).append(filepath)

        return table_files

    except Exception as e:
        print(f"[ERREUR] Impossible de lister les fichiers MinIO : {e}")
        return {}

def download_and_parse_jsonl(filepath):
    """Télécharge le contenu d'un fichier JSONL depuis MinIO via Docker mc cat."""
    import subprocess
    cmd = ["docker", "exec", "minio", "mc", "cat", f"local/{MINIO_BUCKET}/{filepath}"]
    result = subprocess.run(cmd, capture_output=True)
    
    content = result.stdout
    if filepath.endswith(".gz"):
        content = gzip.decompress(content)

    records = []
    for line in content.decode("utf-8", errors="ignore").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line.strip()))
            except Exception:
                pass
    return records

def main():
    print("=" * 60)
    print("DEMARRAGE DU CHARGEMENT : MinIO (S3) -> PostgreSQL (raw_odoo)")
    print("=" * 60)

    table_files = list_and_read_minio_objects()
    if not table_files:
        print("[AVERTISSEMENT] Aucun fichier de données trouvé dans le bucket MinIO.")
        return

    conn = get_pg_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        ensure_schema_exists(cursor)

        for tbl, files in table_files.items():
            print(f"\n[TRAITEMENT] Table '{tbl}' ({len(files)} fichier(s))...")
            all_records = []
            for f in files:
                records = download_and_parse_jsonl(f)
                all_records.extend(records)
            
            flatten_and_load_table(cursor, tbl, all_records)

        conn.commit()
        print("\n" + "=" * 60)
        print("[TERMINE] Toutes les tables ont été chargées dans raw_odoo avec succès !")
        print("Vous pouvez maintenant exécuter : dbt run")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"[ERREUR CRITIQUE] : {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
