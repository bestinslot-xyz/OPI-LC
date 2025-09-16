#!/bin/bash
set -eu

if command -v pm2 &> /dev/null
then
    echo "PM2 is already installed."
else
    echo "PM2 is not installed. Installing PM2..."
    sudo apt install -y npm nodejs
    sudo npm install -g pm2
fi

git clone https://github.com/bestinslot-xyz/OPI.git

cd OPI/modules/brc20_api
npm install

# Start using pm2 just run node api.js
if command -v pm2 &> /dev/null
then
    PM2_PROCESSES=$(pm2 list | grep -c "brc20-api" || true)
    if [ "$PM2_PROCESSES" -gt 0 ]; then
        echo "Stopping existing BRC20 API process..."
        pm2 stop brc20-api
        pm2 delete brc20-api
    fi
fi

pm2 start api.js --name brc20-api
pm2 save
pm2 startup
pm2 save
echo "BRC20 API is running under PM2 process manager."
echo "To manage the BRC20 API process, use the following commands:"
echo "  pm2 status               # Check the status of all PM2 processes"
echo "  pm2 restart brc20-api    # Restart the BRC20 API process"
echo "  pm2 stop brc20-api       # Stop the BRC20 API process"
echo "  pm2 logs brc20-api       # View logs for the BRC20 API process"
echo "  pm2 delete brc20-api     # Delete the BRC20 API process from PM2"
echo "Setup complete!"