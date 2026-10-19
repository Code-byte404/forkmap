#!/usr/bin/env bash
# Package the skill folder as dist/forkmap.zip for upload to the Claude app.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p dist
rm -f dist/forkmap.zip
zip -rq dist/forkmap.zip forkmap -x '*/__pycache__/*' -x '*/.DS_Store'
echo "Wrote dist/forkmap.zip"
