# Chain Insights Subnet - The validator Setup

## Table of Contents
- [Setup](#setup)
  - [Validator Setup](#validator-setup)
    - [Install Python and Communex](#install-python-and-communex)
    - [Create Wallet](#create-wallet)
    - [Clone Repository](#clone-repository)
    - [Configure Validator Environment](#configure-validator-environment)
    - [Run Multiple validators](#run-multiple-validators)
    - [Install PM2](#install-pm2)
    - [Continuously Run the Validator](#continuously-run-the-validator)

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
sudo apt update
sudo apt upgrade -y

sudo apt autoremove

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

pm2 startup systemd
pm2 save

```

#### Validator wallet creation

```
comx key create <your_validator_comx_key>
### example: comx key create my_validator_key
comx key list

# transfer COMAI to your validator wallet ( aprox 10 COMAI)
# stake COMAI to your validator wallet

# register your validator module with your validator's key
comx module register <your_validator_comx_name> <your_validator_comx_key> 20
### example: comx module register my_validator_name  my_validator_key 20

```


#### Clone Repository
```
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git ~/validator1

```

#### Env configuration

Navigate to validator directory and copy the `.env.validator.example` file to `.env.validator.mainnet`.
```
cd ~/validator1
cp ./env/.env.validator.example ./env/.env.validator.mainnet

```

Now edit the `.env.validator.mainnet` file to set the appropriate configurations.
```
ITERATION_INTERVAL=100
MAX_ALLOWED_WEIGHTS=420
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

```
 

### Running the validator and monitoring
start required infrastructure by running navigate to ops directory and run the following command
```

cd ./ops/validator
docker compose up -d
```

then run the validator

```
# use pm2 to run the validator
cd ~/validator1
pm2 start ./scripts/run_validator.sh --name <your_validator_name>
### example: pm2 start ./scripts/run_validator.sh --name my_validator_name
pm2 save
```
 