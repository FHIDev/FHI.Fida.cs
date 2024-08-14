#!/usr/bin/bash

echo "CS9_AUTO=0" >> $R_HOME/etc/Renviron
echo "CS9_PATH='/cs9path'" >> $R_HOME/etc/Renviron

echo "CS9_DBCONFIG_ACCESS='config/anon'" >> $R_HOME/etc/Renviron
echo "CS9_DBCONFIG_DRIVER='PostgreSQL Unicode'" >> $R_HOME/etc/Renviron
echo "CS9_DBCONFIG_PORT='5432'" >> $R_HOME/etc/Renviron
# echo "CS9_DBCONFIG_USER='XXXX'" >> $R_HOME/etc/Renviron
# echo "CS9_DBCONFIG_PASSWORD='XXXX'" >> $R_HOME/etc/Renviron

echo "CS9_DBCONFIG_TRUSTED_CONNECTION='no'" >> $R_HOME/etc/Renviron
echo "CS9_DBCONFIG_SSLMODE='require'" >> $R_HOME/etc/Renviron
# echo "CS9_DBCONFIG_SERVER='XXXX'" >> $R_HOME/etc/Renviron

# echo "CS9_DBCONFIG_SCHEMA_CONFIG='XXXX'" >> $R_HOME/etc/Renviron
# echo "CS9_DBCONFIG_DB_CONFIG='XXXX'" >> $R_HOME/etc/Renviron

# echo "CS9_DBCONFIG_SCHEMA_ANON='XXXX'" >> $R_HOME/etc/Renviron
# echo "CS9_DBCONFIG_DB_ANON='XXXX'" >> $R_HOME/etc/Renviron
