#!/bin/bash
# Oopsie Handcrafted Studio - Catalog server + admin
# Double-click to open the admin page, where you add, edit, move and delete
# categories, products and photos. Phones on the same Wi-Fi can view the catalog too.

cd "$(dirname "$0")"

echo ""
echo "🌸 ====================================================== 🌸"
echo "     OOPSIE HANDCRAFTED STUDIO • CATALOG SERVER & ADMIN"
echo "🌸 ====================================================== 🌸"
echo ""
python3 serve.py
