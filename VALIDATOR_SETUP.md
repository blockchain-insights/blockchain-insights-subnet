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


### Validator Setup

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

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

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
```

#### Env configuration

Navigate to miner directory and copy the `.env.miner.example` file to `.env.miner.mainnet`.
```
cd miner1
cp /env/.env.validator.example .env.validator.mainnet
```

Now edit the `.env.validator.mainnet` file to set the appropriate configurations.
```
ITERATION_INTERVAL=100
MAX_ALLOWED_WEIGHTS=420
NET_UID=20
VALIDATOR_KEY=valdiator
LLM_QUERY_TIMEOUT=120
QUERY_TIMEOUT=120
CHALLENGE_TIMEOUT=120

POSTGRES_DB=validator
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeit456$

BITCOIN_NODE_RPC_URL=http://{put_proper_value_here}:{put_proper_value_here}@{put_proper_value_here}:8332
DATABASE_URL=postgresql+asyncpg://postgres:changeit456$@localhost:5432/validator

API_RATE_LIMIT=1000
REDIS_URL=redis://localhost:6379/0
LLM_API_KEY={put_proper_value_here}
LLM_TYPE=openai
PORT=9900
WORKERS=4

```
 
#### Validator wallet creation

```
comx comx key create miner1
comx key list
# transfer COMAI to your miner wallet ( aprox 10 COMAI)
comx module register miner1 miner1 20 --port XXXX
```



### Running the validator and monitoring
start required infrastructure by running navigate to ops directory and run the following command
```docker compose up -d```

then run the validator

```
# use pm2 to run the miner
pm2 start ./scripts/run_miner.sh --name miner1
pm2 save
```
 