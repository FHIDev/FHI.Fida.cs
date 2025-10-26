from datetime import datetime
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s
from teams.config import get_team_config

# Team configuration: This DAG belongs to the norsyss team
TEAM_NAME = "norsyss"
TEAM_CONFIG = get_team_config(TEAM_NAME)

# Default resource limits for all cs9 tasks (must not exceed Kyverno policy: CPU <= 2, Memory <= 2Gi)
DEFAULT_CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    requests={"cpu": "1", "memory": "2Gi"},
    limits={"cpu": "1", "memory": "2Gi"}
)

# Reusable environment variables for all cs9 tasks
# Database credentials point to norsyss_test database on airflow-cs9-test.postgres.database.azure.com
CS9_ENV_VARS = {
    "CS9_DBCONFIG_USER": "norsyss_user",
    "CS9_DBCONFIG_PASSWORD": "NorsyssTestPass!23#Secure",
    "CS9_AUTO": "0",
    "CS9_PATH": "/work",
    "CS9_DBCONFIG_ACCESS": "config/anon",
    "CS9_DBCONFIG_DRIVER": "PostgreSQL Unicode",
    "CS9_DBCONFIG_PORT": "5432",
    "CS9_DBCONFIG_SSLMODE": "no",
    "CS9_DBCONFIG_ROLE_CREATE_TABLE": "norsyss_user",
    "CS9_DBCONFIG_SERVER": "airflow-cs9-test.postgres.database.azure.com",
    "CS9_DBCONFIG_SCHEMA_CONFIG": "public",
    "CS9_DBCONFIG_DB_CONFIG": "norsyss_test",
    "CS9_DBCONFIG_SCHEMA_ANON": "public",
    "CS9_DBCONFIG_DB_ANON": "norsyss_test"
}

# Writable work volume for CS9 script execution
# KubernetesPodOperator does not inherit volumes from pod_template_file,
# so volumes must be explicitly defined here
WORK_VOLUME = k8s.V1Volume(
    name="work",
    empty_dir=k8s.V1EmptyDirVolumeSource()
)

WORK_VOLUME_MOUNT = k8s.V1VolumeMount(
    name="work",
    mount_path="/work"
)

# Security context to allow writing to emptyDir volumes
SECURITY_CONTEXT = k8s.V1PodSecurityContext(
    fs_group=1000  # Allow user 1000 to write to emptyDir volumes
)

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
        security_context=SECURITY_CONTEXT,
        volumes=[WORK_VOLUME],
        volume_mounts=[WORK_VOLUME_MOUNT],
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
        security_context=SECURITY_CONTEXT,
        volumes=[WORK_VOLUME],
        volume_mounts=[WORK_VOLUME_MOUNT],
    )

    # Task dependencies
    weather_download_and_import_rawdata >> weather_clean_data