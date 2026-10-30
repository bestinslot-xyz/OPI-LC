#!/bin/bash

# Load env variables
set -o allexport
. ./.env
set +o allexport

# Exit on error, undefined variable
set -eu

# The OPI repository branch opi-indexer is installed from
OPI_BRANCH="opi-monolith"

if [ "${REPORT_TO_INDEXER:-}" == "true" ]; then
    if [ "${REPORT_NAME:-}" == "opi-brc20-lc" ]; then
        echo "REPORT_NAME is set to default. Please set a REPORT_NAME in the .env file to describe who is reporting."
        exit 1
    fi
fi

# Check for secure configurations
if [ "${DB_PASSWD:-}" == "postgres" ]; then
    echo "Please change the DB_PASSWD variable in the .env file to a secure password."
    exit 1
fi

if [ "${OPERATION_MODE:-}" != "light" ]; then
    echo "OPERATION_MODE must be light in the .env file."
    exit 1
fi

if [ -z "${BRC20_PROG_DB_PATH:-}" ]; then
    echo "Please set BRC20_PROG_DB_PATH in the .env file to the BRC2.0 engine's data directory."
    exit 1
fi

if ! [[ "${BRC20_PROG_RPC_SERVER_URL:-127.0.0.1:18545}" == "127.0.0.1"* ]]; then
    echo "Warning: the BRC2.0 JSON-RPC at $BRC20_PROG_RPC_SERVER_URL takes no credentials and is reachable from other hosts. Firewall it, or set BRC20_PROG_RPC_SERVER_URL to 127.0.0.1:18545."
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

# Build dependencies: the BRC2.0 engine's RocksDB compiles C++ and runs bindgen
sudo apt install -y build-essential clang libclang-dev cmake pkg-config curl

# Install cargo if not installed
if ! command -v cargo &> /dev/null
then
    echo "Cargo could not be found, installing..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    . $HOME/.cargo/env
fi

if ! rustup toolchain list | grep -q "stable"; then
    rustup toolchain install stable
fi

rustup default stable
rustup update stable

# Install opi-indexer, which runs the light client, the BRC2.0 engine and the API
export CARGO_TARGET_DIR="$HOME/.cargo/target/OPI"
SQLX_OFFLINE=true cargo install --locked --git https://github.com/bestinslot-xyz/OPI.git --branch "$OPI_BRANCH" opi-indexer

# Stop and remove the brc20-index and brc20-prog services of the earlier setup:
# opi-indexer replaces both, and opens the same database and engine data
for SERVICE in brc20-index brc20-prog; do
    if [ -f "/etc/systemd/system/$SERVICE.service" ]; then
        echo "Removing the $SERVICE service, which opi-light replaces..."
        sudo systemctl disable --now "$SERVICE"
        sudo rm "/etc/systemd/system/$SERVICE.service"
    fi
done

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

# Run the light client as a systemd service: it restarts on failure and starts on boot.
# The service loads .env from this directory the same way this script does.
SERVICE_USER=$(id -un)
SERVICE_DIR=$(pwd)
OPI_INDEXER_BIN=$(command -v opi-indexer || true)
if [ -z "$OPI_INDEXER_BIN" ]; then
    echo "opi-indexer is not on PATH after cargo install. Add \$HOME/.cargo/bin to PATH and run this script again."
    exit 1
fi

echo "Installing systemd service opi-light..."

sudo tee /etc/systemd/system/opi-light.service > /dev/null <<EOF
[Unit]
Description=OPI BRC-20 light client with the BRC2.0 engine (opi-indexer brc20 light)
Wants=network-online.target
After=network-online.target postgresql.service

[Service]
User=$SERVICE_USER
WorkingDirectory=$SERVICE_DIR
ExecStart=/bin/bash -c 'set -a; . ./.env; set +a; exec $OPI_INDEXER_BIN brc20 light'
Restart=always
RestartSec=5
# The light client finishes its current block on SIGTERM
TimeoutStopSec=180
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable opi-light
sudo systemctl restart opi-light

echo "The OPI light client is running as the systemd service opi-light."
echo ""
echo "To check its status, use: systemctl status opi-light"
echo "To follow its logs, use: journalctl -u opi-light -f"
echo ""
echo "Setup complete!"
