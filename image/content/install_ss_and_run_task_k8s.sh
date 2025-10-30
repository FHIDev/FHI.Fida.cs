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

# Use writable work directory (defaults to /work mounted as emptyDir in Kubernetes)
WORK_DIR="${CS9_PATH:-/work}"
if [ ! -d "$WORK_DIR" ]; then
  echo "Work directory $WORK_DIR does not exist. Creating it."
  mkdir -p "$WORK_DIR"
fi

# Clone the repository and checkout the specified branch
git -C "$WORK_DIR" clone -b "$BRANCH" "$REPO_URL"

# Check if the cloning was successful
if [ $? -ne 0 ]; then
  echo "Failed to clone repository from $REPO_URL (branch: $BRANCH)"
  exit 1
fi

# Build the R package from the work directory (R CMD build outputs tarball to current dir)
cd "$WORK_DIR"
R CMD build "$REPOSITORY"

# Check if the build was successful
if [ $? -ne 0 ]; then
  echo "Failed to build the R package from ${WORK_DIR}/${REPOSITORY}"
  exit 1
fi

# Find the most recent tarball in the work directory
TARBALL=$(ls -t "${REPOSITORY}"_*.tar.gz | head -n 1)

if [ -z "$TARBALL" ]; then
  echo "No tarball found for ${REPOSITORY} in ${WORK_DIR}"
  exit 1
fi

# Install the R package to a user-writable library (use work directory for R user library)
# This avoids permission issues when running as non-root user in containers
export R_LIBS_USER="$WORK_DIR/R_library"
mkdir -p "$R_LIBS_USER"
Rscript -e "install.packages('$TARBALL', repos = NULL, type = 'source')"

# Check if the installation was successful
if [ $? -ne 0 ]; then
  echo "Failed to install the R package from $TARBALL"
  exit 1
fi

# Run the specified R command
# CS9 environment variables are inherited from the container environment (set by Kubernetes)
# and are automatically available to R via Sys.getenv()
Rscript -e "${REPOSITORY}::global\$ss\$run_task('${TASK}')"

# Check if the R command execution was successful
if [ $? -ne 0 ]; then
  echo "Failed to run the specified R command"
  exit 1
fi

echo "Script completed successfully"