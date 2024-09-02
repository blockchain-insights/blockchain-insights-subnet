# Chain Insights Subnet - The Miner Setup

## Table of Contents
- [Setup](#setup)
  - [Miner Setup](#miner-setup)
    - [Install Python and Communex](#install-python-and-communex)
    - [Create Wallet](#create-wallet)
    - [Clone Repository](#clone-repository)
    - [Configure Miner Environment](#configure-miner-environment)
    - [Run Multiple Miners](#run-multiple-miners)
    - [Install PM2](#install-pm2)
    - [Continuously Run the Miner](#continuously-run-the-miner)

## Setup

### Miner Setup

Prerequisites:
- Ubuntu 22.04 LTS
- Python 3.10+
- Node.js 18.x
- PM2
- Communex
- Git

```
sudo apt update
sudo apt upgrade -y
sudo apt install python3-pip
sudo apt install git
sudo apt install build-essential libssl-dev libffi-dev python3-dev

pip install communex

curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install pm2@latest -g
pm2 --version

pm2 link {private} {public}

pm2 startup systemd
pm2 save
```

#### Clone Repository
```
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner1
cd miner1
cp /env/.env.miner.example .env.miner.mainnet
./scripts/run_miner.sh
```

#### Env configuration

Navigate to miner directory and copy the `.env.miner.example` file to `.env.miner.mainnet`.
```
cd miner1
cp /env/.env.miner.example .env.miner.mainnet
```

Now edit the `.env.miner.mainnet` file to set the appropriate configurations.
```
NET_UID=20
MINER_KEY=miner1
MINER_NAME=miner1
NETWORK=bitcoin

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

```
comx comx key create miner1
comx key list
# transfer COMAI to your miner wallet ( aprox 10 COMAI)
comx module register miner1 miner1 --port XXXX
```

### Running the miner and monitoring
```
# use pm2 to run the miner
pm2 start ./scripts/run_miner.sh --name miner1
pm2 save
```


### Run Multiple Miners

To run multiple miners on a single machine, our proposal is following:

1. Clone the repository into different directories (e.g., `miner1`, `miner2`, `minerN`).
2. Set proper ports in the `.env` files for each miner.

```sh
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner1
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner2
# Repeat for minerN
```

- Edit the `.env` files in each directory to set unique ports and other necessary configurations.
 