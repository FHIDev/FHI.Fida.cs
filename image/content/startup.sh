#!/bin/bash

set -e
set -x

# # Deactivate license when it exists
# deactivate() {
#     echo "== Exiting =="
#     echo " --> TAIL 100 rstudio-server.log"
#     tail -100 /var/log/rstudio-server.log
#     echo " --> TAIL 100 rstudio-launcher.log"
#     tail -100 /var/lib/rstudio-launcher/rstudio-launcher.log
#     echo " --> TAIL 100 monitor/log/rstudio-server.log"
#     tail -100 /var/lib/rstudio-server/monitor/log/rstudio-server.log

#     echo "Deactivating license ..."
#     rstudio-server license-manager deactivate >/dev/null 2>&1

#     echo "== Done =="
# }
# trap deactivate EXIT

# touch log files to initialize them
su rstudio-server -c 'touch /var/lib/rstudio-server/monitor/log/rstudio-server.log'
mkdir -p /var/lib/rstudio-launcher
chown rstudio-server:rstudio-server /var/lib/rstudio-launcher
su rstudio-server -c 'touch /var/lib/rstudio-launcher/rstudio-launcher.log'
touch /var/log/rstudio-server.log

# # Activate License
# if ! [ -z "$RSP_LICENSE" ]; then
#     rstudio-server license-manager deactivate $RSP_LICENSE
#     rstudio-server license-manager activate $RSP_LICENSE
# elif ! [ -z "$RSP_LICENSE_SERVER" ]; then
#     rstudio-server license-manager license-server $RSP_LICENSE_SERVER
# elif test -f "/etc/rstudio-server/license.lic"; then
#     rstudio-server license-manager activate-file /etc/rstudio-server/license.lic
# fi

# lest this be inherited by child processes
unset RSP_LICENSE
unset RSP_LICENSE_SERVER

# Stuff that is shared from the live mount
cp /shared/list_of_users.sh /usr/local/bin/list_of_users.sh
chmod +x /usr/local/bin/list_of_users.sh
/usr/local/bin/list_of_users.sh

cp /shared/openid-client-secret /etc/rstudio/openid-client-secret
chmod 0600 /etc/rstudio/openid-client-secret

cp /shared/licence_file /var/lib/rstudio-server/licence_file
chmod 444 /var/lib/rstudio-server-licence_file
rstudio-server license-manager deactivate
rstudio-server license-manager activate-file /var/lib/rstudio-server/licence_file

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

