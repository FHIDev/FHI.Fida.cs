from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def say_hello():
    print("hello world 2")

with DAG(
    dag_id='hello_world_2_dag',
    start_date=datetime(2023, 1, 1),
    schedule_interval="*/5 * * * *",  # Every 10 minutes
    catchup=False,
    tags=['example'],
) as dag:
    
    hello_task = PythonOperator(
        task_id='print_hello',
        python_callable=say_hello
    )
