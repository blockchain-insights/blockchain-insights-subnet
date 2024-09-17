# Chain Insights - The Miner Setup

## Table of Contents
- [Setup](#setup)
  - [Blockchain Indexer Setup](#blockchain-indexer-setup)
    - [Bitcoin](#bitcoin-blockchain-indexer-setup)
  - [Miner Setup](#miner-setup)
    - [Prerequisites](#prerequisites)
    - [Clone repository](#clone-repository)
    - [Env configutaion](#env-configuration)
    - [Miner wallet creation](#miner-wallet-creation)
    - [Running the miner](#running-the-miner-and-monitoring)
    - [Run multiple miners](#run-multiple-miners)

## Setup

### Blockchain Indexer Setup

Miner requires a blockchain indexer to be able to fetch the blockchain data. The indexer should be running and accessible to the miner.
At the moment we deliver open source version of the Bitcoin Blockchain Indexer. There is also an Ethereum Blockchain Indexer available, but it is not operational, and should be used as a reference only for building custom implementation by individual miners.

#### Bitcoin Blockchain Indexer Setup
  - [Bitcoin Blockchain Indexer](https://github.com/blockchain-insights/blockchain-insights-indexer-bitcoin)
  
### Miner Setup

#### Prerequisites

- Ubuntu 22.04 LTS (or similar)
- Python 3.10+
- Node.js 18.x+
- PM2
- Communex
- Git

```shell
sudo apt update
sudo apt upgrade -y
sudo apt install python3-pip python3-venv python3-dev git build-essential libssl-dev libffi-dev

pip install communex

curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install pm2 -g
pm2 startup
```

#### Clone Repository

```shell
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner1
```

#### Env configuration

Navigate to miner directory and copy the `.env.miner.example` file to `.env.miner.mainnet`.
```shell
cd miner1
cp /env/.env.miner.example .env.miner.mainnet
```

Now edit the `.env.miner.mainnet` file to set the appropriate configurations:
```shell
NET_UID=20
MINER_KEY=miner1
MINER_NAME=miner1
NETWORK=bitcoin
PORT=9962

DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

GRAPH_DATABASE_URL={put_proper_value_here}
GRAPH_DATABASE_USER={put_proper_value_here}
GRAPH_DATABASE_PASSWORD={put_proper_value_here}

LLM_API_KEY={put_proper_value_here}
LLM_TYPE=openai
```
 
#### Miner wallet creation

```shell
comx key create miner1
comx key list
# transfer COMAI to your miner wallet for registration (aprox 10 COMAI are needed)
comx module register miner1 miner1 20 --port 9962
```

### Running the miner and monitoring

```shell
# use pm2 to run the miner
pm2 start ./scripts/run_miner.sh --name miner1
pm2 save
```


### Run Multiple Miners

To run multiple miners on a single machine, you can create additional `.env.miner.mainnet` files, set unique ports and registered keys in them, then pass it to pm2 like this for example:

```shell
pm2 start ./scripts/run_miner.sh --name miner2 --env .env.miner2.mainnet
pm2 save
# Repeat for minerN
```