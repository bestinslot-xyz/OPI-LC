if command -v screen &> /dev/null
then
    SCREEN_SESSIONS=$(screen -ls | grep -c "brc20-prog\|brc20-index" || true)
    if [ "$SCREEN_SESSIONS" -gt 0 ]; then
        echo "Killing existing screen sessions..."
        screen -ls | grep -E "brc20-prog|brc20-index" | awk '{print $1}' | xargs -I {} screen -S {} -X quit
    fi
fi
