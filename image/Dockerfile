FROM python:3.10-slim

# Create non-root 'airflow' user with UID 50000 and GID 50000
ARG AIRFLOW_UID=50000
ARG AIRFLOW_GID=50000
RUN groupadd -r -g ${AIRFLOW_GID} airflow && \
    useradd -r -u ${AIRFLOW_UID} -g ${AIRFLOW_GID} -s /bin/bash -m airflow

# Install Airflow for Kubernetes execution
RUN pip install --upgrade pip && \
    pip install apache-airflow[kubernetes]==3.1.1 \
      --constraint https://raw.githubusercontent.com/apache/airflow/constraints-3.1.1/constraints-3.10.txt

# Set AIRFLOW_HOME for ephemeral worker pods
ENV AIRFLOW_HOME=/tmp/airflow

# Setup airflow directories
RUN mkdir -p /tmp/airflow && \
    chown -R airflow:airflow /tmp/airflow && \
    chmod -R 750 /tmp/airflow

# Switch to non-root airflow user
USER airflow
