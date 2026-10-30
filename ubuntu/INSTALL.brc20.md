# Detailed Installation Guide for OPI Light Client on Ubuntu

This guide sets up the OPI Light Client on Ubuntu by hand. One binary, `opi-indexer` from the [OPI repository](https://github.com/bestinslot-xyz/OPI), runs the BRC-20 light client with the BRC2.0 programmable module in process, and serves the optional OPI API. There is no bitcoind: the light client takes the OPI network's verified block data and recomputes every hash itself.

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

### Installing build tools and Cargo

1) The BRC2.0 engine's RocksDB compiles C++ and runs bindgen:

```sh
sudo apt install -y build-essential clang libclang-dev cmake pkg-config curl
```

2) Install cargo if you don't have it ([guide](https://doc.rust-lang.org/cargo/getting-started/installation.html)), and keep the stable toolchain current: `opi-indexer` needs Rust 1.95 or later.

```sh
curl https://sh.rustup.rs -sSf | sh
rustup update stable
```

## Installing opi-indexer

```sh
SQLX_OFFLINE=true cargo install --locked --git https://github.com/bestinslot-xyz/OPI.git --branch opi-monolith opi-indexer
```

## Configuration

`opi-indexer` reads `.env` from its working directory. The `.env` in this directory is a light-client setup; set at least `DB_PASSWD` and `NETWORK_TYPE`. The keys a light client needs:

```sh
OPERATION_MODE="light"
NETWORK_TYPE="mainnet" # or signet

# The BRC2.0 engine's Bitcoin lookups come from this cache, filled from the OPI network
BITCOIN_RPC_CACHE_ENABLED="true"

DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_DATABASE="postgres"
DB_PASSWD="<PASSWORD>"

# The engine's data directory
BRC20_PROG_DB_PATH="data/brc20-prog"
# The engine's public JSON-RPC; it takes no credentials, so keep it on loopback or firewall it
BRC20_PROG_RPC_SERVER_URL="127.0.0.1:18545"
```

The API reads the same `DB_*` keys, plus `API_HOST`, `API_PORT`, `API_TRUSTED_PROXY_CNT` and `RATE_LIMIT_*`. The OPI repository's `.env_sample` describes every key.

Keys of the earlier setup that `opi-indexer` ignores: `BRC20_PROG_ENABLED`, `BRC20_PROG_RPC_URL`, `BRC20_PROG_RPC_USER`, `BRC20_PROG_RPC_PASSWORD`, `BRC20_PROG_BALANCE_SERVER_ADDR`, `BRC20_PROG_BALANCE_SERVER_URL`, `BITCOIN_RPC_PROXY_SERVER_ENABLED`, `BITCOIN_RPC_PROXY_SERVER_ADDR`, `BITCOIN_RPC_URL` and `BITCOIN_RPC_NETWORK`. `BRC20_PROG_RPC_SERVER_ENABLE_AUTH`, `BRC20_PROG_RPC_SERVER_USER` and `BRC20_PROG_RPC_SERVER_PASSWORD` do not apply to the engine's JSON-RPC, and `BRC20_PROG_RPC_SERVER_ENABLE_AUTH=true` without a user and password stops the engine from opening, so remove them.

## Running Light Client

```sh
opi-indexer brc20 light
```

It stops on SIGINT or SIGTERM after its current block. Run it under a supervisor such as systemd that restarts it: `run.ubuntu.sh` installs the `opi-light` service for this.

Moving from the separate `brc20-index` and `brc20-prog` processes: stop both, keep `DB_*` and `BRC20_PROG_DB_PATH` pointed at their database and engine data, and start `opi-indexer brc20 light`. It resumes from the last block. On its first start it checks the current-balance tables once, and rebuilds them when an older version left them partly built. When the engine data is behind the database, it rolls back to the engine's height and replays those blocks with every hash verified.

### (Optional) Run API

```sh
opi-indexer api
```

It serves the OPI API on `API_HOST:API_PORT`: the BRC-20 routes of the earlier JS API, plus ticker, holder, wallet and event-feed routes. `run-api.ubuntu.sh` installs the `opi-api` service for it.

## Checking

```sh
curl -s localhost:8000/v1/brc20/block_height
```

The height follows the OPI network's best verified block.
