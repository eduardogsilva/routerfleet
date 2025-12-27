#!/bin/bash
# This script is intended only for development purposes.
# It reads the cron file and executes the curl commands in it,
# rewriting routerfleet:8001 to localhost:8001.

CRON_FILE="cron_tasks"

while true; do
    start_time=$(date +%s)

    # Extract curl commands from cron file
    grep -o '/usr/bin/curl[^>]*' "$CRON_FILE" | while read -r line; do
        # Replace routerfleet:8001 with localhost:8001
        localhost_line=$(echo "$line" | sed 's|routerfleet:8001|localhost:8001|g')

        echo "Executing: $localhost_line"
        eval "$localhost_line"
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
