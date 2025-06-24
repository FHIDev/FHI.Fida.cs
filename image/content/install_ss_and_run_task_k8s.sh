#!/bin/bash

# Check if exactly three arguments are provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <repo_url> <branch> <task>"
  echo "Example: $0 https://github.com/csids/cs9example.git main weather_download_and_import_rawdata"
  echo "Note: CS9 environment variables should be set by Kubernetes"
  exit 1
fi

REPO_URL=$1
BRANCH=$2
TASK=$3

# Extract repository name from URL (remove .git suffix and get basename)
REPOSITORY=$(basename "$REPO_URL" .git)

# Clone the repository and checkout the specified branch
git -C / clone -b "$BRANCH" "$REPO_URL"

# Check if the cloning was successful
if [ $? -ne 0 ]; then
  echo "Failed to clone repository from $REPO_URL (branch: $BRANCH)"
  exit 1
fi

# Build the R package
R CMD build "/${REPOSITORY}"

# Check if the build was successful
if [ $? -ne 0 ]; then
  echo "Failed to build the R package from /${REPOSITORY}"
  exit 1
fi

# Find the most recent tarball in the / directory
TARBALL=$(ls -t /${REPOSITORY}_*.tar.gz | head -n 1)

if [ -z "$TARBALL" ]; then
  echo "No tarball found for ${REPOSITORY} in /"
  exit 1
fi

# Install the R package
Rscript -e "install.packages('$TARBALL', repos = NULL, type = 'source')"

# Check if the installation was successful
if [ $? -ne 0 ]; then
  echo "Failed to install the R package from $TARBALL"
  exit 1
fi

# Set CS9 environment variables in R from Kubernetes environment
ENV_COMMAND=""
for var in CS9_DBCONFIG_USER CS9_DBCONFIG_PASSWORD CS9_AUTO CS9_PATH CS9_DBCONFIG_ACCESS CS9_DBCONFIG_DRIVER CS9_DBCONFIG_PORT CS9_DBCONFIG_SSLMODE CS9_DBCONFIG_ROLE_CREATE_TABLE CS9_DBCONFIG_SERVER CS9_DBCONFIG_SCHEMA_CONFIG CS9_DBCONFIG_DB_CONFIG CS9_DBCONFIG_SCHEMA_ANON CS9_DBCONFIG_DB_ANON; do
  if [ ! -z "${!var}" ]; then
    escaped_value="${!var//\"/\\\"}"
    ENV_COMMAND="${ENV_COMMAND}Sys.setenv(${var}=\"${escaped_value}\"); "
  fi
done

# Run the specified R command with environment variables
Rscript -e "${ENV_COMMAND}${REPOSITORY}::global\$ss\$run_task('${TASK}')"

# Check if the R command execution was successful
if [ $? -ne 0 ]; then
  echo "Failed to run the specified R command"
  exit 1
fi

echo "Script completed successfully"