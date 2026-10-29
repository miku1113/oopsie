#!/bin/bash
# Oopsie Handcrafted Studio - Quick Catalog Updater
# Double-click this file anytime you add or remove folders inside 'oppsie categories'!

cd "$(dirname "$0")"

echo ""
echo "🌸 ====================================================== 🌸"
echo "        OOPSIE HANDCRAFTED STUDIO • CATALOG BUILDER"
echo "🌸 ====================================================== 🌸"
echo ""
echo "🔍 Scanning 'oppsie categories' folder..."
python3 generate_catalog.py
echo ""
echo "✨ Catalog updated successfully!"
echo "📁 All categories inside 'oppsie categories' have been synced."
echo "📄 Open 'index.html' in your browser to view."
echo ""
read -n 1 -s -r -p "Press any key to close this window..."
echo ""
