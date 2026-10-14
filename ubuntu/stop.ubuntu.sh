# Stop the systemd services run.ubuntu.sh installs, and keep them stopped across reboots
for SERVICE in brc20-index brc20-prog; do
    if [ -f "/etc/systemd/system/$SERVICE.service" ]; then
        echo "Stopping $SERVICE service..."
        sudo systemctl disable --now "$SERVICE"
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
