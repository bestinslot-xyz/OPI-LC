#!/bin/bash

# Stop the API service run-api.ubuntu.sh installs, and keep it stopped across reboots
if [ -f "/etc/systemd/system/opi-api.service" ]; then
    echo "Stopping opi-api service..."
    sudo systemctl disable --now opi-api
else
    echo "The opi-api service is not installed. No API to stop."
fi
