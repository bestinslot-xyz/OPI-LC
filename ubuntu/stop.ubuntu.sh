#!/bin/bash

# Stop the light client service run.ubuntu.sh installs, and keep it stopped across reboots
if [ -f "/etc/systemd/system/opi-light.service" ]; then
    echo "Stopping opi-light service..."
    sudo systemctl disable --now opi-light
fi
