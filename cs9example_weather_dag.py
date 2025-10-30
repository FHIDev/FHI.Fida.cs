from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

# Service account for this DAG
SERVICE_ACCOUNT_NAME = "airflow-worker-team-norsyss"

# Environment variables for cs9 tasks
# All variables are set here; tasks will access them via shell environment and pass to R via Sys.setenv()
CS9_ENV_VARS = {
    "CS9_DBCONFIG_USER": "norsyss_user",
    "CS9_DBCONFIG_PASSWORD": "NorsyssTestPass!23#Secure",
    "CS9_AUTO": "0",
    "CS9_PATH": "/tmp/work",
    "CS9_DBCONFIG_ACCESS": "config/anon",
    "CS9_DBCONFIG_DRIVER": "PostgreSQL Unicode",
    "CS9_DBCONFIG_PORT": "5432",
    "CS9_DBCONFIG_SSLMODE": "disable",
    "CS9_DBCONFIG_ROLE_CREATE_TABLE": "norsyss_user",
    "CS9_DBCONFIG_SERVER": "airflow-cs9-test.postgres.database.azure.com",
    "CS9_DBCONFIG_SCHEMA_CONFIG": "public",
    "CS9_DBCONFIG_DB_CONFIG": "norsyss_test",
    "CS9_DBCONFIG_SCHEMA_ANON": "public",
    "CS9_DBCONFIG_DB_ANON": "norsyss_test"
}

# Try to import kubernetes client. This is needed in the scheduler to construct executor configs,
# but worker pods (which execute tasks) don't have the kubernetes library installed.
# The try/except allows the DAG to be imported in both contexts.
try:
    from kubernetes.client import models as k8s

    # Resource requirements for all cs9 tasks (must not exceed Kyverno policy: CPU <= 2, Memory <= 2Gi)
    CS9_CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
        requests={"cpu": "500m", "memory": "1Gi"},
        limits={"cpu": "1000m", "memory": "1Gi"}
    )

    def get_executor_config():
        """Pod override config for Kubernetes Executor tasks."""
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
                            resources=CS9_CONTAINER_RESOURCES,
                            env=[
                                k8s.V1EnvVar(name=key, value=str(value))
                                for key, value in CS9_ENV_VARS.items()
                            ],
                        )
                    ],
                    service_account_name=SERVICE_ACCOUNT_NAME,
                    restart_policy="Never",
                )
            )
        }

except ModuleNotFoundError:
    # Kubernetes client not available (e.g., in worker pods).
    # Provide dummy implementations to allow DAG import to succeed.
    CS9_CONTAINER_RESOURCES = None

    def get_executor_config():
        """Dummy implementation when kubernetes client is not available."""
        return {}

with DAG(
    dag_id="cs9example_weather_download",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Changed from "0 * * * *" to None for manual triggers only
    catchup=False,
    tags=["cs9", "weather", "example"],
) as dag:

    debug_postgres_connection = BashOperator(
        task_id="debug_postgres_connection",
        bash_command="""
            set -e
            echo "=== Testing PostgreSQL connectivity from bash ==="
            echo "Host: ${CS9_DBCONFIG_SERVER}"
            echo "User: ${CS9_DBCONFIG_USER}"
            echo "Database: ${CS9_DBCONFIG_DB_CONFIG}"

            PGPASSWORD="${CS9_DBCONFIG_PASSWORD}" psql \
              -h "${CS9_DBCONFIG_SERVER}" \
              -U "${CS9_DBCONFIG_USER}" \
              -d "${CS9_DBCONFIG_DB_CONFIG}" \
              -c "SELECT 1 as connection_test;" || echo "Bash psql test failed"

            echo ""
            echo "=== Testing PostgreSQL connectivity from R ==="
            R -q -e "
            cat('Testing R database connection\n')
            cat('Host: ', Sys.getenv('CS9_DBCONFIG_SERVER'), '\n')
            cat('User: ', Sys.getenv('CS9_DBCONFIG_USER'), '\n')
            cat('Database: ', Sys.getenv('CS9_DBCONFIG_DB_CONFIG'), '\n')

            tryCatch({
              library(DBI)
              conn <- dbConnect(
                RPostgres::Postgres(),
                host = Sys.getenv('CS9_DBCONFIG_SERVER'),
                user = Sys.getenv('CS9_DBCONFIG_USER'),
                password = Sys.getenv('CS9_DBCONFIG_PASSWORD'),
                dbname = Sys.getenv('CS9_DBCONFIG_DB_CONFIG'),
                port = as.numeric(Sys.getenv('CS9_DBCONFIG_PORT')),
                sslmode = Sys.getenv('CS9_DBCONFIG_SSLMODE')
              )
              result <- dbGetQuery(conn, 'SELECT 1 as connection_test')
              cat('R database connection successful:\n')
              print(result)
              dbDisconnect(conn)
            }, error = function(e) {
              cat('R database connection failed:\n')
              cat(e[['message']], '\n')
            })
            "
        """,
        executor_config=get_executor_config(),
    )

    weather_download_and_import_rawdata = BashOperator(
        task_id="weather_download_and_import_rawdata",
        bash_command="/usr/local/bin/install_ss_and_run_task_k8s.sh https://github.com/csids/cs9example.git main weather_download_and_import_rawdata",
        executor_config=get_executor_config(),
    )

    weather_clean_data = BashOperator(
        task_id="weather_clean_data",
        bash_command="/usr/local/bin/install_ss_and_run_task_k8s.sh https://github.com/csids/cs9example.git main weather_clean_data",
        executor_config=get_executor_config(),
    )

    # Task dependencies
    debug_postgres_connection >> weather_download_and_import_rawdata >> weather_clean_data
