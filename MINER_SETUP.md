# Chain Insights Subnet - The Miner Setup

## Table of Contents
- [Setup](#setup)
  - [Miner Setup](#miner-setup)
    - [Prerequisites](#prerequisites)
    - [Clone repository](#clone-repository)
    - [Env configutaion](#env-configuration)
    - [Miner wallet creation](#miner-wallet-creation)
    - [Running the miner](#running-the-miner-and-monitoring)
    - [Run multiple miners](#run-multiple-miners)

## Setup

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
sudo apt install python3-pip python3-dev git build-essential libssl-dev libffi-dev

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

POSTGRES_USER=bitcoin
POSTGRES_PASSWORD={put_proper_value_here}
POSTGRES_HOST={put_proper_value_here}
POSTGRES_PORT={put_proper_value_here}
POSTGRES_DB={put_proper_value_here}

DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

GRAPH_DATABASE_URL={put_proper_value_here}
GRAPH_DATABASE_USER={put_proper_value_here}
GRAPH_DATABASE_PASSWORD={put_proper_value_here}

BITCOIN_NODE_RPC_URL=http://{put_proper_value_here}:{put_proper_value_here}@{put_proper_value_here}:8332
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

To run multiple miners on a single machine, our proposal is following:

1. Start by [Clone repository](#clone-repository) into different directories (e.g., `miner1`, `miner2`, `minerN`).
2. Continue with the instructions again for the new miner, but remember to set unique ports in the `.env.miner.mainnet` files and when registering each miner.

```shell
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner1
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner2
# Repeat for minerN, then continue with the instructions for each of them
```