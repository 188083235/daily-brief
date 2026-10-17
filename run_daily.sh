#!/usr/bin/env bash
# Daily pipeline. Usage: ./run_daily.sh YYYY-MM-DD   (window = 30h ending DATE 10:00 KST)
set -euo pipefail
D=${1:-$(TZ=Asia/Seoul date +%F)}
cd "$(dirname "$0")/pipeline"
PY=../.venv/bin/python
$PY collect.py "$D" --hours 30        # feeds -> data/candidates-D.json (dedupe, cluster, score)
$PY select_items.py "$D"              # quotas + explore pool, resolve links, fetch article text -> data/pack-D.json
if [ ! -f "../editorial/$D.py" ]; then
  echo "Editorial step: write editorial/$D.py (Chinese title/summary/why per cid, grounded in pack text only), then rerun."; exit 2; fi
$PY build_issue.py "$D"               # merge -> data/issue-D.json (asserts every item is grounded)
$PY render.py                         # -> index.html, archive/D.html, archive/index.html
echo "done: $D"
