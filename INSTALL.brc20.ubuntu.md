# Detailed Installation Guide for OPI Light Client on Ubuntu

This guide provides a setup for the OPI Light Client on Ubuntu. For a simple setup, you can run the provided script after modifying the `.env` file as needed:

```sh
bash run.ubuntu.sh
```

You'll need to start the BRC20 API afterwards if you want to use it:

```sh
bash run-api.ubuntu.sh
```

You can stop them by running:

```sh
bash stop.ubuntu.sh
bash stop-api.ubuntu.sh
```

## Installing Dependencies

### Installing PostgreSQL

1) First install and run postgresql binaries.

```sh
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql.service
```

2) Set some optional parameters, this step is *optional*.

```sh
sudo -u postgres psql -c "ALTER SYSTEM SET listen_addresses TO '*';"
sudo -u postgres psql -c "ALTER SYSTEM SET max_connections TO 2000;"
```

3) Set the password for default user. Replace `<password>` with your password. (do not use ! in password, it may interfere with shell escape)

```sh
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '<password>';"
```

4) Restart postgres service to apply new configuration.

```sh
sudo systemctl restart postgresql
```

### Installing Cargo

1) Install cargo if you don't have it. [guide](https://doc.rust-lang.org/cargo/getting-started/installation.html).

```sh
curl https://sh.rustup.rs -sSf | sh
```

## Setting up OPI v2 Light-Client

1) Clone the OPI repository

```sh
git clone https://github.com/bestinslot-xyz/OPI.git
cd OPI/modules/brc20_index
```

2) Set up environment for BRC20 indexer

A light client setup requires `OPERATION_MODE=light`, here's a sample `.env` file, it also runs a Bitcoin RPC proxy server to load and forward events from OPI in absence of a full node:

```sh
OPERATION_MODE="light"

DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_DATABASE="postgres"
DB_PASSWD="<PASSWORD>"

BRC20_PROG_ENABLED="true"
BRC20_PROG_RPC_URL="http://127.0.0.1:18545"
BRC20_PROG_BALANCE_SERVER_ADDR="127.0.0.1:18546"

BITCOIN_RPC_CACHE_ENABLED="true"
BITCOIN_RPC_PROXY_SERVER_ENABLED="true"
BITCOIN_RPC_PROXY_SERVER_URL="127.0.0.1:18547"
```

3) Clone the BRC2.0 repository

```sh
git clone https://github.com/bestinslot-xyz/brc20-programmable-module.git
cd brc20-programmable-module
```

4) Set up the environment for BRC2.0 programmable module

Bitcoin RPC needs to be pointed at the light client proxy for programmable module, as there's no real full node. Here's a sample `.env` file for BRC2.0 programmable module:

```sh
BRC20_PROG_BALANCE_SERVER_URL=http://localhost:18546
BITCOIN_RPC_URL=127.0.0.1:18547 # This points to the light client proxy server

BRC20_PROG_RPC_SERVER_URL=127.0.0.1:18545
BRC20_PROG_RPC_SERVER_ENABLE_AUTH=false

# Required for trace hash calculation
EVM_RECORD_TRACES=true
```

## Running Light Client

### Run BRC2.0 Programmable Module

```sh
cd brc20-programmable-module;
cargo build --release;
cd target/release;
./brc20-prog -l info
```

### Run OPI v2 Light Client

```sh
cd OPI/modules/brc20_index;
cargo build --release;
cd target/release;
./brc20-index -l info
```

### (Optional) Run API

#### Install NodeJS

These steps are following the guide at [here](https://github.com/nodesource/distributions).

```sh
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg

NODE_MAJOR=20
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list

sudo apt-get update
sudo apt-get install nodejs -y
```

#### Setup BRC20 API

1) Clone if you haven't already

```sh
git clone https://github.com/bestinslot-xyz/OPI.git
cd OPI/modules/brc20_api
```

1) Install node modules

```sh
npm install;
```

2) Set up the environment for the API

Here's a sample `.env` file for the API:

```sh
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_DATABASE="postgres"
DB_PASSWD="<PASSWORD>"
DB_SSL="true"
DB_MAX_CONNECTIONS=10

API_HOST="127.0.0.1"
API_PORT="8000"
API_TRUSTED_PROXY_CNT="0" # number of trusted proxies in front of API, set to 1 if using nginx reverse proxy

RATE_LIMIT_ENABLE="true" # enable rate limit
RATE_LIMIT_WINDOW_MS=1000 # 1 second
RATE_LIMIT_MAX=10 # limit each IP to 10 requests per windowMs
```

#### Start API

```sh
node api.js
```
