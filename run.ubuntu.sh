#!/bin/bash

# Load env variables
set -o allexport
. ./.env
set +o allexport

# Exit on error, undefined variable
set -eu

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
    if [ $BRC20_PROG_RPC_SERVER_USER == "brc20prog" ] || [ $BRC20_PROG_RPC_SERVER_PASSWD == "brc20prog" ]; then
        echo "You are using the default username or password for the RPC server, and the server is accessible externally. Please change BRC20_PROG_RPC_SERVER_USER and BRC20_PROG_RPC_SERVER_PASSWD to secure values in the .env file."
        exit 1
    fi
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

# Install dependencies
cargo install --locked --git https://github.com/bestinslot-xyz/OPI.git brc20-index
cargo install --locked --git https://github.com/bestinslot-xyz/brc20-programmable-module.git

# check if screen is running and kill existing sessions
if command -v screen &> /dev/null
then
    SCREEN_SESSIONS=$(screen -ls | grep -c "brc20-prog\|brc20-index" || true)
    if [ "$SCREEN_SESSIONS" -gt 0 ]; then
        echo "Killing existing screen sessions..."
        screen -ls | grep -E "brc20-prog|brc20-index" | awk '{print $1}' | xargs -I {} screen -S {} -X quit
    fi
else
    echo "Screen could not be found, installing..."
    sudo apt install -y screen
fi

# Change postgres user password
echo "Setting PostgreSQL password..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '$DB_PASSWD';"

echo "Starting BRC20 Programmable Module and BRC20 Indexer in detached screen sessions..."

screen -dmS brc20-prog bash -c 'while true; do brc20-prog -l info; sleep 1; done;'
screen -dmS brc20-index bash -c 'while true; do brc20-index -l info; sleep 1; done;'

echo "BRC20 Programmable Module and BRC20 Indexer are running in detached screen sessions."
echo ""
echo "To attach to the BRC20 Programmable Module session, use: screen -dr brc20-prog"
echo "To attach to the BRC20 Indexer session, use: screen -dr brc20-index"
echo ""
echo "Setup complete!"