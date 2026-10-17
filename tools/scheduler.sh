#!/usr/bin/env bash
# No cron on the box: a background loop that runs run_update.sh at 00/06/12/18 KST.  Start: nohup tools/scheduler.sh >> /tmp/daily-brief-scheduler.log 2>&1 &
cd "$(dirname "$0")/.."
while true; do
  now=$(TZ=Asia/Seoul date +%s); h=$(TZ=Asia/Seoul date +%H); h=$((10#$h)); next=$(( (h/6+1)*6 ))
  mid=$(TZ=Asia/Seoul date -d "today 00:00" +%s); target=$(( mid + next*3600 ))
  # (old "today 00:00 +N hours" was parsed as a UTC offset -> negative sleep -> back-to-back runs)
  s=$(( target-now+60 )); [ "$s" -lt 60 ] && s=60; sleep "$s"
  echo "== $(TZ=Asia/Seoul date) run_update"; ./run_update.sh
done
