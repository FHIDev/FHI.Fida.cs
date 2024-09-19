#!/bin/bash

set -e
set -x

# Live mount - Create list of users
cp /shared/list_of_users.sh /usr/local/bin/list_of_users.sh
chmod +x /usr/local/bin/list_of_users.sh
/usr/local/bin/list_of_users.sh

# Live mount - openid
cp /shared/openid-client-secret /etc/rstudio/openid-client-secret
chmod 0600 /etc/rstudio/openid-client-secret

# Live mount - Activate workbench licence file
cp /shared/licence_file /var/lib/rstudio-server/licence_file
chmod 444 /var/lib/rstudio-server-licence_file
rstudio-server license-manager deactivate
rstudio-server license-manager activate-file /var/lib/rstudio-server/licence_file

# touch log files to initialize them
su rstudio-server -c 'touch /var/lib/rstudio-server/monitor/log/rstudio-server.log'
mkdir -p /var/lib/rstudio-launcher
chown rstudio-server:rstudio-server /var/lib/rstudio-launcher
su rstudio-server -c 'touch /var/lib/rstudio-launcher/rstudio-launcher.log'
touch /var/log/rstudio-server.log

# lest this be inherited by child processes
unset RSP_LICENSE
unset RSP_LICENSE_SERVER

# start folder moutns
# automount

# Start Rsyslog
# service rsyslog start

# Start SSSD
# service sssd start

# Start Launcher
if [ "$RSP_LAUNCHER" == "true" ]; then
  /usr/lib/rstudio-server/bin/rstudio-launcher > /var/log/rstudio-launcher.log 2>&1 &
  wait-for-it.sh localhost:5559 -t $RSP_LAUNCHER_TIMEOUT
fi

tail -n 100 -f /var/lib/rstudio-server/monitor/log/*.log /var/lib/rstudio-launcher/*.log /var/log/rstudio-server.log &

# the main container process
# cannot use "exec" or the "trap" will be lost
/usr/lib/rstudio-server/bin/rserver --server-daemonize 0 > /var/log/rstudio-server.log 2>&1

