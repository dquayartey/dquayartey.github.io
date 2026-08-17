#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "🔨 Building site locally to check for errors..."
python3 build/build.py

if [[ -z $(git status --porcelain -- src build) ]]; then
  echo "Nothing to commit — working tree clean."
  exit 0
fi

git add -A
git commit -m "chore: auto-push $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main

echo "✅ Pushed to origin/main"