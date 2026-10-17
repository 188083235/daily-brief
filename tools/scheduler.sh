#!/usr/bin/env bash
# No cron on the box: a background loop that runs run_update.sh at 00/06/12/18 KST.  Start: nohup tools/scheduler.sh >> /tmp/daily-brief-scheduler.log 2>&1 &
cd "$(dirname "$0")/.."
while true; do
  now=$(TZ=Asia/Seoul date +%s); h=$(TZ=Asia/Seoul date +%H); h=$((10#$h)); next=$(( (h/6+1)*6 ))
  target=$(TZ=Asia/Seoul date -d "today 00:00 +$next hours" +%s); sleep $(( target-now+60 ))
  echo "== $(TZ=Asia/Seoul date) run_update"; ./run_update.sh
done
