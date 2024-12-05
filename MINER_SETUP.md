# Chain Insights - The Miner Setup

## Table of Contents
- [Chain Insights - The Miner Setup](#chain-insights---the-miner-setup)
  - [Table of Contents](#table-of-contents)
  - [Setup](#setup)
  - [Minimum Requirements](#minimum-requirements)
    - [Internet Access](#internet-access)
    - [Bitcoin:](#bitcoin)
    - [Indexers and Miners](#indexers-and-miners)
    - [Commune Recommended Requirements](#commune-recommended-requirements)
    - [Blockchain Indexer Setup](#blockchain-indexer-setup)
      - [1st Step: Indexer Setup](#1st-step-indexer-setup)
    - [Miner Setup](#miner-setup)
      - [Prerequisites](#prerequisites)
      - [Clone Repository](#clone-repository)
      - [Env configuration](#env-configuration)
      - [Miner wallet creation](#miner-wallet-creation)
    - [Running the miner and monitoring](#running-the-miner-and-monitoring)
    - [Run Multiple Miners](#run-multiple-miners)

## Setup

## Minimum Requirements

> The recommended minimum requirements are not a guarantee of performance, monitor your ressources and logs as demand increasese more ressources will be required to fullfill the demand. The most powerful miners will get more incentives.

### Internet Access

- Minimum: 1Gb downstream / 256Mb Upstream is required
- Recommended: 1Gb Full Duplex

### Bitcoin:

> Bitcoin Archive Node:

- 8vCPU/ 1GB RAM / 1TB NVMe
- Alternative You can use a JSON-RPC provider

> Money Flow database engines

- Neo4j: 8vCPU/128GB RAM with 2TB NVMe
  - Recommended 16vCPU/1.5TB RAM with 3TB NVMe

or

- Memgraph: 16vCPU/2TB RAM with 3TB NVMe
  - Recommended 64vCPU/2.3TB RAM with 3TB NVMe

> Balance Tracking

- Postgres: 8vCPU/64GB RAM with 1TB NVMe
  - Recommended 16vCPU/256GB RAM with 1.5TB NVMe

### Indexers and Miners

> Initial Indexing requires lots of ressources and the time to index depends on the number of vCPU and RAM
> Indexing from Pickle files will require 10 to 21 days minimum depending on the speed of your hardware.
> When the latest block is indexed the indexers takes less ressources:

- Indexers: 2vCPU /2GB RAM

> Minimum Requirements per miner

- Miner: 1vCPU / 1GB RAM

### Commune Recommended Requirements


- Commune Archive Node: 2vCPU/64GB RAM / 1TB NVMe
- Money Flow
  - Neo4j: 16vCPU/128GB RAM / 1TB NVMe
  - Or
  - Memgraph: 16vCPU/784GB RAM / 2TB NVMe (2 Snapshots)
- Balance Tracking
  - Postgres: 8vCPU/128GB RAM / 1TB NVMe
- Indexers (When lastblock is indexed)
  - Substrate: 1 vCPU/1GB RAM
  - SubQuery Money Flow: 1vCPU/1GB RAM
  - SubQuery Balance Tracking: 1vCPU/1GB RAM
  - Indexer-rs Money Flow: 8vCPU/16GB RAM
  - Indexer-rs Balance Tracking 1vCPU/8GB RAM
- Miner (per miner)
  - 1vCPU/1GB RAM

### Blockchain Indexer Setup

Miner requires a blockchain indexer to be able to fetch the blockchain data. The indexer should be always running to provide data to the miner.

We provide an open source version of the Bitcoin Blockchain Indexer. An open source Ethereum indexer in development, and will be required for all miners that wants to deliver data for the L1 and L2 EVM chains.

We provide an open source Indexer for Polkadot and substrates that is compatible with CommuneAI and Bittensor.

Miners are allowed to improve the code but not the structure of the Graph or TimescaleDB database.

#### 1st Step: Indexer Setup

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
git fetch --all --tags
git tag -l
# use latest tag in next command
git checkout tags/1.2.0
```

#### Env configuration

Navigate to miner directory and copy the `.env.miner.example` file to `.env.miner.mainnet`.
```shell
cd miner1
cp /env/.env.miner.example .env.miner.mainnet
```

Now edit the `.env.miner.mainnet` file to set the appropriate configurations:

```sh
NET_UID=20
MINER_KEY=miner1
MINER_NAME=miner1

# NETWORK values `bitcoin` or `commune`
NETWORK=bitcoin

PORT=9962

DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

GRAPH_DATABASE_URL={put_proper_value_here}
GRAPH_DATABASE_USER={put_proper_value_here}
GRAPH_DATABASE_PASSWORD={put_proper_value_here}
```

**NETWORK values:**

- `NETWORK=bitcoin` : Bitcoin $BTC Indexers
- `NETWORK=commune` : CommuneAI $COMAI Indexers

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
