from datetime import datetime
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

with DAG(
    dag_id="hello_world_docker",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["example"],
) as dag:

    hello_task = DockerOperator(
        task_id="echo_hello",
        image="alpine:latest",  # Small and quick for echo
        command='echo "hello world"',
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        auto_remove=True,
    )
    
