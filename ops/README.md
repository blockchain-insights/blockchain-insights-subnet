```markdown
# Chain Insights Subnet

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

#### Install Python and Communex

```sh
sudo apt update
sudo apt upgrade -y
sudo apt install python3-pip
sudo apt install git
sudo apt install build-essential libssl-dev libffi-dev python3-dev cmake

pip install communex
```

#### Create Wallet

```sh
comx comx key create miner1
# Show key address
# Send COMAI to the wallet (10?)
# Register module
```

#### Clone Repository

```sh
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner1
cd miner1
cp /env/.env.miner.example .env.miner.mainnet
./scripts/run_miner.sh
```

#### Configure Miner Environment

- The `.env.miner.mainnet` file should be configured with the appropriate settings for your miner.
- Reference to Bitcoin indexer or your custom indexer should be included.

#### Run Multiple Miners

To run multiple miners on a single machine:

1. Clone the repository into different directories (e.g., `miner1`, `miner2`, `minerN`).
2. Set proper ports in the `.env` files for each miner.

```sh
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner1
git clone https://github.com/blockchain-insights/blockchain-insights-subnet.git miner2
# Repeat for minerN
```

- Edit the `.env` files in each directory to set unique ports and other necessary configurations.

### Install PM2

To install PM2, a process manager for Node.js applications, follow these steps:

1. Install Node.js and npm (if not already installed):

```sh
sudo apt update
sudo apt install nodejs npm -y
```

2. Install PM2 globally using npm:

```sh
sudo npm install -g pm2
```

### Continuously Run the Miner

To continuously run the miner using PM2, follow these steps:

1. Navigate to the miner directory:

```sh
cd miner1
```

2. Start the miner script using PM2:

```sh
pm2 start ./scripts/run_miner.sh --name miner1
```

3. To ensure PM2 restarts the miner on system reboots, save the PM2 process list and setup startup script:

```sh
pm2 save
pm2 startup
```

4. Follow the instructions provided by the `pm2 startup` command to enable the startup script. This usually involves running a command with `sudo`.

### Managing PM2 Processes

- To list all PM2 processes:

```sh
pm2 list
```

- To stop a PM2 process:

```sh
pm2 stop miner1
```

- To restart a PM2 process:

```sh
pm2 restart miner1
```

- To view logs of a PM2 process:

```sh
pm2 logs miner1
```
```