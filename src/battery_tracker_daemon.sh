#!/bin/bash

STATE_DIR="$HOME/.local/state/battery_tracker"
STATE_FILE="$STATE_DIR/current_session.txt"
CSV_FILE="/home/suvojit/battery_history.csv"
POLL_INTERVAL=1 

BAT_PATH=$(find /sys/class/power_supply -name "BAT*" | head -n 1)
WIFI_IFACE=$(ls /sys/class/net | grep -E '^wl' | head -n 1)

if [ -z "$BAT_PATH" ]; then exit 1; fi

# Initialize the new CSV format
if [ ! -f "$CSV_FILE" ]; then
    echo "Session No,Phase,Date,Start (%),End (%),Runtime,Network" > "$CSV_FILE"
fi

# Initialize fresh state file
if [ ! -f "$STATE_FILE" ]; then
    echo "SESSION=1" > "$STATE_FILE"
    echo "MODE=Discharging" >> "$STATE_FILE"
    echo "START_CAP=$(cat "$BAT_PATH/capacity")" >> "$STATE_FILE"
    echo "END_CAP=$(cat "$BAT_PATH/capacity")" >> "$STATE_FILE"
    echo "START_DATE=$(date +%d/%m/%Y)" >> "$STATE_FILE"
    echo "RUNTIME=0" >> "$STATE_FILE"
    echo "NETWORK_TIME=0" >> "$STATE_FILE"
fi

format_time() {
    local T=$1
    printf "%02d:%02d:%02d" $((T / 3600)) $(( (T % 3600) / 60 )) $((T % 60))
}

while true; do
    source "$STATE_FILE"
    
    CURRENT_STATUS=$(cat "$BAT_PATH/status")
    CURRENT_CAP=$(cat "$BAT_PATH/capacity")
    
    # Simplify status into just two distinct phases
    if [ "$CURRENT_STATUS" = "Discharging" ]; then
        CURRENT_MODE="Discharging"
    else
        CURRENT_MODE="Charging"
    fi
    
    # If the phase changed (e.g., you plugged it in OR unplugged it)
    if [ "$MODE" != "$CURRENT_MODE" ]; then
        
        # 1. Instantly save the completed phase to the CSV
        if [ "$RUNTIME" -gt 0 ]; then
            F_RUNTIME=$(format_time "$RUNTIME")
            F_NETWORK=$(format_time "$NETWORK_TIME")
            echo "$SESSION,$MODE,$START_DATE,$START_CAP,$END_CAP,$F_RUNTIME,$F_NETWORK" >> "$CSV_FILE"
        fi
        
        # 2. If a new Discharging phase is starting, increment the Session Number
        if [ "$CURRENT_MODE" = "Discharging" ]; then
            SESSION=$((SESSION + 1))
        fi
        
        # 3. Reset the timers for the new phase
        MODE=$CURRENT_MODE
        START_CAP=$CURRENT_CAP
        START_DATE=$(date +%d/%m/%Y)
        RUNTIME=0
        NETWORK_TIME=0
    fi
    
    # Accumulate awake time for the current phase
    RUNTIME=$((RUNTIME + POLL_INTERVAL))
    END_CAP=$CURRENT_CAP
    
    # Track Wi-Fi during the current phase
    if [ -n "$WIFI_IFACE" ]; then
        WIFI_STATE=$(cat "/sys/class/net/$WIFI_IFACE/operstate" 2>/dev/null)
        if [ "$WIFI_STATE" = "up" ]; then
            NETWORK_TIME=$((NETWORK_TIME + POLL_INTERVAL))
        fi
    fi
    
    # Save current variables to disk
    echo "SESSION=$SESSION" > "$STATE_FILE"
    echo "MODE=$MODE" >> "$STATE_FILE"
    echo "START_CAP=$START_CAP" >> "$STATE_FILE"
    echo "END_CAP=$END_CAP" >> "$STATE_FILE"
    echo "START_DATE=$START_DATE" >> "$STATE_FILE"
    echo "RUNTIME=$RUNTIME" >> "$STATE_FILE"
    echo "NETWORK_TIME=$NETWORK_TIME" >> "$STATE_FILE"
    
    sleep $POLL_INTERVAL
done
