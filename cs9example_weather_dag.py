from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from teams.config import get_team_config

# Lazy import kubernetes only when needed (avoids import error in task pods)
def _get_kubernetes_models():
    from kubernetes.client import models as k8s
    return k8s

# Team configuration: This DAG belongs to the norsyss team
TEAM_NAME = "norsyss"
TEAM_CONFIG = get_team_config(TEAM_NAME)

# Default resource limits for all cs9 tasks (must not exceed Kyverno policy: CPU <= 2, Memory <= 2Gi)
def _get_default_container_resources():
    try:
        k8s = _get_kubernetes_models()
        return k8s.V1ResourceRequirements(
            requests={"cpu": "500m", "memory": "1Gi"},
            limits={"cpu": "1000m", "memory": "1Gi"}
        )
    except ModuleNotFoundError:
        # Worker pods don't have kubernetes; return None
        return None

# Reusable environment variables for all cs9 tasks
# Database credentials point to norsyss_test database on airflow-cs9-test.postgres.database.azure.com
# Note: CS9_PATH will be set dynamically per task to use ephemeral /tmp/work_{run_id}
def _get_cs9_env_vars(work_dir="/tmp/work"):
    return {
        "CS9_DBCONFIG_USER": "norsyss_user",
        "CS9_DBCONFIG_PASSWORD": "NorsyssTestPass!23#Secure",
        "CS9_AUTO": "0",
        "CS9_PATH": work_dir,
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

# Pod executor config for Kubernetes Executor
# Uses ephemeral /tmp storage with run_id isolation for each DAG run
def get_executor_config(work_dir="/tmp/work"):
    """
    Get pod override config for tasks running on Kubernetes Executor.
    This function is only called by the scheduler, not by worker pods during DAG parsing.
    Worker pods that import this DAG for ExecuteTask won't call this function.

    Ephemeral storage pattern:
    - Each task pod gets its own /tmp ephemeral storage
    - Tasks in same DAG run use run_id in path for isolation
    - Concurrent DAG runs don't interfere (different run_ids)
    - Storage is automatically cleaned when pod terminates
    """
    try:
        k8s = _get_kubernetes_models()
    except ModuleNotFoundError:
        # Worker pods don't have kubernetes module; return empty config
        # Scheduler will have already sent executor config via ExecuteTask API
        return {}

    return {
        "pod_override": k8s.V1Pod(
            spec=k8s.V1PodSpec(
                security_context=k8s.V1PodSecurityContext(
                    run_as_user=50000,
                    fs_group=50000
                ),
                containers=[
                    k8s.V1Container(
                        name="base",
                        image="ghcr.io/fhidev/fhi.fida.cs/cs9base-k8s:latest",
                        image_pull_policy="Always",
                        resources=_get_default_container_resources(),
                        env=[
                            k8s.V1EnvVar(name=key, value=str(value))
                            for key, value in _get_cs9_env_vars(work_dir).items()
                        ],
                    )
                ],
                service_account_name=TEAM_CONFIG["service_account_name"],
                restart_policy="Never",
            )
        )
    }

with DAG(
    dag_id="cs9example_weather_download",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Changed from "0 * * * *" to None for manual triggers only
    catchup=False,
    tags=["cs9", "weather", "example"],
) as dag:

    weather_download_and_import_rawdata = BashOperator(
        task_id="weather_download_and_import_rawdata",
        bash_command="""
            set -e
            echo "=== Environment Variables ==="
            env | grep -i CS9 | sort
            echo "=== Testing database connectivity ==="
            which psql || echo "psql not found"
            echo "Done - debug complete"
        """,
        executor_config=get_executor_config(),
    )

    weather_clean_data = BashOperator(
        task_id="weather_clean_data",
        bash_command="""
            set -e
            # Each task gets its own pod, so we clone cs9example again in this pod
            WORK_DIR="/tmp/work_{{ run_id }}"
            mkdir -p "${WORK_DIR}"
            cd "${WORK_DIR}"
            # Clone repository fresh in this task pod
            # (Each KubernetesExecutor task pod is ephemeral and isolated)
            if [ ! -d cs9example ]; then
                git clone --depth 1 --branch main https://github.com/csids/cs9example.git
            fi
            cd cs9example
            /usr/local/bin/install_ss_and_run_task_k8s.sh https://github.com/csids/cs9example.git main weather_clean_data
        """,
        executor_config=get_executor_config(),
    )

    # Task dependency: weather_clean_data runs after weather_download_and_import_rawdata completes
    weather_download_and_import_rawdata >> weather_clean_data
