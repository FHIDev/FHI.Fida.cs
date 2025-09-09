"""
Team-specific Kubernetes Pod Operators for FHI Airflow Platform

This module provides team-specific operators that automatically configure
the appropriate service account for workload identity authentication.

Usage:
    from platform_operators import AlviKubernetesPodOperator
    
    task = AlviKubernetesPodOperator(
        task_id="process_alvi_data",
        image="my-team-image:latest",
        # service_account_name automatically set to airflow-worker-team-alvi
    )
"""

from typing import Optional, Dict, Any
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s


class BaseTeamKubernetesPodOperator(KubernetesPodOperator):
    """Base class for team-specific Kubernetes Pod Operators with workload identity."""
    
    def __init__(self, team_name: str, **kwargs):
        """Initialize with team-specific service account."""
        # Set service account for the team
        kwargs['service_account_name'] = f'airflow-worker-team-{team_name}'
        
        # Ensure workload identity labels are set
        if 'labels' not in kwargs:
            kwargs['labels'] = {}
        kwargs['labels']['azure.workload.identity/use'] = 'true'
        kwargs['labels']['team'] = team_name
        
        super().__init__(**kwargs)




# Team-specific operators
class AlviKubernetesPodOperator(BaseTeamKubernetesPodOperator):
    """Kubernetes Pod Operator for Alvi team."""
    def __init__(self, **kwargs):
        super().__init__(team_name='alvi', **kwargs)


class RisikoVvpKubernetesPodOperator(BaseTeamKubernetesPodOperator):
    """Kubernetes Pod Operator for RisikoVVP team."""
    def __init__(self, **kwargs):
        super().__init__(team_name='risiko-vvp', **kwargs)


class TotMortKubernetesPodOperator(BaseTeamKubernetesPodOperator):
    """Kubernetes Pod Operator for TotMort team."""
    def __init__(self, **kwargs):
        super().__init__(team_name='tot-mort', **kwargs)


class VakDekKubernetesPodOperator(BaseTeamKubernetesPodOperator):
    """Kubernetes Pod Operator for VakDek team."""
    def __init__(self, **kwargs):
        super().__init__(team_name='vak-dek', **kwargs)


class VakSikKubernetesPodOperator(BaseTeamKubernetesPodOperator):
    """Kubernetes Pod Operator for VakSik team."""
    def __init__(self, **kwargs):
        super().__init__(team_name='vak-sik', **kwargs)


class VaxEffMistKubernetesPodOperator(BaseTeamKubernetesPodOperator):
    """Kubernetes Pod Operator for VaxEff_MIST team."""
    def __init__(self, **kwargs):
        super().__init__(team_name='vax-eff-mist', **kwargs)


class VaxEffVvpKubernetesPodOperator(BaseTeamKubernetesPodOperator):
    """Kubernetes Pod Operator for VaxEff_VVP team."""
    def __init__(self, **kwargs):
        super().__init__(team_name='vax-eff-vvp', **kwargs)


# Team mapping for programmatic access
TEAM_OPERATORS = {
    'alvi': AlviKubernetesPodOperator,
    'risiko-vvp': RisikoVvpKubernetesPodOperator,
    'tot-mort': TotMortKubernetesPodOperator,
    'vak-dek': VakDekKubernetesPodOperator,
    'vak-sik': VakSikKubernetesPodOperator,
    'vax-eff-mist': VaxEffMistKubernetesPodOperator,
    'vax-eff-vvp': VaxEffVvpKubernetesPodOperator,
}


def get_team_operator(team_name: str):
    """Get the appropriate operator class for a team."""
    return TEAM_OPERATORS.get(team_name)


# Validation functions for platform team
def validate_service_account_usage(dag):
    """
    Validate that DAGs use appropriate service accounts for their tasks.
    This should be called in CI/CD pipeline during DAG validation.
    """
    
    warnings = []
    errors = []
    
    for task in dag.tasks:
        if isinstance(task, KubernetesPodOperator):
            task_id_lower = task.task_id.lower()
            
            if not task.service_account_name.startswith('airflow-worker-team-'):
                errors.append(
                    f"Task {task.task_id} does not use correct service account."
                )
            
            # Check for proper team operator usage
            if hasattr(task, 'labels') and 'team' in task.labels:
                team = task.labels['team']
                expected_sa = f'airflow-worker-team-{team}'
                
                if task.service_account_name != expected_sa:
                    warnings.append(
                        f"Task {task.task_id} has team label '{team}' but uses service account "
                        f"'{task.service_account_name}'. Expected '{expected_sa}'."
                    )
    
    return {
        'errors': errors,
        'warnings': warnings,
        'is_valid': len(errors) == 0
    }


# Example DAG template for teams
def create_team_dag_template(team_name: str, dag_id: str):
    """
    Create a template DAG for a specific team.
    This function can be used by the platform team to generate starter DAGs.
    """
    from airflow import DAG
    from datetime import datetime, timedelta
    
    operator_class = get_team_operator(team_name)
    
    dag_template = f'''
from airflow import DAG
from datetime import datetime, timedelta
from platform_operators import {operator_class.__name__}

default_args = {{
    'owner': '{team_name}-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}}

dag = DAG(
    '{dag_id}',
    default_args=default_args,
    description='Template DAG for {team_name} team',
    schedule_interval=None,
    catchup=False,
    tags=['{team_name}', 'team-template'],
)

# Example task using team-specific operator
example_task = {operator_class.__name__}(
    task_id='example_{team_name.replace("-", "_")}_task',
    image='your-team-image:latest',
    cmds=['python'],
    arguments=['-c', 'print("Hello from {team_name} team!")'],
    dag=dag,
)
'''
    
    return dag_template
