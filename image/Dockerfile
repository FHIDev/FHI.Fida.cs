FROM csids/cs9-su-csverse:4.4.1

# environmental variables
COPY env_inside_image/env_inside_image.sh /tmp/
RUN chmod 0777 /tmp/env_inside_image.sh
RUN bash /tmp/env_inside_image.sh

# Copy config and startup
COPY content/install_ss_and_run_task.sh /usr/local/bin/install_ss_and_run_task.sh
RUN chmod +x /usr/local/bin/install_ss_and_run_task.sh

### install extra packages
RUN R -e 'devtools::install_github("norsyss/norsyss", upgrade="never")'

### install surveillance systems
RUN R -e 'devtools::install_github("csids/cs9example", upgrade="never")'
