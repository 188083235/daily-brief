#!/usr/bin/env bash
# Start the self-hosted RSSHub (library mode) on 127.0.0.1:1200 if it is not already up.
# One-time setup on the box:  node>=22 at /home/box/opt/node22 ; cd /home/box/rsshub && npm i rsshub ; npx playwright install chromium-headless-shell
set -e
curl -s -m 3 -o /dev/null http://127.0.0.1:1200/ && exit 0
RH=${RSSHUB_DIR:-/home/box/rsshub}; cp "$(dirname "$0")/server.mjs" "$RH/server.mjs"
cd "$RH" && PATH=/home/box/opt/node22/bin:$PATH nohup node server.mjs >> /tmp/rsshub.log 2>&1 &
for i in $(seq 1 30); do sleep 1; curl -s -m 2 -o /dev/null http://127.0.0.1:1200/ && exit 0; done; echo "rsshub failed to start" >&2; exit 1
