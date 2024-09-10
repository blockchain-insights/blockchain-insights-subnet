#!/bin/bash

key=${1:-owner}

for (( c=1; c<=99999; c++ ))
do
   comx --testnet balance run-faucet "$key"
done