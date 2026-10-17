#!/usr/bin/env bash
# 6-hourly "latest updates": new items since the previous run, from news feeds + the user's own follows.
# Usage: ./run_update.sh [--no-push]
set -uo pipefail
cd "$(dirname "$0")"; ROOT=$PWD; PY=$ROOT/.venv/bin/python; D=$(TZ=Asia/Seoul date +%F)
tools/rsshub-local/start.sh || echo "local RSSHub unavailable; RSSHub-based follows will fall back or fail"
cd pipeline
$PY collect.py "$D" --hours 8 --end now --out ../data/update-news.json || echo "news collect failed"
[ -n "${SKIP_SOCIAL:-}" ] || $PY social.py --per-account 5 || echo "social collect failed"
$PY update.py || exit 1
cd "$ROOT"
$PY - <<'P'
import re,glob,os
# point the daily page's nav at the newest update page
latest=sorted(glob.glob('updates/20*.html'))[-1].split('/')[-1]
for f in ['index.html']+glob.glob('archive/20*.html'):
    s=open(f).read();pre='' if f=='index.html' else '../'
    s=re.sub(r'<a class="updl"[^>]*>[^<]*</a>','',s)
    s=s.replace('<span id="prog">',f'<a class="updl" href="{pre}updates/{latest}">🕒 最新更新</a><span id="prog">',1)
    open(f,'w').write(s)
P
if [ "${1:-}" != "--no-push" ]; then
  git add updates/ index.html archive/ && git commit -qm "update $(TZ=Asia/Seoul date +%F-%H)" && git push -q origin main && echo pushed
fi
