#!/usr/bin/env python3
"""
DAG Validation Framework for Multi-Team Airflow Platform

This script validates DAGs for proper service account usage and team compliance.
Designed to be run in CI/CD pipeline to enforce platform security policies.

Usage:
    python validate_dags.py [dag_directory] [--strict]

Exit codes:
    0: All DAGs valid
    1: Validation errors found
    2: Script error
"""

import sys
import os
import importlib.util
import argparse
from pathlib import Path
from typing import List, Dict, Any
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from platform_operators import validate_service_account_usage, TEAM_OPERATORS


class DAGValidator:
    """Validates DAGs for platform compliance."""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.errors = []
        self.warnings = []
        
    def validate_dag_file(self, dag_file_path: Path) -> Dict[str, Any]:
        """Validate a single DAG file."""
        try:
            # Load the DAG file as a module
            spec = importlib.util.spec_from_file_location(
                f"dag_{dag_file_path.stem}", 
                dag_file_path
            )
            if spec is None or spec.loader is None:
                return {
                    'file': str(dag_file_path),
                    'errors': [f"Could not load DAG file: {dag_file_path}"],
                    'warnings': [],
                    'dags_found': 0
                }
                
            dag_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dag_module)
            
            # Find all DAG objects in the module
            dags = []
            for attr_name in dir(dag_module):
                attr = getattr(dag_module, attr_name)
                if isinstance(attr, DAG):
                    dags.append(attr)
            
            if not dags:
                return {
                    'file': str(dag_file_path),
                    'errors': [],
                    'warnings': ['No DAG objects found in file'],
                    'dags_found': 0
                }
            
            # Validate each DAG
            file_errors = []
            file_warnings = []
            
            for dag in dags:
                validation_result = validate_service_account_usage(dag)
                file_errors.extend([f"DAG '{dag.dag_id}': {error}" for error in validation_result['errors']])
                file_warnings.extend([f"DAG '{dag.dag_id}': {warning}" for warning in validation_result['warnings']])
                
                # Additional platform-specific validations
                additional_validation = self._validate_dag_metadata(dag)
                file_errors.extend(additional_validation['errors'])
                file_warnings.extend(additional_validation['warnings'])
            
            return {
                'file': str(dag_file_path),
                'errors': file_errors,
                'warnings': file_warnings,
                'dags_found': len(dags)
            }
            
        except Exception as e:
            return {
                'file': str(dag_file_path),
                'errors': [f"Failed to validate DAG file: {str(e)}"],
                'warnings': [],
                'dags_found': 0
            }
    
    def _validate_dag_metadata(self, dag: DAG) -> Dict[str, List[str]]:
        """Validate DAG metadata and structure."""
        errors = []
        warnings = []
        
        # Check for required tags
        if not dag.tags:
            warnings.append(f"DAG '{dag.dag_id}' has no tags. Consider adding team identification tags.")
        
        # Check for team-specific DAG naming conventions
        team_prefixes = list(TEAM_OPERATORS.keys())
        has_team_prefix = any(dag.dag_id.startswith(f"{team}_") for team in team_prefixes)
        
        if not has_team_prefix and dag.tags:
            # Check if DAG has team tag but doesn't follow naming convention
            team_tags = [tag for tag in dag.tags if tag in team_prefixes]
            if team_tags:
                warnings.append(
                    f"DAG '{dag.dag_id}' has team tag '{team_tags[0]}' but doesn't follow "
                    f"naming convention '{team_tags[0]}_*'"
                )
        
        # Check for owner field
        if not dag.default_args.get('owner'):
            warnings.append(f"DAG '{dag.dag_id}' has no owner specified in default_args.")
        
        # Validate KubernetesPodOperator tasks
        for task in dag.tasks:
            if isinstance(task, KubernetesPodOperator):
                task_validation = self._validate_kubernetes_task(task, dag.dag_id)
                errors.extend(task_validation['errors'])
                warnings.extend(task_validation['warnings'])
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_kubernetes_task(self, task: KubernetesPodOperator, dag_id: str) -> Dict[str, List[str]]:
        """Validate individual Kubernetes tasks."""
        errors = []
        warnings = []
        
        # Check for required workload identity labels
        if not hasattr(task, 'labels') or not task.labels:
            warnings.append(
                f"Task '{task.task_id}' in DAG '{dag_id}' has no labels. "
                f"Workload identity requires 'azure.workload.identity/use: true'"
            )
        elif task.labels.get('azure.workload.identity/use') != 'true':
            errors.append(
                f"Task '{task.task_id}' in DAG '{dag_id}' missing required label "
                f"'azure.workload.identity/use: true'"
            )
        
        # Check for service account configuration
        if not task.service_account_name:
            errors.append(
                f"Task '{task.task_id}' in DAG '{dag_id}' has no service account specified. "
                f"This is required for workload identity."
            )
        elif not task.service_account_name.startswith('airflow-worker-team-'):
            errors.append(
                f"Task '{task.task_id}' in DAG '{dag_id}' uses service account "
                f"'{task.service_account_name}' which is not a team-specific service account. "
                f"Only team-specific service accounts (airflow-worker-team-*) are allowed."
            )
        
        # Check for image security
        if task.image and ':latest' in task.image:
            warnings.append(
                f"Task '{task.task_id}' in DAG '{dag_id}' uses image with ':latest' tag. "
                f"Consider pinning to specific version for reproducibility."
            )
        
        return {'errors': errors, 'warnings': warnings}
    
    def validate_directory(self, dag_directory: Path) -> Dict[str, Any]:
        """Validate all Python files in a directory."""
        python_files = list(dag_directory.glob('**/*.py'))
        
        if not python_files:
            return {
                'total_files': 0,
                'total_dags': 0,
                'files_with_errors': 0,
                'files_with_warnings': 0,
                'results': [],
                'summary': {'errors': ['No Python files found in directory'], 'warnings': []}
            }
        
        results = []
        total_errors = 0
        total_warnings = 0
        total_dags = 0
        files_with_errors = 0
        files_with_warnings = 0
        
        for python_file in python_files:
            # Skip __pycache__ and other non-DAG files
            if '__pycache__' in str(python_file) or python_file.name.startswith('test_'):
                continue
                
            result = self.validate_dag_file(python_file)
            results.append(result)
            
            total_dags += result['dags_found']
            
            if result['errors']:
                total_errors += len(result['errors'])
                files_with_errors += 1
                
            if result['warnings']:
                total_warnings += len(result['warnings'])
                files_with_warnings += 1
        
        return {
            'total_files': len([r for r in results if r['dags_found'] > 0]),
            'total_dags': total_dags,
            'files_with_errors': files_with_errors,
            'files_with_warnings': files_with_warnings,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'results': results,
        }


def print_validation_results(validation_results: Dict[str, Any], strict_mode: bool = False):
    """Print formatted validation results."""
    print("=" * 80)
    print("DAG VALIDATION REPORT")
    print("=" * 80)
    print(f"Files processed: {validation_results['total_files']}")
    print(f"DAGs found: {validation_results['total_dags']}")
    print(f"Files with errors: {validation_results['files_with_errors']}")
    print(f"Files with warnings: {validation_results['files_with_warnings']}")
    print(f"Total errors: {validation_results['total_errors']}")
    print(f"Total warnings: {validation_results['total_warnings']}")
    print()
    
    # Print detailed results
    for result in validation_results['results']:
        if result['errors'] or result['warnings'] or result['dags_found'] == 0:
            print(f"File: {result['file']}")
            print(f"  DAGs found: {result['dags_found']}")
            
            if result['errors']:
                print("  ERRORS:")
                for error in result['errors']:
                    print(f"    ❌ {error}")
            
            if result['warnings']:
                print("  WARNINGS:")
                for warning in result['warnings']:
                    print(f"    ⚠️  {warning}")
            print()
    
    # Summary
    if validation_results['total_errors'] > 0:
        print("❌ VALIDATION FAILED - Errors must be fixed before deployment")
        return False
    elif validation_results['total_warnings'] > 0 and strict_mode:
        print("❌ VALIDATION FAILED - Warnings treated as errors in strict mode")
        return False
    elif validation_results['total_warnings'] > 0:
        print("⚠️  VALIDATION PASSED - But warnings should be addressed")
        return True
    else:
        print("✅ VALIDATION PASSED - All DAGs are compliant")
        return True


def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description='Validate Airflow DAGs for platform compliance')
    parser.add_argument('dag_directory', nargs='?', default='dags', 
                       help='Directory containing DAG files (default: dags)')
    parser.add_argument('--strict', action='store_true',
                       help='Treat warnings as errors')
    
    args = parser.parse_args()
    
    dag_directory = Path(args.dag_directory)
    
    if not dag_directory.exists():
        print(f"Error: Directory '{dag_directory}' does not exist")
        sys.exit(2)
    
    if not dag_directory.is_dir():
        print(f"Error: '{dag_directory}' is not a directory")
        sys.exit(2)
    
    # Add current directory to Python path to allow DAG imports
    sys.path.insert(0, str(Path.cwd()))
    
    validator = DAGValidator(strict_mode=args.strict)
    results = validator.validate_directory(dag_directory)
    
    success = print_validation_results(results, args.strict)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
