#!/bin/bash

# Check if at least four arguments are provided
if [ "$#" -lt 4 ]; then
  echo "Usage: $0 <repo_url> <repository> <branch> <task> [ENV_VAR1=value1] [ENV_VAR2=value2] ..."
  echo "Example: $0 https://github.com/csids/cs9example.git cs9example main weather_download_and_import_rawdata"
  exit 1
fi

REPO_URL=$1
REPOSITORY=$2
BRANCH=$3
TASK=$4

# Environment variables start at position 5
ENV_START=5

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

# Set environment variables
ENV_COMMAND=""
for var in "${@:$ENV_START}"; do
  ENV_COMMAND="${ENV_COMMAND}Sys.setenv(${var%%=*}='${var#*=}'); "
done

# Run the specified R command with environment variables
Rscript -e "${ENV_COMMAND}${REPOSITORY}::global\$ss\$run_task('${TASK}')"

# Check if the R command execution was successful
if [ $? -ne 0 ]; then
  echo "Failed to run the specified R command"
  exit 1
fi

echo "Script completed successfully"