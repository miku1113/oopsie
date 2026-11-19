#!/bin/bash
# Oopsie Handcrafted Studio - Rebuild & publish the catalog
# Double-click to rebuild index.html from catalog.json and push catalog changes to GitHub.
# (Editing is done in the admin page: double-click start_server.command.)

cd -- "$(dirname "$0")"

clear
echo ""
echo "🌸 ====================================================== 🌸"
echo "        OOPSIE HANDCRAFTED STUDIO • CATALOG PUBLISHER"
echo "🌸 ====================================================== 🌸"
echo ""
echo "🔍 1. Rebuilding index.html from catalog.json..."
python3 generate_catalog.py || { read -n 1 -s -r -p "Fix the error above, then press any key to close..."; exit 1; }

echo ""
echo "🚀 2. Publishing changes to GitHub..."
git add -A -- catalog.json index.html images

if git diff --cached --quiet -- catalog.json index.html images; then
  echo "✨ Everything is already up to date!"
else
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
  git commit -m "Catalog update ($TIMESTAMP)" -- catalog.json index.html images
  echo "📡 Pushing to live site..."
  git push origin HEAD
  echo ""
  echo "✨ Published to GitHub successfully!"
fi

echo ""
echo "🌍 Live Website: https://miku1113.github.io/oopsie/"
echo "🌸 All done! Have a lovely day."
echo ""
read -n 1 -s -r -p "Press any key to close this window..."
echo ""
