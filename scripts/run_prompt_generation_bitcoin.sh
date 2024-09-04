#!/bin/bash

python3 -m venv venv_validator
source venv_validator/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$(pwd)
echo "PYTHONPATH is set to $PYTHONPATH"
NETWORK_TYPE=${1:-mainnet}
NETWORK=${2:-bitcoin}
FREQUENCY=${3:-1}
TRESHOLD=${4:-100}


cd src
python3 subnet/validator/llm_prompt_utility.py $NETWORK_TYPE $NETWORK $FREQUENCY $TRESHOLD

