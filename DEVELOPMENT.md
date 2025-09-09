# Development Environment Setup

This document describes how to set up a development environment for the FHI.Fida.cs platform code.

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

## Package Management with uv (Recommended)

### Installing uv

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setting up the development environment

```bash
# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Install development dependencies
uv sync --extra dev
```

### Adding new dependencies

```bash
# Add a runtime dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Add with version constraints
uv add "package-name>=1.0.0"
```


## Key Dependencies

- **apache-airflow**: Core Airflow functionality
- **apache-airflow-providers-cncf-kubernetes**: Kubernetes operators
- **pyyaml**: YAML configuration parsing
- **kubernetes**: Kubernetes API client

## Running Tests

```bash
# With uv
uv run pytest

```

## Code Formatting

```bash
# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy platform_operators.py validate_dags.py
```

## Platform Code Overview

### Core Files

- **`platform_operators.py`**: Team-specific Kubernetes Pod Operators with dynamic generation
- **`validate_dags.py`**: DAG validation framework for CI/CD pipelines
- **`infra/charts/airflow-teams/values.yaml`**: Single source of truth for team configuration

### Dynamic Team Operators

The platform operators are generated dynamically from the Helm chart configuration:

1. **Single Source of Truth**: Teams are defined in `infra/charts/airflow-teams/values.yaml`
2. **Dynamic Generation**: Python classes are created at module import time
3. **Backward Compatibility**: All existing imports continue to work

### Testing the Platform Code

```bash
# Test dynamic operator generation
source .venv/bin/activate
python -c "
import platform_operators
print('Available teams:', list(platform_operators.TEAM_OPERATORS.keys()))
for team, op_class in platform_operators.TEAM_OPERATORS.items():
    print(f'{team}: {op_class.__name__}')
"

# Test operator instantiation
python -c "
import platform_operators
op = platform_operators.AlviKubernetesPodOperator(task_id='test', image='test:latest')
print('Service account:', op.service_account_name)
print('Labels:', op.labels)
"
```

### DAG Validation

```bash
# Run DAG validation (when DAG files exist)
python validate_dags.py dags/

# Strict mode (warnings as errors)
python validate_dags.py dags/ --strict
```

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError` for Airflow modules, ensure:

1. Virtual environment is activated
2. All dependencies are installed
3. Using correct import paths (e.g., `from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator`)

### Values.yaml Not Found

The platform operators require `infra/charts/airflow-teams/values.yaml` to exist. If running outside the main repository:

1. Ensure the file path is correct
2. Check that the YAML format matches the expected schema
3. Review the error message for specific path issues

### Python Version Compatibility

- Airflow 3.0+ requires Python 3.10 or higher
- All platform code is compatible with Python 3.10+
- Use `python --version` to check your Python version

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test: `uv run pytest`
3. Format code: `uv run black . && uv run isort .`
4. Type check: `uv run mypy platform_operators.py validate_dags.py`
5. Commit and push: `git commit -am "Description" && git push`
6. Create pull request

## Project Structure

```
FHI.Fida.cs/
├── platform_operators.py          # Team-specific operators (dynamic)
├── validate_dags.py               # DAG validation framework
├── pyproject.toml                 # Project configuration and dependencies
├── DEVELOPMENT.md                 # This file
├── infra/
│   └── charts/
│       └── airflow-teams/
│           ├── values.yaml        # Team configuration (source of truth)
│           ├── values.schema.json # Configuration validation schema
│           └── templates/         # Helm templates for K8s resources
└── .venv/                         # Virtual environment
```
