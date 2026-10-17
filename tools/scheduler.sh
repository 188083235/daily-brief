#!/usr/bin/env bash
# No cron on the box: a background loop that runs run_update.sh at 00/06/12/18 KST.  Start: nohup tools/scheduler.sh >> /tmp/daily-brief-scheduler.log 2>&1 &
# Polls the wall clock every 60s (a single long `sleep` drifts when the box is suspended, since sleep uses a monotonic clock).
cd "$(dirname "$0")/.."
last=""
while true; do
  h=$(TZ=Asia/Seoul date +%H); h=$((10#$h)); slot="$(TZ=Asia/Seoul date +%F)-$(( h/6*6 ))"
  if [ -z "$last" ]; then last="$slot"; fi   # don't fire for the slot that is current at start-up
  if [ "$slot" != "$last" ]; then
    last="$slot"; echo "== $(TZ=Asia/Seoul date) run_update"; ./run_update.sh
  fi
  sleep 60
done
