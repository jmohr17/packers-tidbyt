#!/bin/bash

DEVICE_ID="forthrightly-blossoming-profound-basilisk-e6f"

APPS=(
    "next_game"
    #"future_app1"
    #"future_app2"
    #"future_app3"
)

while true; do
    for APP in "${APPS[@]}"; do
        echo "Updating $APP..."

        if pixlet render "${APP}.star" -o "${APP}.webp"; then
            pixlet push "$DEVICE_ID" "${APP}.webp"
        else
            echo "Failed to render $APP"
        fi

        sleep 5
    done
done