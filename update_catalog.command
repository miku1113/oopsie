#!/bin/bash
# Oopsie Handcrafted Studio - Quick Catalog Updater & Publisher
# Double-click this file anytime you add or remove folders inside 'oppsie categories'!

cd -- "$(dirname "$0")"

clear
echo ""
echo "🌸 ====================================================== 🌸"
echo "        OOPSIE HANDCRAFTED STUDIO • CATALOG BUILDER"
echo "🌸 ====================================================== 🌸"
echo ""
echo "🔍 1. Scanning folders & rebuilding catalog..."
python3 generate_catalog.py

echo ""
echo "🚀 2. Publishing changes to GitHub..."
git add -A

# Only commit if there are changes
if git diff-index --quiet HEAD --; then
  echo "✨ Everything is already up to date!"
else
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
  git commit -m "Manual update: catalog refreshed ($TIMESTAMP)"
  echo "📡 Pushing to live site..."
  git push origin main
  echo ""
  echo "✨ Published to GitHub successfully!"
fi

echo ""
echo "🌍 Live Website: https://miku1113.github.io/oopsie/"
echo "🌸 All done! Have a lovely day."
echo ""
read -n 1 -s -r -p "Press any key to close this window..."
echo ""
