#!/bin/bash
comx module register $MINER_KEY $MINER_NAME 20 --port $PORT && python3 subnet/miner/miner.py $NETWORK_TYPE
