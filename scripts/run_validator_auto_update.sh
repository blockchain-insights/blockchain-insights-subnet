#!/bin/bash

# Function to get the current version
get_current_version() {
    python -c "from subnet import __init__; print(__init__.version)"
}

# Function to check for updates and restart if needed
check_for_updates() {
    while true; do
        # Fetch the latest changes from the GitHub repository
        git fetch origin
        git reset --hard origin/main

        # Get the new version after pulling the latest changes
        new_version=$(get_current_version)

        # Compare versions
        if [ "$current_version" != "$new_version" ]; then
            echo "Version has changed from $current_version to $new_version. Restarting script."

            # Kill the running Python process
            pkill -f "python3 subnet/cli.py"

            # Deactivate the current virtual environment
            deactivate

            # Restart the script using pm2
            pm2 restart 0

            # Exit the update checker
            exit 0
        fi

        # Wait before checking again (e.g., check every 5 minutes)
        sleep 300
    done
}

# Activate the virtual environment and install dependencies
python3 -m venv venv_validator
source venv_validator/bin/activate
pip install -r requirements.txt

# Copy environment files
cp -r env venv_validator/

# Set PYTHONPATH
export PYTHONPATH=$(pwd)
echo "PYTHONPATH is set to $PYTHONPATH"

# Define network type
NETWORK_TYPE=${1:-mainnet}

# Get the current version before starting
current_version=$(get_current_version)

# Start the update checker in the background
check_for_updates &

# Start the main Python script
cd src
python3 subnet/cli.py $NETWORK_TYPE

# When the main script exits, deactivate the virtual environment
deactivate
