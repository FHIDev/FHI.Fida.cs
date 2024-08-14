FROM ghcr.io/fhidev/fhi.fida.cs/cs9base:4.4.1

# Set default env values
ENV DEBIAN_FRONTEND=noninteractive
ENV RSP_LICENSE ""
ENV RSP_LICENSE_SERVER ""
ENV RSP_TESTUSER rstudio
ENV RSP_TESTUSER_PASSWD helloworld
ENV RSP_TESTUSER_UID 10000
ENV RSP_LAUNCHER true
ENV RSP_LAUNCHER_TIMEOUT 10

# Template surveillance system
RUN git clone "https://github.com/csids/cs9example.git" "/cs9example"

# Copy config and startup
COPY content/create_user.sh /usr/local/bin/create_user.sh
RUN chmod +x /usr/local/bin/create_user.sh

COPY content/startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# Install Posit Workbench --------------------------------------------------#
RUN apt-get update -y
RUN /usr/local/bin/install_posit.sh https://download2.rstudio.org/server/jammy/amd64/rstudio-workbench-2024.04.2-amd64.deb

# permissions
RUN chmod 0600 /etc/rstudio/launcher.pem

# Create log dir
RUN mkdir -p /var/lib/rstudio-server/monitor/log && \
    chown -R rstudio-server:rstudio-server /var/lib/rstudio-server/monitor

# server config
COPY conf/logging.conf /etc/rstudio/logging.conf
COPY conf/rserver.conf /etc/rstudio/rserver.conf
COPY conf/rsession.conf /etc/rstudio/rsession.conf
# COPY conf/openid-client-secret /etc/rstudio/openid-client-secret
# RUN chmod 0600 /etc/rstudio/openid-client-secret

#--------- Licence --------------------------

# blocked out licence deactivation/activation stuff in the startup.sh script
# below is a copy of beta lic file that was sent via support

# COPY content/licence_file /var/lib/rstudio-server/licence_file
# RUN chmod 444 /var/lib/rstudio-server/licence_file
# RUN rstudio-server license-manager deactivate
# RUN rstudio-server license-manager activate-file /var/lib/rstudio-server/licence_file

EXPOSE 8787

ENTRYPOINT ["tini", "--"]
CMD ["/usr/local/bin/startup.sh"]
