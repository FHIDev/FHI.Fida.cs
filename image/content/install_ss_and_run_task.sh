#!/bin/bash

#!/bin/bash

# Check if exactly two arguments are provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <username> <repository> <task>"
  exit 1
fi

USERNAME=$1
REPOSITORY=$2
TASK=$3
REPO_URL="http://p2932-podman.tsd.usit.no:3000/${USERNAME}/${REPOSITORY}.git"

# Clone the repository
git -C / clone "$REPO_URL"

# Check if the cloning was successful
if [ $? -ne 0 ]; then
  echo "Failed to clone repository from $REPO_URL"
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
  echo "No tarball found for ${REPOSITORY} in /tmp"
  exit 1
fi

# Install the R package
Rscript -e "install.packages('$TARBALL', repos = NULL, type = 'source')"

# Check if the installation was successful
if [ $? -ne 0 ]; then
  echo "Failed to install the R package from $TARBALL"
  exit 1
fi

# Run the specified R command
Rscript -e "${REPOSITORY}::global\$ss\$run_task('${TASK}')"

# Check if the R command execution was successful
if [ $? -ne 0 ]; then
  echo "Failed to run the specified R command"
  exit 1
fi

echo "Script completed successfully"