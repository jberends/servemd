#!/bin/bash
# Install cron job for automatic Docker container updates
# Runs hourly: pulls latest images and restarts if changed
set -e
CRON_CMD="0 * * * * root cd /opt/servemd && docker compose pull -q && docker compose up -d"
CRON_FILE="/etc/cron.d/servemd-update"
echo "$CRON_CMD" > "$CRON_FILE"
chmod 644 "$CRON_FILE"
echo "Installed: $CRON_FILE"
cat "$CRON_FILE"
