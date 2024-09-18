#!/bin/bash

# Path to the version file
VERSION_FILE="version.txt"

# Function to get the current version
get_current_version() {
    # Read the version from the version.txt file
    if [[ -f $VERSION_FILE ]]; then
        cat $VERSION_FILE
    else
        echo "0"  # Return a default version if version.txt doesn't exist
    fi
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
            pm2 restart "$PM2_PROCESS_NAME"

            # Exit the update checker
            exit 0
        fi

        # Wait before checking again (e.g., check every 5 minutes)
        sleep 300
    done
}

# Check if the correct number of arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <network_type> <pm2_process_name>"
    exit 1
fi

# Get arguments
NETWORK_TYPE=$1
PM2_PROCESS_NAME=$2

# Activate the virtual environment and install dependencies
python3 -m venv venv_validator
source venv_validator/bin/activate
pip install -r requirements.txt

# Copy environment files
cp -r env venv_validator/

# Set PYTHONPATH
export PYTHONPATH=$(pwd)
echo "PYTHONPATH is set to $PYTHONPATH"

# Get the current version before starting
current_version=$(get_current_version)

# Start the update checker in the background
check_for_updates &

# Start the main Python script
cd src
python3 subnet/cli.py $NETWORK_TYPE

# When the main script exits, deactivate the virtual environment
deactivate
