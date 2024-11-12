# Chain Insights - The validator Setup

## Table of Contents
- [Setup](#setup)
  - [Validator Setup](#validator-setup)
    - [Prerequisites](#prerequisites)
    - [Clone Repository](#clone-repository)
    - [Env configuration](#env-configuration)
    - [Validator wallet creation](#validator-wallet-creation)
    - [Validator metadata configuration](#validator-metadata-configuration)
    - [Running the validator and monitoring](#running-the-validator-and-monitoring)
    - [Running the validator api gateway](#running-the-validator-api-gateway)

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
git fetch --all --tags
git tag -l
# use latest tag in next command
git checkout tags/1.2.0
```

#### Env configuration

Navigate to validator directory and copy the `.env.validator.example` file to `.env.validator.mainnet`.
```shell
cd ~/validator1
cp ./env/.env.validator.example ./env/.env.validator.mainnet
```

Now edit the `.env.validator.mainnet` file to set the appropriate configurations.
```shell
VALIDATOR_KEY=<your_validator_comx_key>

POSTGRES_DB=validator1
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeit456$

BITCOIN_NODE_RPC_URL=http://{put_proper_value_here}:{put_proper_value_here}@{put_proper_value_here}:8332
COMMUNE_NODE_RPC=wss://api.communeai.net

DATABASE_URL=postgresql+asyncpg://postgres:changeit456$@localhost:5432/validator1
REDIS_URL=redis://localhost:6379/0

PORT=9900
WORKERS=4
```

#### Validator wallet creation

```shell
comx key create validator1
comx key list
# transfer COMAI to your validator wallet for registration (aprox 10 COMAI are needed)
comx module register validator validator 20 --port 9900
# stake COMAI to your validator wallet
```

#### Validator metadata configuration

For validators participating in organic query support (running a gateway), it's necessary to register or update the validator with specific metadata. This metadata includes the gateway endpoint information that other validators will use to sync receipts with your validator.

If you're registering a new validator with metadata:
```shell
comx module register validator validator_name 20 --metadata '{"gateway":"http://your-validator-gateway-ip:9907"}'
```

If you need to update the metadata for an existing validator:
```shell
comx module update validator_name 20 --metadata '{"gateway":"http://your-validator-gateway-ip:9907"}'
```

Replace `validator_name` with your validator's name and adjust the gateway URL to match your validator's actual endpoint. The gateway URL should be accessible from the internet if you want other nodes to be able to query your validator.

Important considerations:
- Make sure your firewall allows incoming connections to your gateway port
- Use HTTPS if possible for production environments
- Ensure the gateway URL is stable and persistent
- The metadata update is required for participation in the organic query network

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

### Running the validator api gateway

```shell
cd ~/validator1
pm2 start ./scripts/run_gateway.sh --name gateway
pm2 save
```