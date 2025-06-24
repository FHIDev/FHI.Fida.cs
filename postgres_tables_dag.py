from datetime import datetime
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

with DAG(
    dag_id="postgres_tables_list",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["postgres", "database"],
) as dag:

    list_tables_task = KubernetesPodOperator(
        task_id="list_all_tables",
        image="postgres:15",
        cmds=["psql"],
        arguments=[
            "postgresql://altformyerettigheter:portalazurecomcreateMicrosoftPostgreSQLServer@airflow-cs9-test.postgres.database.azure.com:5432/postgres?sslmode=prefer",
            "-c",
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        ],
        name="postgres-tables-pod",
        namespace="ns-cs9-test",
        is_delete_operator_pod=True,
    )