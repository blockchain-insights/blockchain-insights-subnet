#!/bin/bash

python3 -m venv venv_gateway
source venv_gateway/bin/activate
pip install -r requirements.txt

cp -r env venv_gateway/

export PYTHONPATH=$(pwd)
echo "PYTHONPATH is set to $PYTHONPATH"
NETWORK_TYPE=${1:-mainnet}
cd src
python3 subnet/gateway/main.py $NETWORK_TYPE

deactivate