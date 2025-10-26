"""
Team-specific configuration for Airflow DAG execution.

This module defines Kubernetes execution parameters (service account, namespace)
for each team that runs DAGs. Configuration is kept here so DAGs can explicitly
specify their team identity and execution context.

PREREQUISITE: Each team's service account must be created in Kubernetes:
  - airflow-worker-team-{team_name} in the airflow namespace
  - With Azure Workload Identity annotations

And a Role/RoleBinding must exist in the target namespace granting the team
service account permissions to create and manage pods.
"""

TEAM_CONFIG = {
    "norsyss": {
        "service_account_name": "airflow-worker-team-norsyss",
        "namespace": "tn-fida-airflow",
        "description": "NorSySS team - running on cs9 infrastructure",
    },
    # Template for additional teams:
    # "team_name": {
    #     "service_account_name": "airflow-worker-team-team_name",
    #     "namespace": "ns-team-name",
    #     "description": "Team description",
    # },
}


def get_team_config(team_name: str) -> dict:
    """
    Get the Kubernetes execution configuration for a team.

    Args:
        team_name: The name of the team (must exist in TEAM_CONFIG)

    Returns:
        Dictionary with 'service_account_name' and 'namespace' keys

    Raises:
        KeyError: If team_name is not found in TEAM_CONFIG
    """
    if team_name not in TEAM_CONFIG:
        raise KeyError(
            f"Team '{team_name}' not found in TEAM_CONFIG. "
            f"Available teams: {', '.join(TEAM_CONFIG.keys())}"
        )
    return TEAM_CONFIG[team_name]
