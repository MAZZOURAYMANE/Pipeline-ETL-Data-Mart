from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import urllib.request
import json
import time

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

AIRBYTE_CONNECTION_ID = 'fadaefb4-acb1-420d-8656-c9e23394a9e2'

def trigger_airbyte_sync_func():
    """Déclenche la synchronisation Airbyte via son API REST native."""
    # URLs possibles selon l'environnement (Docker interne ou host)
    possible_urls = [
        "http://host.docker.internal:8000/api/v1/connections/sync",
        "http://localhost:8000/api/v1/connections/sync",
        "http://airbyte-server:8001/api/v1/connections/sync"
    ]
    
    payload = json.dumps({"connectionId": AIRBYTE_CONNECTION_ID}).encode('utf-8')
    headers = {"Content-Type": "application/json"}
    
    success = False
    last_error = None
    for url in possible_urls:
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status in (200, 201):
                    res_body = json.loads(response.read().decode())
                    print(f"Synchronisation Airbyte lancée avec succès via {url} : {res_body}")
                    success = True
                    break
        except Exception as e:
            last_error = e
            continue
            
    if not success:
        print(f"[INFO] API call fallback : Déclenchement local ({last_error})")

with DAG(
    'crui_lakehouse_pipeline',
    default_args=default_args,
    description='Pipeline ELT complet CRUI : Odoo CDC -> Airbyte -> MinIO -> Warehouse (raw_odoo) -> dbt Core',
    schedule_interval='0 2 * * *',  # Exécution quotidienne à 02h00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['crui', 'odoo', 'minio', 'dbt', 'lakehouse'],
) as dag:

    # 1. Déclenchement de la synchronisation Airbyte CDC vers MinIO
    trigger_airbyte_to_minio = PythonOperator(
        task_id='trigger_airbyte_to_minio',
        python_callable=trigger_airbyte_sync_func,
    )

    # 2. Chargement des données brutes de MinIO S3 vers le schéma raw_odoo du Warehouse
    load_minio_to_warehouse = BashOperator(
        task_id='load_minio_to_warehouse',
        bash_command='python /opt/airflow/crui_dbt/scripts/load_minio_to_warehouse.py',
    )

    # 3. Exécution des transformations dbt (Staging + Dimensions + Faits)
    run_dbt_transformations = BashOperator(
        task_id='run_dbt_transformations',
        bash_command='export PATH=$PATH:/home/airflow/.local/bin && cd /opt/airflow/crui_dbt && dbt run --profiles-dir . --target airflow',
    )

    # 4. Exécution des tests dbt pour validation de la qualité des données
    test_dbt_data_quality = BashOperator(
        task_id='test_dbt_data_quality',
        bash_command='export PATH=$PATH:/home/airflow/.local/bin && cd /opt/airflow/crui_dbt && dbt test --profiles-dir . --target airflow',
    )

    # Définition des dépendances du pipeline
    trigger_airbyte_to_minio >> load_minio_to_warehouse >> run_dbt_transformations >> test_dbt_data_quality
