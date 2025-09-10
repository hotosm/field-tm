#!/bin/sh

set -e

# Copy frontend to attached volume, making it
# accessible to the Nginx container
echo "Syncing files from /app --> /frontend."
rclone sync /app /frontend
echo "Updating directory group --> nginx."
chown -R nginx:nginx /frontend
echo "Sync done."

# Successful exit (stop container)
exit 0
