"""
Team-specific Kubernetes Pod Operators for FHI Airflow Platform

This module provides team-specific operators that automatically configure
the appropriate service account for workload identity authentication.

Team operators are dynamically generated from the Helm values.yaml configuration,
ensuring synchronization between infrastructure and application code.

Usage:
    from platform_operators import AlviKubernetesPodOperator
    
    task = AlviKubernetesPodOperator(
        task_id="process_alvi_data",
        image="my-team-image:latest",
        # service_account_name automatically set to airflow-worker-team-alvi
    )
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Type
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
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


# Dynamic team operator generation
def _load_team_config():
    """Load teams from canonical Helm values.yaml"""
    # Allow overriding the path via environment variable for different execution contexts
    default_path = Path(__file__).parent / "infra/charts/airflow-teams/values.yaml"
    values_path = os.environ.get("FIDA_HELM_VALUES_PATH", default_path)
    values_file = Path(values_path)
    
    if not values_file.exists():
        raise FileNotFoundError(
            f"Helm values not found at {values_file}. "
            f"This is required for dynamic team operator generation. "
            f"Set FIDA_HELM_VALUES_PATH environment variable if running from different context."
        )
    
    with open(values_file, 'r') as f:
        values = yaml.safe_load(f)
    
    return values.get('teams', [])


def _create_team_operator_class(team_name: str) -> Type[BaseTeamKubernetesPodOperator]:
    """Dynamically create team-specific operator class"""
    # Convert team-name to PascalCase for class name
    class_name_parts = []
    for part in team_name.split('-'):
        class_name_parts.append(part.capitalize())
    class_name = ''.join(class_name_parts) + 'KubernetesPodOperator'
    
    # Create the class dynamically
    def __init__(self, **kwargs):
        BaseTeamKubernetesPodOperator.__init__(self, team_name=team_name, **kwargs)
    
    # Create the new class
    operator_class = type(
        class_name,
        (BaseTeamKubernetesPodOperator,),
        {
            '__init__': __init__,
            '__doc__': f'Kubernetes Pod Operator for {team_name} team.',
            '__module__': __name__,
        }
    )
    
    return operator_class


# Initialize team operators from configuration
try:
    teams = _load_team_config()
    TEAM_OPERATORS = {}
    
    for team in teams:
        team_name = team['name']
        operator_class = _create_team_operator_class(team_name)
        
        # Add to module namespace for direct imports
        globals()[operator_class.__name__] = operator_class
        TEAM_OPERATORS[team_name] = operator_class
    

except Exception as e:
    # Fallback for development/testing when values.yaml might not be available
    import warnings
    warnings.warn(
        f"Could not load dynamic team configuration: {e}. "
        f"Using empty TEAM_OPERATORS dict. This should only happen during development.",
        RuntimeWarning
    )
    TEAM_OPERATORS = {}


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
    from string import Template
    
    operator_class = get_team_operator(team_name)
    if operator_class is None:
        raise ValueError(f"No operator found for team '{team_name}'")
    
    # Load template from external file
    template_path = Path(__file__).parent / "dag_template.py.tpl"
    if not template_path.exists():
        raise FileNotFoundError(f"DAG template not found at {template_path}")
    
    with open(template_path, 'r') as f:
        template = Template(f.read())
    
    return template.substitute(
        operator_class_name=operator_class.__name__,
        team_name=team_name,
        team_name_safe=team_name.replace("-", "_"),
        dag_id=dag_id,
    )
