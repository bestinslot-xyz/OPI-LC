sudo apt install -y npm nodejs
sudo npm install -g pm2

git clone https://github.com/bestinslot-xyz/OPI.git

cd OPI/modules/brc20_api
npm install

pm2 start npm --name "brc20-api" -- start
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