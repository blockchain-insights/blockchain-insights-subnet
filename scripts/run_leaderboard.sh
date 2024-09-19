#!/bin/bash

python3 -m venv venv_leaderboard
source venv_leaderboard/bin/activate
pip install -r requirements.txt

cp -r env venv_leaderboard/

export PYTHONPATH=$(pwd)
echo "PYTHONPATH is set to $PYTHONPATH"
NETWORK_TYPE=${1:-mainnet}
cd src
python3 subnet/validator/leaderboard.py $NETWORK_TYPE

deactivate