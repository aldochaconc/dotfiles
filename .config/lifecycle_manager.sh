#!/bin/sh

# Lifecycle Manager Script

# --- Configuration ---
DAY_START_HOUR=6 # 6 AM
NIGHT_START_HOUR=18 # 6 PM

WALLPAPER_DIR="/home/crystal/.config/wallpapers"
DAY_WALLPAPER="${WALLPAPER_DIR}/p5r_day.jpg"
NIGHT_WALLPAPER="${WALLPAPER_DIR}/p5r_night.jpg"

# Gammastep temperatures
TEMP_DAY=6500
TEMP_NIGHT=5800 # Adjust as needed

# State file
STATE_FILE="/home/crystal/.current_lifecycle_period"
LOG_FILE="/tmp/lifecycle_manager.log" # For cron job logging
MAX_LOG_LINES=1000 # Maximum lines to keep in the log

# --- Functions ---
cleanup_log_file() {
    if [ -f "${LOG_FILE}" ]; then
        CURRENT_LINES=$(wc -l < "${LOG_FILE}" | awk '{print $1}')
        if [ "${CURRENT_LINES}" -gt "${MAX_LOG_LINES}" ]; then
            # Log to a temporary variable first, as the log file is about to be overwritten
            local cleanup_msg="$(date): Log file exceeded ${MAX_LOG_LINES} lines. Truncating."
            
            tail -n "${MAX_LOG_LINES}" "${LOG_FILE}" > "${LOG_FILE}.tmp" && \
            mv "${LOG_FILE}.tmp" "${LOG_FILE}"
            
            # Now log the cleanup message to the newly truncated log
            echo "${cleanup_msg}" >> "${LOG_FILE}"
        fi
    fi
}

log_message() {
    echo "$(date): $1" >> "${LOG_FILE}"
}

# --- Main Logic ---

# Perform log cleanup at the start of script execution
cleanup_log_file

CURRENT_HOUR=$(date +%H)
CURRENT_PERIOD=""

if [ "${CURRENT_HOUR}" -ge "${DAY_START_HOUR}" ] && [ "${CURRENT_HOUR}" -lt "${NIGHT_START_HOUR}" ]; then
    CURRENT_PERIOD="day"
else
    CURRENT_PERIOD="night"
fi

LAST_PERIOD=""
if [ -f "${STATE_FILE}" ]; then
    LAST_PERIOD=$(cat "${STATE_FILE}")
fi

if [ "${CURRENT_PERIOD}" != "${LAST_PERIOD}" ]; then
    log_message "Period changed from '${LAST_PERIOD}' to '${CURRENT_PERIOD}'."

    TARGET_WALLPAPER=""
    TARGET_TEMP=""

    if [ "${CURRENT_PERIOD}" = "day" ]; then
        TARGET_WALLPAPER="${DAY_WALLPAPER}"
        TARGET_TEMP="${TEMP_DAY}"
        log_message "Setting DAY configurations."
    else # night
        TARGET_WALLPAPER="${NIGHT_WALLPAPER}"
        TARGET_TEMP="${TEMP_NIGHT}"
        log_message "Setting NIGHT configurations."
    fi

    # 1. Set Wallpaper with feh
        autorandr --change
    if [ -f "${TARGET_WALLPAPER}" ]; then
        feh --bg-scale "${TARGET_WALLPAPER}"
        log_message "Wallpaper set to ${TARGET_WALLPAPER}."

    else
        log_message "ERROR: Wallpaper ${TARGET_WALLPAPER} not found!"
    fi

    # 2. Set Screen Temperature with gammastep (one-shot)
    gammastep -P -O "${TARGET_TEMP}" > /dev/null 2>&1
    log_message "Gammastep temperature set to ${TARGET_TEMP}K."

    # 3. Set Terminal Color Scheme with pywal
    if [ -f "${TARGET_WALLPAPER}" ]; then
        wal -i "${TARGET_WALLPAPER}" -b '#050505' -n -q
        log_message "Pywal theme generated from ${TARGET_WALLPAPER} with forced black background."

        # Source wal's generated colors (needed for xrdb)
        if [ -f "$HOME/.cache/wal/colors.sh" ]; then
            . "$HOME/.cache/wal/colors.sh" # Execute in current shell to get vars
        else
            log_message "ERROR: ~/.cache/wal/colors.sh not found for xrdb!"
        fi
        
        xrdb -merge "/home/crystal/.Xresources"
        log_message "Merged .Xresources for pywal."
    else
        log_message "ERROR: Wallpaper ${TARGET_WALLPAPER} not found for pywal!"
    fi

    # 4. Update state file
    echo "${CURRENT_PERIOD}" > "${STATE_FILE}"
    log_message "State file updated to ${CURRENT_PERIOD}."

else
    # log_message "Period (${CURRENT_PERIOD}) has not changed. No action." # Optional: for debugging cron
    : # No change, do nothing silently
fi

exit 0 
