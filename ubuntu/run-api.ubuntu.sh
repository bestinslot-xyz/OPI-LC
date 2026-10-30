#!/bin/bash
set -eu

# run.ubuntu.sh installs opi-indexer, which also serves the API
OPI_INDEXER_BIN=$(command -v opi-indexer || true)
if [ -z "$OPI_INDEXER_BIN" ]; then
    echo "opi-indexer is not on PATH. Run run.ubuntu.sh first, or add \$HOME/.cargo/bin to PATH."
    exit 1
fi

# Stop the JS brc20-api of the earlier setup: opi-indexer api replaces it on the same port
if command -v pm2 &> /dev/null
then
    PM2_PROCESSES=$(pm2 list | grep -c "brc20-api" || true)
    if [ "$PM2_PROCESSES" -gt 0 ]; then
        echo "Removing the brc20-api PM2 process, which opi-api replaces..."
        pm2 stop brc20-api
        pm2 delete brc20-api
        pm2 save
    fi
fi

# Run the API as a systemd service: it restarts on failure and starts on boot.
# The service loads .env from this directory.
SERVICE_USER=$(id -un)
SERVICE_DIR=$(pwd)

echo "Installing systemd service opi-api..."

sudo tee /etc/systemd/system/opi-api.service > /dev/null <<EOF
[Unit]
Description=OPI API (opi-indexer api)
Wants=network-online.target
After=network-online.target postgresql.service

[Service]
User=$SERVICE_USER
WorkingDirectory=$SERVICE_DIR
ExecStart=/bin/bash -c 'set -a; . ./.env; set +a; exec $OPI_INDEXER_BIN api'
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable opi-api
sudo systemctl restart opi-api

echo "The OPI API is running as the systemd service opi-api."
echo ""
echo "To check its status, use: systemctl status opi-api"
echo "To follow its logs, use: journalctl -u opi-api -f"
echo ""
echo "Setup complete!"
