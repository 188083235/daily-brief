#!/usr/bin/env bash
# Daily pipeline. Usage: ./run_daily.sh YYYY-MM-DD   (window = 30h ending DATE 10:00 KST)
set -euo pipefail
D=${1:-$(TZ=Asia/Seoul date +%F)}
cd "$(dirname "$0")/pipeline"
PY=../.venv/bin/python
# Second pass (editorial already written): don't re-collect, or cids/fids in the packs would change under the editorial.
if [ -f "../editorial/$D.py" ] && [ -f "../data/pack-$D.json" ] && [ "${FORCE_COLLECT:-0}" != 1 ]; then
  $PY build_issue.py "$D" && $PY render.py && echo "done: $D (build only)"; exit $?; fi
$PY feedback.py fetch || echo "feedback fetch failed (continuing)"   # owner feedback issues -> data/feedback/ (private)
$PY collect.py "$D" --hours 30        # feeds -> data/candidates-D.json (dedupe, cluster, score)
$PY select_items.py "$D"              # quotas + explore pool, resolve links, fetch article text -> data/pack-D.json
../tools/rsshub-local/start.sh || echo "local RSSHub unavailable"
$PY social.py --per-account 5 || echo "social collect failed (continuing)"   # own follows -> data/social/ (private)
$PY follow_pack.py "$D" --hours 30 || true   # -> data/follow-pack-D.json (private)
$PY fixed_topics.py "$D" --hours 72 --per-topic 10   # 固定关注: config issue (owner only) or config/fixed_topics.json -> data/fixed-pack-D.json
if [ ! -f "../editorial/$D.py" ]; then
  echo "Editorial step: write editorial/$D.py (ITEMS/DETAIL per cid + FIXED per topic, FOLLOW per follow-pack fid, grounded in pack/fixed-pack text only), then rerun."; exit 2; fi
$PY build_issue.py "$D"               # merge -> data/issue-D.json (asserts every item is grounded)
$PY render.py                         # -> index.html, archive/D.html, archive/index.html
echo "done: $D"
