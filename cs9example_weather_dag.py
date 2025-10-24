from datetime import datetime
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s
from teams.config import get_team_config

# Team configuration: This DAG belongs to the norsyss team
TEAM_NAME = "norsyss"
TEAM_CONFIG = get_team_config(TEAM_NAME)

# Default resource limits for all cs9 tasks
DEFAULT_CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    limits={"cpu": "1", "memory": "4Gi"}
)

# Reusable environment variables for all cs9 tasks
CS9_ENV_VARS = {
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
}

with DAG(
    dag_id="cs9example_weather_download",
    start_date=datetime(2024, 1, 1),
    schedule="0 * * * *",
    catchup=False,
    tags=["cs9", "weather", "example"],
) as dag:

    weather_download_and_import_rawdata = KubernetesPodOperator(
        task_id="weather_download_and_import_rawdata",
        image="ghcr.io/fhidev/fhi.fida.cs/cs9base:latest",
        image_pull_policy="Always",
        cmds=["/usr/local/bin/install_ss_and_run_task_k8s.sh"],
        arguments=[
            "https://github.com/csids/cs9example.git",
            "main",
            "weather_download_and_import_rawdata"
        ],
        env_vars=CS9_ENV_VARS,
        container_resources=DEFAULT_CONTAINER_RESOURCES,
        name="cs9_weather_download_and_import_rawdata",
        namespace="tn-fida-airflow",
        service_account_name=TEAM_CONFIG["service_account_name"],
        is_delete_operator_pod=False,
    )

    weather_clean_data = KubernetesPodOperator(
        task_id="weather_clean_data",
        image="ghcr.io/fhidev/fhi.fida.cs/cs9base:latest",
        image_pull_policy="Always",
        cmds=["/usr/local/bin/install_ss_and_run_task_k8s.sh"],
        arguments=[
            "https://github.com/csids/cs9example.git",
            "main",
            "weather_clean_data"
        ],
        env_vars=CS9_ENV_VARS,
        container_resources=DEFAULT_CONTAINER_RESOURCES,
        name="cs9_weather_clean_data",
        namespace="tn-fida-airflow",
        service_account_name=TEAM_CONFIG["service_account_name"],
        is_delete_operator_pod=False,
    )

    # Task dependencies
    weather_download_and_import_rawdata >> weather_clean_data