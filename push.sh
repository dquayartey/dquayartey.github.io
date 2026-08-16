#!/bin/bash
set -e

cd "$(dirname "$0")"

if [[ -z $(git status --porcelain) ]]; then
  echo "Nothing to commit — working tree clean."
  exit 0
fi

git add -A
git commit -m "chore: auto-push $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main

echo "✅ Pushed to origin/main"
