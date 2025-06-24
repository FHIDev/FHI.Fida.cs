from datetime import datetime
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator

def list_tables():
    """List all table names in the PostgreSQL database"""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Query to get all table names from information_schema
    sql = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
    """
    
    records = hook.get_records(sql)
    
    print("Tables in the database:")
    for record in records:
        print(f"- {record[0]}")
    
    return [record[0] for record in records]

with DAG(
    dag_id="postgres_tables_list",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["postgres", "database"],
) as dag:

    list_tables_task = PythonOperator(
        task_id="list_all_tables",
        python_callable=list_tables,
    )