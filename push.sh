#!/bin/bash

DEVICE_ID="faithlessly-ultimate-tuneful-bedbug-682"

APPS=(
    "next_game"
)

while true; do
    for APP in "${APPS[@]}"; do
        echo "Updating $APP..."

        if pixlet render "${APP}.star" -o "${APP}.webp"; then
            if [ -s "${APP}.webp" ]; then
                sleep 1
                pixlet push "$DEVICE_ID" "${APP}.webp" --installation-id "${APP//_/}"
            else
                echo "Render produced an empty image; retrying..."
                sleep 2
            fi
        else
            echo "Failed to render $APP; retrying..."
            sleep 2
        fi
    done
done