#!/bin/bash

CONFIG_FILE="/home/crystal/.config/polybar/config.ini"
TARGET_MONITOR_FOR_POLYBAR="eDP" # Target monitor for all Polybar instances

# Terminate already running bar instances
echo "Terminating existing Polybar instances..."
pkill -u "$UID" -x polybar
# Give pkill a moment to act before the check loop
sleep 0.5 # Increased sleep slightly more

# Wait until the processes have been shut down
echo "Waiting for Polybar processes to shut down..."
WAIT_COUNT=0
while pgrep -u "$UID" -x polybar >/dev/null; do
  sleep 0.3
  WAIT_COUNT=$((WAIT_COUNT + 1))
  if [ "$WAIT_COUNT" -gt 20 ]; then # Wait for max ~6 seconds
    echo "Polybar processes did not shut down, attempting to force kill and continue..."
    pkill -KILL -u "$UID" -x polybar # Force kill
    sleep 0.5 # Give force kill a moment
    break
  fi
done
echo "Polybar processes shut down or timeout reached."

# Launch Polybar
echo "Launching Polybar..."

if type "xrandr"; then
  # Check if the target monitor eDP is connected
  if xrandr --query | grep -q "^$TARGET_MONITOR_FOR_POLYBAR connected"; then
    echo "Target monitor $TARGET_MONITOR_FOR_POLYBAR is connected."
    
    echo "Attempting to launch 'main' bar on MONITOR: $TARGET_MONITOR_FOR_POLYBAR"
    MONITOR="$TARGET_MONITOR_FOR_POLYBAR" polybar main -c "$CONFIG_FILE" &
    
    echo "Attempting to launch 'bottom' bar on MONITOR: $TARGET_MONITOR_FOR_POLYBAR"
    MONITOR="$TARGET_MONITOR_FOR_POLYBAR" polybar bottom -c "$CONFIG_FILE" &

  else
    echo "Error: Target monitor $TARGET_MONITOR_FOR_POLYBAR is not connected or not found by xrandr."
    echo "Please check your xrandr output. No Polybar instances will be launched."
    # Optionally, you could try to launch on a primary or first available monitor as a fallback here
    # For example, to launch on primary if eDP is not found:
    # PRIMARY_MONITOR=$(xrandr --query | grep " connected primary" | cut -d" " -f1)
    # if [ -n "$PRIMARY_MONITOR" ]; then
    #   echo "Fallback: Launching on primary monitor $PRIMARY_MONITOR"
    #   MONITOR="$PRIMARY_MONITOR" polybar main -c "$CONFIG_FILE" &
    #   MONITOR="$PRIMARY_MONITOR" polybar bottom -c "$CONFIG_FILE" &
    # else
    #   echo "No primary monitor found either."
    # fi
  fi
else
  echo "xrandr not found. Attempting to launch Polybar without specific monitor assignment (may not work as intended)."
  # This fallback might launch on whichever monitor Polybar picks by default
  MONITOR="" polybar main -c "$CONFIG_FILE" &
  MONITOR="" polybar bottom -c "$CONFIG_FILE" &
fi

echo "Polybar launch script finished."