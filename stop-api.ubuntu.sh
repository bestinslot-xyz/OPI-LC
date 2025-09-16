if command -v pm2 &> /dev/null
then
    PM2_PROCESSES=$(pm2 list | grep -c "brc20-api" || true)
    if [ "$PM2_PROCESSES" -gt 0 ]; then
        echo "Stopping existing BRC20 API process..."
        pm2 stop brc20-api
        pm2 delete brc20-api
    fi
else
    echo "PM2 is not installed. No BRC20 API process to stop."
fi