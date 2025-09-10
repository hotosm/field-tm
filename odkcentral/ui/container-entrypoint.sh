#!/bin/sh

set -e

# Copy frontend to attached volume
echo "Syncing files from /app --> /frontend."
rclone sync /app /frontend
echo "Updating permissions --> 777."
chmod 777 -R /frontend
echo "Sync done."

# Successful exit (stop container)
exit 0
