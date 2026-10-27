#!/bin/bash
# Refresh the GOWR dashboard data and publish it to GitHub Pages.
# Safe for any tool (Claude, Antigravity): it only touches this site repo.
# Usage: bash ~/gow-site/publish.sh ["what changed"]
set -euo pipefail
SITE=/run/media/arielk/WorkDrive/work/gow-site
GOW=/home/arielk/gow
MSG=${1:-"Update dashboard data"}

python3 -I "$GOW/dash_build.py"
python3 -I "$SITE/build_site.py"

cd "$SITE"
git add -A
if git diff --cached --quiet; then
    echo "Nothing changed; site already up to date."
    exit 0
fi
git commit -q -m "$MSG"
git push -q origin main
echo "Published: https://zswolt.github.io/gowr-dashboard/ (GitHub Pages updates within a minute or two)"
