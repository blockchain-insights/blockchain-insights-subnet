# Chain Insights - The validator Setup

## Table of Contents
- [Setup](#setup)
  - [Validator Setup](#validator-setup)
    - [Prerequisites](#prerequisites)
    - [Clone Repository](#clone-repository)
    - [Env configuration](#env-configuration)
    - [Validator wallet creation](#validator-wallet-creation)
    - [Running the validator and monitoring](#running-the-validator-and-monitoring)
    - [Running the validator api](#running-the-validator-api)
    - [Running the miner leaderboard](#running-the-miner-leaderboard)

## Setup

### Validator Setup

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
sudo apt install python3-pip python3-venv python3-dev git build-essential libssl-dev libffi-dev ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

pip install communex

curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install pm2 -g
pm2 startup
```

#### Clone Repository

```shell
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git ~/validator1
```

#### Env configuration

Navigate to validator directory and copy the `.env.validator.example` file to `.env.validator.mainnet`.
```shell
cd ~/validator1
cp ./env/.env.validator.example ./env/.env.validator.mainnet
```

Now edit the `.env.validator.mainnet` file to set the appropriate configurations.
```shell
ITERATION_INTERVAL=512
MAX_ALLOWED_WEIGHTS=32
NET_UID=20
VALIDATOR_KEY=<your_validator_comx_key>
LLM_QUERY_TIMEOUT=120
QUERY_TIMEOUT=120
CHALLENGE_TIMEOUT=120

POSTGRES_DB=validator1
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeit456$

BITCOIN_NODE_RPC_URL=http://{put_proper_value_here}:{put_proper_value_here}@{put_proper_value_here}:8332
DATABASE_URL=postgresql+asyncpg://postgres:changeit456$@localhost:5432/validator1

API_RATE_LIMIT=1000
REDIS_URL=redis://localhost:6379/0
LLM_API_KEY={put_proper_value_here}
LLM_TYPE=openai
PORT=9900
WORKERS=4

PROMPT_FREQUENCY=100
PROMPT_THRESHOLD=100

FUNDS_FLOW_CHALLENGE_FREQUENCY=10
FUNDS_FLOW_CHALLENGE_THRESHOLD=100
BALANCE_TRACKING_CHALLENGE_FREQUENCY=10
BALANCE_TRACKING_CHALLENGE_THRESHOLD=100
```

#### Validator wallet creation

```shell
comx key create validator1
comx key list
# transfer COMAI to your validator wallet for registration (aprox 10 COMAI are needed)
comx module register validator validator 20 --port 9900
# stake COMAI to your validator wallet
```
 

### Running the validator and monitoring

Start required infrastructure by navigating to ops directory and running the following commands:
```shell
cd ./ops/validator
docker compose up -d
```

Then run the validator:
```shell
# use pm2 to run the validator
cd ~/validator1
pm2 start ./scripts/run_validator.sh --name validator
pm2 save
```

Or run the validator in auto update mode:
```shell
cd ~/validator1
pm2 start ./scripts/run_validator_auto_update.sh --name validator -- mainnet validator
pm2 save
```

### Running the validator api

```shell
cd ~/validator1
pm2 start ./scripts/run_validator_api.sh --name validator-api
pm2 save
```

Or run the validator api in auto update mode:
```shell
cd ~/validator1
pm2 start ./scripts/run_validator_api_auto_update.sh --name validator-api -- mainnet validator-api
pm2 save
```

### Running the miner leaderboard

```shell
cd ~/validator1
pm2 start ./scripts/run_miner_leaderboard.sh --name miner-leaderboard
pm2 save
```

Or run the miner leaderboard in auto update mode:
```shell
cd ~/validator1
pm2 start ./scripts/run_miner_leaderboard_auto_update.sh --name miner-leaderboard -- mainnet leaderboard
pm2 save
```

```
