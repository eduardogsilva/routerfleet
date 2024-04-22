#!/bin/bash
# This script is intended only for development purposes.
# It reads the cron file and executes the curl commands in it.
CRON_FILE="cron_tasks"

while true; do
    start_time=$(date +%s)

    # Read the cron file and extract curl commands
    grep -o 'curl[^>]*' $CRON_FILE | while read -r line; do
        echo "Executing: $line"
        eval "$line"
        echo ""
        sleep 5
    done

    elapsed_time=$(( $(date +%s) - start_time ))

    if [ $elapsed_time -lt 60 ]; then
        sleep_time=$(( 60 - elapsed_time ))
        echo "Waiting $sleep_time seconds to complete the cycle."
        sleep $sleep_time
    else
        echo "Cycle took more than 60 seconds. Resuming immediately."
    fi
done
