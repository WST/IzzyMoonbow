#!/bin/bash

# Function to start the bot
start_bot() {
    echo "Starting Telegram bot..."
    while true; do
        python izzy.py
        echo "Bot crashed. Restarting in 5 seconds..."
        sleep 5
    done
}

# Function to start the API
start_api() {
    echo "Starting API..."
    while true; do
        python api.py
        echo "API crashed. Restarting in 5 seconds..."
        sleep 5
    done
}

# Check environment variables and start components accordingly
if [ -z "$IZZY_NO_BOT" ] && [ -z "$IZZY_NO_API" ]; then
    echo "Starting both bot and API..."
    start_bot &
    start_api
elif [ -n "$IZZY_NO_API" ]; then
    start_bot
elif [ -n "$IZZY_NO_BOT" ]; then
    start_api
else
    echo "Error: Invalid configuration. Please set IZZY_NO_BOT or IZZY_NO_API correctly."
    exit 1
fi