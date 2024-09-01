# Chain Insights Subnet 

Table of contents:
- [Setup](#setup)

## Setup

1) Install python and communex
```
sudo apt update 
sudo apt upgrade -y
sudo apt install python3-pip
sudo apt install git
sudo apt install build-essential libssl-dev libffi-dev python3-dev cmake

pip install communex

```
 
2) create wallet
```
comx comx key create miner1
```
3) git pull

```
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner1
cd miner1
cp /env/.env.miner.example .env.miner.mainnet
./scripts/run_miner.sh
```
``
./scripts/run_miner.sh
```

``

4) description of miner .env file

5) how to run multiple miners on single machine?
git cloner into miner1 miner2 minerN
set proper ports in .env files  