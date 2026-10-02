#!/bin/sh
# Copy the newest verified backup off this VM. Does nothing until /etc/beyond-heroes/offsite.env exists, so a fresh install
# never fails here; the on-VM backups (every 15 minutes, daily tiers kept 30 days) still run.
#
# /etc/beyond-heroes/offsite.env (mode 0600, owned by beyond-heroes) chooses ONE destination:
#   OFFSITE_RCLONE=remote:bucket/beyond-heroes     # needs rclone configured for the beyond-heroes user
#   OFFSITE_RSYNC=user@backup-host:/srv/beyond-heroes/   # needs a passwordless key for the beyond-heroes user
# The destination and its credentials are the owner's choice; this repository does not create any.
set -eu
ENV=/etc/beyond-heroes/offsite.env
[ -r "$ENV" ] || { echo "No off-VM backup destination configured ($ENV); skipping."; exit 0; }
# shellcheck disable=SC1090
. "$ENV"
DATA=/var/lib/beyond-heroes/backups
NEWEST=$(ls -1t "$DATA"/*.sqlite3 2>/dev/null | head -n 1 || true)
[ -n "$NEWEST" ] || { echo "No backup found in $DATA"; exit 1; }
# only a backup that verifies is copied
/opt/beyond-heroes/current/.venv/bin/python -m server.maintenance verify "$NEWEST" >/dev/null
if [ -n "${OFFSITE_RCLONE:-}" ]; then
    rclone copyto "$NEWEST" "$OFFSITE_RCLONE/$(basename "$NEWEST")"
elif [ -n "${OFFSITE_RSYNC:-}" ]; then
    rsync -a "$NEWEST" "$OFFSITE_RSYNC"
else
    echo "offsite.env sets neither OFFSITE_RCLONE nor OFFSITE_RSYNC"; exit 1
fi
echo "Copied $(basename "$NEWEST") off the VM."
