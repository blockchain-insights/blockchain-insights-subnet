#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Navigate to the script's directory
cd "$(dirname "$0")"

# Create and activate a Python virtual environment
if [ ! -d "../venv_benchmark" ]; then
    python3 -m venv ../venv_benchmark
fi
source ../venv_benchmark/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r ../requirements.txt

# Set PYTHONPATH
export PYTHONPATH=$(pwd)/..
echo "PYTHONPATH is set to $PYTHONPATH"

# Validate required arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <db-type> <blockchain> [additional locust args]"
    echo "Example: $0 memgraph bitcoin --headless -u 50 -r 10 --run-time 1m"
    deactivate
    exit 1
fi

DB_TYPE=$1
BLOCKCHAIN=$2
shift 2 # Shift the arguments to access any additional Locust options

# Navigate to the Locust directory and run Locust
cd ../src
locust -f benchmark/locustfile.py --db-type "$DB_TYPE" --blockchain "$BLOCKCHAIN" "$@"


# Deactivate virtual environment
deactivate
