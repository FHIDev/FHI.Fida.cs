from datetime import datetime
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

with DAG(
    dag_id="cs9example_weather_download",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    tags=["cs9", "weather", "example"],
) as dag:

    weather_download_task = KubernetesPodOperator(
        task_id="weather_download_and_import",
        image="ghcr.io/fhidev/fhi.fida.cs/cs9base:latest",
        image_pull_policy="Always",
        cmds=["/usr/local/bin/install_ss_and_run_task_k8s.sh"],
        arguments=[
            "https://github.com/csids/cs9example.git",
            "main",
            "weather_download_and_import_rawdata"
        ],
        env_vars={
            "CS9_DBCONFIG_USER": "yourusername",
            "CS9_DBCONFIG_PASSWORD": "yourStrongPassword100",
            "CS9_AUTO": "0",
            "CS9_PATH": "/cs9path",
            "CS9_DBCONFIG_ACCESS": "config/anon",
            "CS9_DBCONFIG_DRIVER": "PostgreSQL Unicode",
            "CS9_DBCONFIG_PORT": "5432",
            "CS9_DBCONFIG_SSLMODE": "no",
            "CS9_DBCONFIG_ROLE_CREATE_TABLE": "yourusername",
            "CS9_DBCONFIG_SERVER": "db",
            "CS9_DBCONFIG_SCHEMA_CONFIG": "public",
            "CS9_DBCONFIG_DB_CONFIG": "postgres",
            "CS9_DBCONFIG_SCHEMA_ANON": "public",
            "CS9_DBCONFIG_DB_ANON": "postgres"
        },
        name="cs9example-weather-pod",
        namespace="ns-cs9-test",
        is_delete_operator_pod=True,
    )