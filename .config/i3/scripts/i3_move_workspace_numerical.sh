#!/bin/bash

# Script to move to the next/previous workspace numerically in i3

get_current_workspace_num() {
  i3-msg -t get_workspaces | jq '.[] | select(.focused==true).num'
}

# Define min and max workspace numbers if you want to loop or cap
# Example: MIN_WORKSPACE=1
# Example: MAX_WORKSPACE=10

CURRENT_WS=$(get_current_workspace_num)

if [ -z "$CURRENT_WS" ]; then
  echo "Could not determine current workspace."
  exit 1
fi

TARGET_WS=""

case "$1" in
  next)
    TARGET_WS=$((CURRENT_WS + 1))
    # Optional: if [ "$TARGET_WS" -gt "$MAX_WORKSPACE" ]; then TARGET_WS=$MIN_WORKSPACE; fi
    ;;
  prev)
    TARGET_WS=$((CURRENT_WS - 1))
    # Optional: if [ "$TARGET_WS" -lt "$MIN_WORKSPACE" ]; then TARGET_WS=$MAX_WORKSPACE; fi
    ;;
  *)
    echo "Usage: $0 <next|prev>"
    exit 1
    ;;
esac

# Optional: Prevent going below workspace 1 if not looping
if [ "$TARGET_WS" -lt 1 ]; then
    # You could choose to do nothing, or go to workspace 1, or loop to MAX_WORKSPACE
    # For now, let's prevent going below 1 if MIN_WORKSPACE is not set for looping
    if [[ "$1" == "prev" && "$CURRENT_WS" -eq 1 ]]; then
        # echo "Already on workspace 1, not going further back."
        exit 0 # Or loop to MAX_WORKSPACE if defined
    fi
    TARGET_WS=1 # Default to 1 if calculated less than 1
fi


if [ -n "$TARGET_WS" ]; then
  i3-msg workspace number "$TARGET_WS"
fi 