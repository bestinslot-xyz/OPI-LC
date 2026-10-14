#!/bin/bash

# Load env variables
set -o allexport
. ./.env
set +o allexport

# Exit on error, undefined variable
set -eu

if [ $REPORT_TO_INDEXER == "true" ]; then
    if [ "$REPORT_NAME" == "opi-brc20-lc" ]; then
        echo "REPORT_NAME is set to default. Please set a REPORT_NAME in the .env file to describe who is reporting."
        exit 1
    fi
fi

# Check for secure configurations
if [ "$DB_PASSWD" == "postgres" ]; then
    echo "Please change the DB_PASSWD variable in the .env file to a secure password."
    exit 1
fi

if ! [[ $BRC20_PROG_RPC_SERVER_URL == "127.0.0.1"* ]]; then
    if ! [ $BRC20_PROG_RPC_SERVER_ENABLE_AUTH == "true" ]; then
        echo "You have not enabled authentication for the RPC server, and the server is accessible externally. Please change BRC20_PROG_RPC_SERVER_ENABLE_AUTH to true in the .env file."
        exit 1
    fi
    if [ $BRC20_PROG_RPC_SERVER_USER == "brc20prog" ] || [ $BRC20_PROG_RPC_SERVER_PASSWORD == "brc20prog" ]; then
        echo "You are using the default username or password for the RPC server, and the server is accessible externally. Please change BRC20_PROG_RPC_SERVER_USER and BRC20_PROG_RPC_SERVER_PASSWD to secure values in the .env file."
        exit 1
    fi
fi

if ! [ $BRC20_PROG_RPC_SERVER_USER == $BRC20_PROG_RPC_USER ]; then
    echo "BRC20_PROG_RPC_SERVER_USER and BRC20_PROG_RPC_USER must be the same for authentication to work. Please fix this in the .env file."
    exit 1
fi
if ! [ $BRC20_PROG_RPC_SERVER_PASSWORD == $BRC20_PROG_RPC_PASSWORD ]; then
    echo "BRC20_PROG_RPC_SERVER_PASSWORD and BRC20_PROG_RPC_PASSWORD must be the same for authentication to work. Please fix this in the .env file."
    exit 1
fi

# Install postgres if not installed
if ! command -v psql &> /dev/null
then
    echo "PostgreSQL could not be found, installing..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql

    # Configure PostgreSQL
    sudo -u postgres psql -c "ALTER SYSTEM SET listen_addresses TO '*';"
    sudo -u postgres psql -c "ALTER SYSTEM SET max_connections TO 2000;"

    # Restart PostgreSQL to apply changes
    sudo systemctl restart postgresql
fi

# Create database if not exists
DB_EXIST=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_DATABASE'")
if [ "$DB_EXIST" != "1" ]; then
    echo "Creating database $DB_DATABASE..."
    sudo -u postgres psql -c "CREATE DATABASE $DB_DATABASE;"
fi

# Install cargo if not installed
if ! command -v cargo &> /dev/null
then
    sudo apt install -y clang curl pkg-config libssl-dev
    echo "Cargo could not be found, installing..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    . $HOME/.cargo/env
fi

if ! rustup toolchain list | grep -q "stable"; then
    rustup toolchain install stable
fi

rustup default stable
rustup update stable

# Install dependencies, pinned to the release tags this setup is validated against
BRC20_INDEX_VERSION="v2.0.13"
BRC20_PROG_VERSION="v0.16.1"
export CARGO_TARGET_DIR="$HOME/.cargo/target/OPI"
cargo install --locked --git https://github.com/bestinslot-xyz/OPI.git brc20-index --tag "$BRC20_INDEX_VERSION"
export CARGO_TARGET_DIR="$HOME/.cargo/target/brc20-programmable-module"
cargo install --locked --git https://github.com/bestinslot-xyz/brc20-programmable-module.git --tag "$BRC20_PROG_VERSION"

# Stop screen sessions left by setups that ran both processes under screen
if command -v screen &> /dev/null
then
    SCREEN_SESSIONS=$(screen -ls | grep -c "brc20-prog\|brc20-index" || true)
    if [ "$SCREEN_SESSIONS" -gt 0 ]; then
        echo "Killing existing screen sessions..."
        screen -ls | grep -E "brc20-prog|brc20-index" | awk '{print $1}' | xargs -I {} screen -S {} -X quit
    fi
fi

# Change postgres user password and grant all privileges on the database
echo "Setting PostgreSQL password..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '$DB_PASSWD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_DATABASE TO postgres;"

# Run both processes as systemd services: they restart on failure and start on boot.
# Each service loads .env from this directory the same way this script does.
SERVICE_USER=$(id -un)
SERVICE_DIR=$(pwd)
BRC20_PROG_BIN=$(command -v brc20-prog || true)
BRC20_INDEX_BIN=$(command -v brc20-index || true)
if [ -z "$BRC20_PROG_BIN" ] || [ -z "$BRC20_INDEX_BIN" ]; then
    echo "brc20-prog or brc20-index is not on PATH after cargo install. Add \$HOME/.cargo/bin to PATH and run this script again."
    exit 1
fi

echo "Installing systemd services brc20-prog and brc20-index..."

sudo tee /etc/systemd/system/brc20-prog.service > /dev/null <<EOF
[Unit]
Description=BRC20 Programmable Module (OPI light client)
Wants=network-online.target
After=network-online.target

[Service]
User=$SERVICE_USER
WorkingDirectory=$SERVICE_DIR
ExecStart=/bin/bash -c 'set -a; . ./.env; set +a; exec $BRC20_PROG_BIN -l info'
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/brc20-index.service > /dev/null <<EOF
[Unit]
Description=BRC20 Indexer (OPI light client)
Wants=network-online.target brc20-prog.service
After=network-online.target postgresql.service brc20-prog.service

[Service]
User=$SERVICE_USER
WorkingDirectory=$SERVICE_DIR
ExecStart=/bin/bash -c 'set -a; . ./.env; set +a; exec $BRC20_INDEX_BIN -l info'
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable brc20-prog brc20-index
sudo systemctl restart brc20-prog brc20-index

echo "BRC20 Programmable Module and BRC20 Indexer are running as systemd services."
echo ""
echo "To check their status, use: systemctl status brc20-prog brc20-index"
echo "To follow the BRC20 Programmable Module logs, use: journalctl -u brc20-prog -f"
echo "To follow the BRC20 Indexer logs, use: journalctl -u brc20-index -f"
echo ""
echo "Setup complete!"