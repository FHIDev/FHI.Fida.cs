FROM csids/cs9-su-csverse:4.4.1

# Create python symlink for compatibility (python3 is installed, but some scripts expect python)
RUN ln -s /usr/bin/python3 /usr/bin/python

# Create non-root 'airflow' user with UID 50000 and GID 50000
# Required for Kubernetes Pod Security Standards compliance and principle of least privilege
ARG AIRFLOW_UID=50000
ARG AIRFLOW_GID=50000
RUN groupadd -r -g ${AIRFLOW_GID} airflow && \
    useradd -r -u ${AIRFLOW_UID} -g ${AIRFLOW_GID} -s /bin/bash -m airflow

# environmental variables
COPY env_inside_image/env_inside_image.sh /tmp/
RUN chmod 0777 /tmp/env_inside_image.sh
RUN bash /tmp/env_inside_image.sh

# Copy config and startup
COPY content/install_ss_and_run_task.sh /usr/local/bin/install_ss_and_run_task.sh
COPY content/install_ss_and_run_task_k8s.sh /usr/local/bin/install_ss_and_run_task_k8s.sh
RUN chmod +x /usr/local/bin/install_ss_and_run_task.sh
RUN chmod +x /usr/local/bin/install_ss_and_run_task_k8s.sh

### install extra packages
RUN R -e 'devtools::install_github("norsyss/norsyss", upgrade="never")'

### install surveillance systems
RUN R -e 'devtools::install_github("csids/cs9example", upgrade="never")'

### install Airflow for Kubernetes execution (for Airflow 3.0+ compatibility)
### Use official Airflow 3.1.0 constraints for known-good dependency versions
RUN pip install --upgrade pip && \
    pip install apache-airflow[kubernetes]==3.1.0 \
      --constraint https://raw.githubusercontent.com/apache/airflow/constraints-3.1.0/constraints-3.10.txt && \
    find /usr/local/lib/python3.10/dist-packages -type d -exec chmod 755 {} \; && \
    find /usr/local/lib/python3.10/dist-packages -type f -exec chmod 644 {} \;

### Set AIRFLOW_HOME to /tmp/airflow for ephemeral worker pods
### This allows any UID to import airflow without permission issues
ENV AIRFLOW_HOME=/tmp/airflow

# Ensure airflow user owns necessary directories and can write to them
RUN mkdir -p /tmp/airflow && \
    chown -R airflow:airflow /tmp/airflow && \
    chmod -R 750 /tmp/airflow && \
    chown -R airflow:airflow /opt/airflow 2>/dev/null || true && \
    chmod -R 750 /opt/airflow 2>/dev/null || true

# Switch to non-root airflow user for all subsequent operations
USER airflow
