from datetime import datetime
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

with DAG(
    dag_id="hello_world_docker",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["example"],
) as dag:

    hello_task = KubernetesPodOperator(
        task_id="echo_hello",
        image="alpine:latest",
        cmds=["echo"],
        arguments=["hello world"],
        name="hello-world-pod",
        namespace="default",
        is_delete_operator_pod=True,
    )
    
