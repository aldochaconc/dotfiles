#!/bin/sh
LOG_FILE="/tmp/lifecycle_manager.log"

echo "$(date): Force update triggered." >> "${LOG_FILE}"
rm -f "/home/crystal/.current_lifecycle_period" && \
systemctl --user start lifecycle_manager.service && \
echo "$(date): Force update actions completed." >> "${LOG_FILE}" || \
echo "$(date): Force update actions failed." >> "${LOG_FILE}" 