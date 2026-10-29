#!/usr/bin/env python3
"""
Generate Oopsie Product Catalog - Cute & Simple Auto-Updating Edition
- Background: Solid #716c4a with Cute Handcrafted Floating Product SVGs
- Category View: Clean 2-column table/grid showing ONLY category name & item count (NO category cover photos)
- Dynamic Auto-Category: Adding ANY new folder automatically creates a new category with its images!
- Category Tap: Opens that category to display all its products in 2 columns
- Fullscreen Lightbox for product photos
- Pure Flat solid colors, no gradients, no shadows
- Cute typography: Google Fonts 'Fredoka' & 'Nunito'
"""

import os
import re
import json
import shutil
import urllib.parse

# Pre-configured categories with custom colors sampled from logo & complementary artisan tones
CATEGORY_CONFIG = {
    'Calender': {
        'name': 'Calendars',
        'color': '#c96232',
        'text_color': '#FFFFFF'
    },
    'Car charms & wall hanging': {
        'name': 'Car Charms & Decor',
        'color': '#7d9d8b',
        'text_color': '#FFFFFF'
    },
    'Crochet keychains & toys': {
        'name': 'Crochet Plushies & Toys',
        'color': '#c85a75',
        'text_color': '#FFFFFF'
    },
    'Cross stitch cards': {
        'name': 'Cross Stitch Cards',
        'color': '#7d7db8',
        'text_color': '#FFFFFF'
    },
    'Plant charms': {
        'name': 'Plant Charms',
        'color': '#8a9c5c',
        'text_color': '#FFFFFF'
    },
    'Pouches,wallets & tablet sleeves': {
        'name': 'Pouches & Sleeves',
        'color': '#a8684a',
        'text_color': '#FFFFFF'
    },
    'Specs holder': {
        'name': 'Spectacle Holders',
        'color': '#98aa68',
        'text_color': '#FFFFFF'
    },
    'Stickers card': {
        'name': 'Sticker Cards',
        'color': '#8a5a70',
        'text_color': '#FFFFFF'
    },
    'beaded flowers': {
        'name': 'Beaded Flowers',
        'color': '#d9827c',
        'text_color': '#FFFFFF'
    },
    'book marks': {
        'name': 'Artisan Bookmarks',
        'color': '#5078c8',
        'text_color': '#FFFFFF'
    },
    'candals': {
        'name': 'Sculpted Candles',
        'color': '#d9b860',
        'text_color': '#1E201B'
    },
    'ceramic pics': {
        'name': 'Ceramic Pieces',
        'color': '#4a7c7d',
        'text_color': '#FFFFFF'
    },
    'charms': {
        'name': 'Dainty Charms',
        'color': '#d88f75',
        'text_color': '#FFFFFF'
    },
    'dairy': {
        'name': 'Handbound Diaries',
        'color': '#8e85a8',
        'text_color': '#FFFFFF'
    },
    'fabric charms': {
        'name': 'Fabric Charms',
        'color': '#a83e3e',
        'text_color': '#FFFFFF'
    },
    'fridge magnet': {
        'name': 'Fridge Magnets',
        'color': '#6d8c7c',
        'text_color': '#FFFFFF'
    },
    'greeting card': {
        'name': 'Greeting Cards',
        'color': '#782828',
        'text_color': '#FFFFFF'
    },
    'jewelery': {
        'name': 'Handmade Jewellery',
        'color': '#5c779e',
        'text_color': '#FFFFFF'
    },
    'post cards': {
        'name': 'Art Postcards',
        'color': '#4d6888',
        'text_color': '#FFFFFF'
    },
    'small frams': {
        'name': 'Miniature Frames',
        'color': '#ba5828',
        'text_color': '#FFFFFF'
    },
    'Selected felt & fabric charms for keychains,bag,car,wall hanging': {
        'name': 'Felt & Fabric Charms',
        'color': '#8ea696',
        'text_color': '#FFFFFF'
    },
    'stickers': {
        'name': 'Die-Cut Stickers',
        'color': '#cca94e',
        'text_color': '#1E201B'
    }
}

# Rotating muted artisan colors (sampled from logo & studio palette) for newly added folders
SOLID_PALETTE = [
    '#d9827c',  # Soft terracotta pink (logo)
    '#c96232',  # Warm burnt terracotta (logo)
    '#7d9d8b',  # Dusty sage green (logo)
    '#c85a75',  # Muted berry rose (logo)
    '#5078c8',  # Soft artisan denim blue (logo)
    '#d9b860',  # Warm soft butter ochre (logo)
    '#8a9c5c',  # Soft matcha pear olive (logo)
    '#7d7db8',  # Soft dusty periwinkle (logo)
    '#a8684a',  # Warm cinnamon clay
    '#4a7c7d',  # Dusty sea-glass teal
    '#8a5a70',  # Muted plum mauve
    '#d88f75',  # Soft dusty apricot peach
    '#a83e3e',  # Artisan brick red (logo)
    '#6d8c7c',  # Dusty eucalyptus (logo)
    '#5c779e',  # Dusty cornflower slate (logo)
    '#782828',  # Warm deep burgundy (logo)
    '#4d6888',  # Dusty ocean blue
    '#8e85a8',  # Soft lavender clay
    '#ba5828',  # Warm burnt sienna
    '#cca94e',  # Muted warm mustard
    '#98aa68',  # Soft avocado green
]

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def guess_icon_for_folder(folder_name, idx):
    """Smart keyword matcher for newly added folders"""
    lower = folder_name.lower()
    
    rules = [
        (['hair', 'clip', 'scrunch', 'bow', 'ribbon'], '🎀'),
        (['crochet', 'wool', 'knit', 'amigurumi', 'plush', 'toy', 'doll', 'bear', 'yarn'], '🧸'),
        (['clay', 'pin', 'badge', 'brooch', 'paint', 'art', 'palette'], '🎨'),
        (['keychain', 'key', 'ring'], '🔑'),
        (['flower', 'floral', 'bloom', 'rose', 'daisy', 'petal', 'tulip', 'bouquet'], '🌸'),
        (['candle', 'wax', 'scent', 'aroma'], '🕯️'),
        (['plant', 'succulent', 'cactus', 'botanical', 'leaf', 'pot', 'garden'], '🪴'),
        (['phone', 'strap', 'mobile', 'case', 'cover'], '📱'),
        (['bead', 'necklace', 'bracelet', 'bangle', 'anklet'], '📿'),
        (['jewel', 'ring', 'earring', 'gem', 'silver', 'gold', 'pearl'], '💍'),
        (['pouch', 'wallet', 'purse', 'bag', 'sleeve', 'tote'], '👛'),
        (['charm', 'pendant', 'locket', 'heart'], '💖'),
        (['card', 'post', 'letter', 'envelope'], '💌'),
        (['sticker', 'decal', 'label'], '⭐️'),
        (['book', 'mark', 'reading', 'novel'], '🔖'),
        (['ceramic', 'pot', 'mug', 'cup', 'dish', 'plate', 'kitchen', 'crockery'], '🏺'),
        (['diary', 'journal', 'notebook', 'planner', 'stationery', 'pad'], '📔'),
        (['magnet', 'fridge'], '🧲'),
        (['frame', 'photo', 'miniature', 'portrait'], '🖼️'),
        (['calendar', 'calender', 'date', 'schedule'], '🗓️'),
        (['spec', 'glass', 'sunglass'], '👓'),
        (['embroidery', 'sewing', 'stitch', 'needle', 'thread'], '🧵'),
        (['food', 'bakery', 'cookie', 'cake', 'sweet', 'candy'], '🧁'),
        (['soap', 'bath', 'scrub'], '🧼'),
        (['gift', 'box', 'hamper'], '🎁'),
        (['bottle', 'flask', 'tumbler', 'sipper'], '🍶'),
    ]
    
    for keywords, icon in rules:
        if any(k in lower for k in keywords):
            return icon
            
    fallback_icons = ['🌸', '🎀', '🧸', '💖', '⭐️', '🎨', '💌', '🪴', '👛', '🌼', '🍓']
    return fallback_icons[idx % len(fallback_icons)]

def format_folder_name(folder_name):
    """Turns folder_name like 'clay_pins' or 'hair-clips' into 'Clay Pins' or 'Hair Clips'"""
    cleaned = folder_name.replace('_', ' ').replace('-', ' ').replace(',', ', ').strip()
    words = [word.capitalize() for word in cleaned.split() if word]
    return ' '.join(words)

def organize_root_categories(base_dir='.'):
    """
    If the user creates a new category folder directly inside the project root
    (e.g., from Google Drive root or Finder), this automatically moves it
    into 'oppsie categories/' so all categories remain centralized and unified.
    """
    cat_dir, _ = get_categories_dir(base_dir)
    if not os.path.exists(cat_dir) or os.path.abspath(cat_dir) == os.path.abspath(base_dir):
        return

    ignored = {
        'oppsie categories', 'oopsie categories', 'categories',
        '.git', '.github', '.tmp.driveupload', '.tmp.drivedownload',
        '__pycache__', 'scratch', 'node_modules', '.gemini', '.vscode', '.idea'
    }
    image_exts = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.heic', '.avif')

    try:
        entries = os.listdir(base_dir)
    except OSError:
        return

    for entry in entries:
        if entry.startswith('.') or entry in ignored:
            continue
        entry_path = os.path.join(base_dir, entry)
        if not os.path.isdir(entry_path):
            continue

        # Check if entry is a directory containing images
        has_images = False
        try:
            for root, dirs, files in os.walk(entry_path):
                if any(f.lower().endswith(image_exts) for f in files if not f.startswith('.')):
                    has_images = True
                    break
        except Exception:
            pass

        if has_images:
            dest_path = os.path.join(cat_dir, entry)
            print(f"📦 [Auto-Organize] Detected category folder '{entry}' in root. Moving into '{os.path.basename(cat_dir)}/'...")
            try:
                if not os.path.exists(dest_path):
                    shutil.move(entry_path, dest_path)
                else:
                    for item in os.listdir(entry_path):
                        src_item = os.path.join(entry_path, item)
                        dst_item = os.path.join(dest_path, item)
                        if not os.path.exists(dst_item):
                            shutil.move(src_item, dst_item)
                    try:
                        os.rmdir(entry_path)
                    except Exception:
                        pass
            except Exception as e:
                print(f"⚠️ [Auto-Organize] Notice: Could not move {entry}: {e}")

def get_categories_dir(base_dir='.'):
    """
    Finds the main categories directory:
    Prefers 'oppsie categories' or 'oopsie categories' or 'categories'.
    If not found as a subfolder, uses base_dir itself.
    Returns (directory path to scan, prefix folder name for URL src)
    """
    candidates = ['oppsie categories', 'oopsie categories', 'categories']
    for c in candidates:
        target = os.path.join(base_dir, c)
        if os.path.isdir(target):
            return target, c
    return base_dir, ''

def scan_catalog_data(base_dir='.'):
    # Automatically organize any newly created root folders into oppsie categories
    try:
        organize_root_categories(base_dir)
    except Exception:
        pass

    cat_dir, prefix = get_categories_dir(base_dir)
    categories = []
    ignored = {
        'oppsie categories', 'oopsie categories', 'categories',
        '.git', '.vscode', '.idea', '__pycache__', 'scratch', 'node_modules', '.gemini'
    }
    entries = sorted(os.listdir(cat_dir), key=natural_sort_key)

    total_products = 0
    seen_slugs = set()

    for idx, entry in enumerate(entries):
        if entry.startswith('.') or entry in ignored:
            continue
        entry_path = os.path.join(cat_dir, entry)
        if not os.path.isdir(entry_path):
            continue

        images = [
            f for f in os.listdir(entry_path)
            if not f.startswith('.') and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.heic', '.avif'))
        ]
        images.sort(key=natural_sort_key)

        if not images:
            continue

        # Check if preconfigured or dynamically generate for new folder
        conf = CATEGORY_CONFIG.get(entry)
        if conf:
            name = conf['name']
            pill_text = f"{len(images)} Items"
            color = conf['color']
            text_color = conf['text_color']
        else:
            name = format_folder_name(entry)
            pill_text = f"{len(images)} Items"
            color = SOLID_PALETTE[idx % len(SOLID_PALETTE)]
            text_color = '#1E201B' if color in ('#d9b860', '#cca94e') else '#FFFFFF'

        base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', entry).strip('-').lower() or f"cat-{idx+1}"
        cat_slug = base_slug
        slug_counter = 1
        while cat_slug in seen_slugs:
            slug_counter += 1
            cat_slug = f"{base_slug}-{slug_counter}"
        seen_slugs.add(cat_slug)

        items = []
        encoded_prefix = urllib.parse.quote(prefix) if prefix else ''
        encoded_folder = urllib.parse.quote(entry)

        for item_idx, filename in enumerate(images, 1):
            encoded_file = urllib.parse.quote(filename)
            if encoded_prefix:
                encoded_src = f"{encoded_prefix}/{encoded_folder}/{encoded_file}"
            else:
                encoded_src = f"{encoded_folder}/{encoded_file}"

            items.append({
                'id': f"{cat_slug}_{item_idx}",
                'index': item_idx,
                'filename': filename,
                'src': encoded_src,
                'title': f"{name} #{item_idx}"
            })

        total_products += len(items)
        categories.append({
            'slug': cat_slug,
            'folder': entry,
            'name': name,
            'pill_text': pill_text,
            'color': color,
            'text_color': text_color,
            'count': len(items),
            'items': items
        })

    return categories, total_products

def generate_catalog_html(categories, total_products, output_path='index.html'):
    categories_json = json.dumps(categories, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
  <meta name="theme-color" content="#716c4a">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <title>Oopsie • Cute Handcrafted Catalog</title>
  <link rel="icon" type="image/png" href="logo.png">
  <link rel="apple-touch-icon" href="logo.png">
  
  <!-- Playful Rounded Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@600;700;800;900&display=swap" rel="stylesheet">
  
  <style>
    :root {{
      --bg-olive: #716c4a;
      --bg-olive-header: #5f5a3b;
      --card-white: #FFFFFF;
      --text-dark: #1E201B;
      --text-muted: #5E6258;
      --radius-sm: 10px;
      --radius-md: 14px;
      --radius-lg: 18px;
    }}

    /* Global Flat Reset: NO shadows, NO gradients */
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
      box-shadow: none !important;
      text-shadow: none !important;
    }}

    body {{
      font-family: 'Fredoka', 'Nunito', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg-olive);
      color: #FFFFFF;
      min-height: 100vh;
      line-height: 1.35;
      padding-bottom: calc(45px + env(safe-area-inset-bottom));
      overflow-x: hidden;
      letter-spacing: 0.01em;
      position: relative;
    }}

    /* ========================================================
       CUTE FLOATING BACKGROUND SVGS (Keychains, Yarn, Candles, etc.)
       ======================================================== */
    .bg-floating-container {{
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 1;
      overflow: hidden;
    }}

    .float-svg {{
      position: absolute;
      pointer-events: none;
      user-select: none;
      opacity: 0.42;
    }}

    /* Specific Positions & Custom Floating Animations for 12 Authentic Craft SVGs */
    .pos-avocado        {{ top: 5%;  left: 3%;   width: 52px; height: 52px; animation: floatAnim1 7.5s ease-in-out infinite alternate; }}
    .pos-ceramic        {{ top: 18%; right: 4%;  width: 56px; height: 56px; animation: floatAnim2 8.5s ease-in-out infinite alternate; }}
    .pos-beaded-pot     {{ top: 32%; left: 3%;   width: 50px; height: 50px; animation: floatAnim3 9s ease-in-out infinite alternate; }}
    .pos-bubble-candle  {{ top: 46%; right: 4%;  width: 44px; height: 44px; animation: floatAnim1 8s ease-in-out infinite alternate; }}
    .pos-sleepy-heart   {{ top: 60%; left: 3%;   width: 48px; height: 48px; animation: floatRotate 9.5s ease-in-out infinite alternate; }}
    .pos-sleepy-moon    {{ top: 74%; right: 4%;  width: 50px; height: 50px; animation: floatAnim2 7.8s ease-in-out infinite alternate; }}
    .pos-crochet-berry  {{ top: 88%; left: 4%;   width: 48px; height: 48px; animation: floatAnim3 8.2s ease-in-out infinite alternate; }}
    .pos-clay-frame     {{ top: 11%; right: 26%; width: 48px; height: 48px; animation: floatAnim1 7.2s ease-in-out infinite alternate; }}
    .pos-cross-stitch-cam {{ top: 25%; left: 16%; width: 50px; height: 50px; animation: floatAnim2 6.8s ease-in-out infinite alternate; }}
    .pos-pencil-bookmark {{ top: 41%; right: 18%; width: 44px; height: 44px; animation: floatRotate 8s ease-in-out infinite alternate; }}
    .pos-suncatcher     {{ top: 64%; right: 22%; width: 48px; height: 48px; animation: floatAnim3 7.8s ease-in-out infinite alternate; }}
    .pos-denim-pouch    {{ top: 81%; left: 20%;  width: 52px; height: 52px; animation: floatAnim1 8.5s ease-in-out infinite alternate; }}

    @keyframes floatAnim1 {{
      0% {{ transform: translateY(0px) rotate(0deg); }}
      100% {{ transform: translateY(-16px) rotate(8deg); }}
    }}

    @keyframes floatAnim2 {{
      0% {{ transform: translateY(0px) rotate(0deg); }}
      100% {{ transform: translateY(14px) rotate(-8deg); }}
    }}

    @keyframes floatAnim3 {{
      0% {{ transform: translateX(0px) translateY(0px); }}
      100% {{ transform: translateX(10px) translateY(-12px); }}
    }}

    @keyframes floatRotate {{
      0% {{ transform: rotate(0deg) translateY(0px); }}
      100% {{ transform: rotate(18deg) translateY(-14px); }}
    }}

    /* ========================================================
       TOP STICKY HEADER
       ======================================================== */
    header {{
      position: sticky;
      top: 0;
      z-index: 100;
      background-color: var(--bg-olive-header);
      border-bottom: 2px solid rgba(255, 255, 255, 0.25);
      padding: calc(8px + env(safe-area-inset-top)) 16px 8px 16px;
    }}

    .header-inner {{
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}

    .brand-wrap {{
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
    }}

    .logo-header-img {{
      height: 48px;
      max-width: 140px;
      object-fit: contain;
      transition: transform 0.15s ease;
    }}

    .brand-wrap:active .logo-header-img {{
      transform: scale(0.95);
    }}

    .header-stat-pill {{
      display: flex;
      align-items: center;
      gap: 5px;
      background-color: #524e33;
      border: 1.5px solid rgba(255, 255, 255, 0.35);
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 0.78rem;
      font-weight: 600;
      color: #FFF;
      font-family: 'Nunito', sans-serif;
    }}

    .btn-search-toggle {{
      background-color: #524e33;
      border: 1.5px solid rgba(255, 255, 255, 0.45);
      color: #FFFFFF;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: transform 0.15s ease, background-color 0.15s ease, border-color 0.15s ease;
      padding: 0;
    }}

    .btn-search-toggle:active {{
      transform: scale(0.92);
    }}

    .btn-search-toggle.active {{
      background-color: #FFFFFF;
      color: #524e33;
      border-color: #FFFFFF;
    }}

    .search-icon-svg {{
      width: 19px;
      height: 19px;
      display: block;
    }}

    /* Collapsible Search Input */
    .search-box-wrap {{
      max-width: 1200px;
      margin: 8px auto 0 auto;
      display: none;
    }}

    .search-box-wrap.active {{
      display: block;
    }}

    .search-input-inner {{
      position: relative;
      display: flex;
      align-items: center;
      width: 100%;
    }}

    .search-input-icon {{
      position: absolute;
      left: 14px;
      pointer-events: none;
      color: #716c4a;
    }}

    .search-input-field {{
      width: 100%;
      height: 44px;
      padding: 0 40px 0 42px;
      border-radius: 25px;
      border: 2px solid #FFFFFF;
      background-color: #FFFFFF;
      color: var(--text-dark);
      font-size: 0.95rem;
      outline: none;
      font-family: 'Fredoka', 'Nunito', sans-serif;
      font-weight: 500;
    }}

    .search-clear-btn {{
      position: absolute;
      right: 12px;
      background: #EDECE6;
      border: none;
      color: #524e33;
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
      display: none;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      line-height: 24px;
      text-align: center;
    }}

    /* ========================================================
       MAIN CONTENT CONTAINER
       ======================================================== */
    main {{
      position: relative;
      z-index: 10;
      max-width: 1200px;
      margin: 16px auto;
      padding: 0 16px;
    }}

    /* Hero / Logo Showcase on Home */
    .catalog-hero {{
      text-align: center;
      margin: 4px 0 20px 0;
      padding: 4px 6px;
    }}

    .hero-big-logo {{
      width: 190px;
      max-width: 62%;
      height: auto;
      object-fit: contain;
      margin-bottom: 6px;
    }}

    .catalog-hero-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background-color: #5c573a;
      border: 1.5px solid rgba(255, 255, 255, 0.4);
      padding: 4px 14px;
      border-radius: 20px;
      font-size: 0.78rem;
      font-weight: 700;
      color: #FFF;
      margin-bottom: 6px;
    }}

    .catalog-hero h2 {{
      font-family: 'Fredoka', sans-serif;
      font-size: 1.5rem;
      font-weight: 700;
      color: #FFFFFF;
      letter-spacing: 0.01em;
    }}

    .catalog-hero p {{
      font-size: 0.86rem;
      color: #E2DFD2;
      margin-top: 3px;
      font-family: 'Nunito', sans-serif;
    }}

    /* ========================================================
       RESPONSIVE CATEGORIES GRID:
       - Mobile (< 640px): 2 columns
       - Tablet (640px - 949px): 3 columns
       - Laptop & Desktop (≥ 950px): 4 columns
       ======================================================== */
    .two-col-cat-table {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      width: 100%;
    }}

    @media (min-width: 640px) and (max-width: 949px) {{
      .two-col-cat-table {{
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
      }}
    }}

    @media (min-width: 950px) {{
      .two-col-cat-table {{
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
      }}
    }}

    /* Clean, Simple Category Tile: NO Icons, NO See-Product Buttons */
    .cat-tile {{
      background-color: var(--cat-color);
      color: var(--cat-text-color, #FFFFFF);
      border-radius: var(--radius-md);
      border: 2px solid rgba(255, 255, 255, 0.45);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 18px 16px;
      min-height: 105px;
      transition: transform 0.15s ease, border-color 0.15s ease;
      user-select: none;
      text-align: left;
    }}

    .cat-tile:active {{
      transform: scale(0.97);
    }}

    @media (hover: hover) {{
      .cat-tile:hover {{
        transform: translateY(-3px);
        border-color: rgba(255, 255, 255, 0.95);
      }}
    }}

    .cat-tile-name {{
      font-family: 'Fredoka', sans-serif;
      font-size: 1.12rem;
      font-weight: 600;
      line-height: 1.25;
      letter-spacing: 0.01em;
      word-break: break-word;
    }}

    .cat-tile-count {{
      font-family: 'Nunito', sans-serif;
      font-size: 0.82rem;
      font-weight: 800;
      opacity: 0.92;
      margin-top: 10px;
      letter-spacing: 0.02em;
    }}

    /* ========================================================
       VIEW 2: PRODUCTS INSIDE CATEGORY (RESPONSIVE COLUMNS)
       ======================================================== */
    .view-products-wrap {{
      display: none;
    }}

    /* Solid Category Hero Banner */
    .category-hero-solid {{
      border-radius: var(--radius-lg);
      padding: 16px 20px;
      margin-bottom: 16px;
      background-color: var(--current-color, #c96232);
      color: #FFFFFF;
      display: flex;
      flex-direction: column;
      gap: 10px;
      border: 2.5px solid rgba(255, 255, 255, 0.5);
    }}

    .hero-top-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }}

    .btn-back-solid {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      border-radius: 20px;
      background-color: #FFFFFF;
      color: #1A1A1A;
      font-size: 0.86rem;
      font-weight: 700;
      border: none;
      cursor: pointer;
      font-family: 'Fredoka', sans-serif;
      transition: transform 0.15s ease;
    }}

    .btn-back-solid:active {{
      transform: scale(0.95);
    }}

    .hero-count-solid {{
      background-color: rgba(0, 0, 0, 0.25);
      color: #FFF;
      font-size: 0.78rem;
      font-weight: 700;
      padding: 5px 12px;
      border-radius: 20px;
      border: 1.5px solid rgba(255, 255, 255, 0.5);
      font-family: 'Nunito', sans-serif;
    }}

    .hero-info-row {{
      display: flex;
      align-items: center;
    }}

    .hero-text-block h2 {{
      font-family: 'Fredoka', sans-serif;
      font-size: 1.45rem;
      font-weight: 700;
      color: #FFF;
      line-height: 1.2;
    }}

    .hero-text-block p {{
      font-size: 0.84rem;
      color: rgba(255, 255, 255, 0.95);
      margin-top: 2px;
      font-weight: 600;
      font-family: 'Nunito', sans-serif;
    }}

    /* Products Grid:
       - 2 columns on mobile (< 640px)
       - 3 columns on tablet (640px - 949px)
       - 4 columns on laptop/desktop (≥ 950px) */
    .two-col-product-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      width: 100%;
    }}

    @media (min-width: 640px) and (max-width: 949px) {{
      .two-col-product-grid {{
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
      }}
    }}

    @media (min-width: 950px) {{
      .two-col-product-grid {{
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
      }}
    }}

    .product-box-solid {{
      background-color: #FFFFFF;
      border-radius: var(--radius-md);
      overflow: hidden;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      border: 2px solid #FFFFFF;
      position: relative;
      transition: transform 0.15s ease;
    }}

    .product-box-solid:active {{
      transform: scale(0.96);
    }}

    @media (hover: hover) {{
      .product-box-solid:hover {{
        transform: translateY(-3px);
        border-color: var(--current-color, #FF7A00);
      }}
    }}

    .product-img-frame {{
      position: relative;
      width: 100%;
      aspect-ratio: 1 / 1;
      background-color: #EDECE6;
      overflow: hidden;
    }}

    .product-full-img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.3s ease;
    }}

    .product-box-solid:hover .product-full-img {{
      transform: scale(1.05);
    }}

    .product-badge-num {{
      position: absolute;
      top: 8px;
      left: 8px;
      background-color: var(--current-color, #FF7A00);
      color: #FFFFFF;
      font-size: 0.74rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 8px;
      border: 1px solid #FFFFFF;
    }}

    /* Cute Photo Zoom Indicator (Heart ♡) */
    .product-zoom-solid {{
      position: absolute;
      bottom: 8px;
      right: 8px;
      width: 28px;
      height: 28px;
      background-color: #FFFFFF;
      border: 1.5px solid var(--current-color, #FF7A00);
      color: var(--current-color, #FF7A00);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 800;
    }}

    .product-meta-foot {{
      padding: 9px 10px;
      background-color: #FFFFFF;
      border-top: 1px solid #EDECE6;
    }}

    .product-filename-text {{
      font-size: 0.72rem;
      color: var(--text-muted);
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      display: block;
      font-family: 'Nunito', sans-serif;
    }}

    /* ========================================================
       FULLSCREEN LIGHTBOX
       ======================================================== */
    .lightbox-screen {{
      position: fixed;
      inset: 0;
      background-color: rgba(35, 33, 22, 0.97);
      z-index: 1000;
      display: none;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      user-select: none;
    }}

    .lightbox-screen.active {{
      display: flex;
    }}

    .lb-top-bar {{
      position: absolute;
      top: 16px;
      left: 16px;
      right: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: #FFF;
      z-index: 10;
    }}

    .lb-item-title {{
      background-color: var(--current-color, #FF7A00);
      color: #FFF;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.88rem;
      font-weight: 700;
      border: 1.5px solid #FFFFFF;
    }}

    .lb-close-round {{
      background-color: #FFFFFF;
      border: none;
      color: #111;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      font-size: 20px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }}

    .lb-img-box {{
      max-width: 95vw;
      max-height: 78vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px;
    }}

    .lb-preview-img {{
      max-width: 95vw;
      max-height: 75vh;
      object-fit: contain;
      border-radius: 14px;
      border: 3px solid #FFFFFF;
    }}

    .lb-arrow-btn {{
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 46px;
      height: 46px;
      border-radius: 50%;
      background-color: #FFFFFF;
      border: 2px solid #111;
      color: #111;
      font-size: 24px;
      font-weight: bold;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10;
    }}

    .lb-arrow-btn.prev {{ left: 12px; }}
    .lb-arrow-btn.next {{ right: 12px; }}

    .lb-counter-bottom {{
      position: absolute;
      bottom: 20px;
      color: #FFFFFF;
      font-size: 0.9rem;
      font-weight: 700;
      font-family: 'Nunito', sans-serif;
    }}
  </style>
</head>
<body>

  <!-- ========================================================
       CUTE FLOATING BACKGROUND SVGS (Authentic Oopsie Handcrafted Products)
       Modeled directly from Oopsie's actual creations in studio colors!
       ======================================================== -->
  <div class="bg-floating-container">
    <!-- 1. Avocado Specs Holder (from Specs holder) -->
    <svg class="float-svg pos-avocado" viewBox="0 0 100 100" fill="none">
      <path d="M50 18 C36 18 30 34 26 52 C22 70 30 88 50 88 C70 88 78 70 74 52 C70 34 64 18 50 18 Z" fill="#98aa68" stroke="#FFFFFF" stroke-width="2.5"/>
      <path d="M46 18 C46 10 54 8 56 12 C58 16 52 20 46 18 Z" fill="#556b2f" stroke="#FFFFFF" stroke-width="1.5"/>
      <circle cx="50" cy="62" r="15" fill="#716c4a" stroke="#FFFFFF" stroke-width="2.5"/>
      <circle cx="43" cy="38" r="2" fill="#2d3436"/>
      <circle cx="57" cy="38" r="2" fill="#2d3436"/>
      <circle cx="39" cy="42" r="2.5" fill="#f0a098"/>
      <circle cx="61" cy="42" r="2.5" fill="#f0a098"/>
      <path d="M47 43 Q50 46 53 43" stroke="#2d3436" stroke-width="2" stroke-linecap="round" fill="none"/>
    </svg>

    <!-- 2. Ceramic Goldfish Vase with Chunky Handles (from ceramic pics) -->
    <svg class="float-svg pos-ceramic" viewBox="0 0 100 100" fill="none">
      <path d="M26 48 C16 48 16 68 28 68" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round" fill="none"/>
      <path d="M74 48 C84 48 84 68 72 68" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round" fill="none"/>
      <path d="M38 28 C38 24 62 24 62 28 L64 36 C76 44 76 74 64 84 C58 88 42 88 36 84 C24 74 24 44 36 36 Z" fill="#f7f5f0" stroke="#FFFFFF" stroke-width="2.5"/>
      <ellipse cx="50" cy="27" rx="12" ry="4" fill="#9bbec7" stroke="#FFFFFF" stroke-width="2"/>
      <ellipse cx="50" cy="58" rx="10" ry="7" fill="#f07018"/>
      <path d="M58 58 L66 52 L64 58 L66 64 Z" fill="#f07018"/>
      <circle cx="44" cy="56" r="1.5" fill="#2d3436"/>
      <circle cx="40" cy="48" r="2" stroke="#9bbec7" stroke-width="1.5" fill="none"/>
    </svg>

    <!-- 3. Beaded Flower in Terracotta Pot (from beaded flowers) -->
    <svg class="float-svg pos-beaded-pot" viewBox="0 0 100 100" fill="none">
      <path d="M34 44 L66 44 L60 84 C60 88 40 88 40 84 Z" fill="#c96232" stroke="#FFFFFF" stroke-width="2.5"/>
      <rect x="30" y="36" width="40" height="9" rx="3" fill="#ba5828" stroke="#FFFFFF" stroke-width="2"/>
      <path d="M38 45 Q32 60 36 78" stroke="#7d9d8b" stroke-width="2" stroke-linecap="round" stroke-dasharray="1 4" fill="none"/>
      <path d="M62 45 Q68 60 64 78" stroke="#7d9d8b" stroke-width="2" stroke-linecap="round" stroke-dasharray="1 4" fill="none"/>
      <path d="M50 45 Q50 65 52 82" stroke="#7d9d8b" stroke-width="2" stroke-linecap="round" stroke-dasharray="1 4" fill="none"/>
      <circle cx="36" cy="55" r="3" fill="#f0a098"/>
      <circle cx="34" cy="68" r="3" fill="#d9827c"/>
      <circle cx="64" cy="55" r="3" fill="#8ea696"/>
      <circle cx="66" cy="68" r="3" fill="#f0a098"/>
      <circle cx="50" cy="34" r="5" fill="#f8a098"/>
      <circle cx="44" cy="32" r="4" fill="#f0a098"/>
      <circle cx="56" cy="32" r="4" fill="#f0a098"/>
      <circle cx="50" cy="26" r="4" fill="#f0a098"/>
      <circle cx="50" cy="33" r="2" fill="#cca94e"/>
    </svg>

    <!-- 4. Stacked Bubble Bead Artisan Candle (from candals) -->
    <svg class="float-svg pos-bubble-candle" viewBox="0 0 100 100" fill="none">
      <path d="M50 6 C47 13 46 17 50 20 C54 17 53 13 50 6 Z" fill="#f07018"/>
      <line x1="50" y1="20" x2="50" y2="25" stroke="#FFFFFF" stroke-width="2.5"/>
      <circle cx="50" cy="31" r="7.5" fill="#d9827c" stroke="#FFFFFF" stroke-width="2"/>
      <circle cx="50" cy="43" r="7.5" fill="#d9b860" stroke="#FFFFFF" stroke-width="2"/>
      <circle cx="50" cy="55" r="7.5" fill="#7d9d8b" stroke="#FFFFFF" stroke-width="2"/>
      <circle cx="50" cy="67" r="7.5" fill="#7d7db8" stroke="#FFFFFF" stroke-width="2"/>
      <circle cx="50" cy="79" r="7.5" fill="#c85a75" stroke="#FFFFFF" stroke-width="2"/>
      <circle cx="50" cy="90" r="7.5" fill="#5078c8" stroke="#FFFFFF" stroke-width="2"/>
    </svg>

    <!-- 5. Sleepy Fabric Heart Charm (from Car charms & wall hanging) -->
    <svg class="float-svg pos-sleepy-heart" viewBox="0 0 100 100" fill="none">
      <path d="M50 24 C50 10 46 8 50 4 C54 8 50 10 50 24" stroke="#782828" stroke-width="2" fill="none"/>
      <path d="M50 82 C30 68 20 54 20 40 C20 28 29 22 38 22 C45 22 49 26 50 30 C51 26 55 22 62 22 C71 22 80 28 80 40 C80 54 70 68 50 82 Z" fill="#d9827c" stroke="#FFFFFF" stroke-width="3"/>
      <path d="M50 78 C33 65 24 52 24 40 C24 31 31 26 38 26 C44 26 48 30 50 34 C52 30 56 26 62 26 C69 26 76 31 76 40 C76 52 67 65 50 78 Z" stroke="rgba(255,255,255,0.7)" stroke-width="1.5" stroke-dasharray="2 3" fill="none"/>
      <path d="M34 46 Q39 50 44 46" stroke="#4a2020" stroke-width="2" stroke-linecap="round" fill="none"/>
      <path d="M36 49 L35 52" stroke="#4a2020" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M42 49 L43 52" stroke="#4a2020" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M56 46 Q61 50 66 46" stroke="#4a2020" stroke-width="2" stroke-linecap="round" fill="none"/>
      <path d="M58 49 L57 52" stroke="#4a2020" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M64 49 L65 52" stroke="#4a2020" stroke-width="1.5" stroke-linecap="round"/>
      <circle cx="34" cy="53" r="3" fill="#f86888"/>
      <circle cx="66" cy="53" r="3" fill="#f86888"/>
    </svg>

    <!-- 6. Sleepy Crescent Moon Charm (from Car charms & wall hanging) -->
    <svg class="float-svg pos-sleepy-moon" viewBox="0 0 100 100" fill="none">
      <path d="M48 20 C48 10 52 6 52 2" stroke="#782828" stroke-width="2"/>
      <path d="M52 20 C72 26 78 54 62 76 C46 98 18 90 26 72 C40 80 62 70 54 44 C50 32 44 26 52 20 Z" fill="#8ea696" stroke="#FFFFFF" stroke-width="2.5"/>
      <path d="M48 52 Q53 56 58 52" stroke="#263b2f" stroke-width="2" stroke-linecap="round" fill="none"/>
      <path d="M50 55 L49 57" stroke="#263b2f" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M56 55 L57 57" stroke="#263b2f" stroke-width="1.5" stroke-linecap="round"/>
      <circle cx="53" cy="60" r="2.5" fill="#f0a098"/>
    </svg>

    <!-- 7. Crochet Strawberry Keychain (from Crochet keychains & toys) -->
    <svg class="float-svg pos-crochet-berry" viewBox="0 0 100 100" fill="none">
      <circle cx="50" cy="14" r="8" stroke="#cca94e" stroke-width="3" fill="none"/>
      <path d="M50 22 L50 34" stroke="#7d9d8b" stroke-width="3" stroke-linecap="round"/>
      <path d="M36 38 C42 32 50 36 50 36 C50 36 58 32 64 38 C58 42 50 40 50 40 C50 40 42 42 36 38 Z" fill="#5c774e" stroke="#FFFFFF" stroke-width="1.5"/>
      <path d="M34 40 C24 50 30 76 50 90 C70 76 76 50 66 40 C58 43 42 43 34 40 Z" fill="#c84646" stroke="#FFFFFF" stroke-width="2.5"/>
      <circle cx="44" cy="52" r="1.5" fill="#FFFFFF"/>
      <circle cx="56" cy="52" r="1.5" fill="#FFFFFF"/>
      <circle cx="50" cy="62" r="1.5" fill="#FFFFFF"/>
      <circle cx="42" cy="70" r="1.5" fill="#FFFFFF"/>
      <circle cx="58" cy="70" r="1.5" fill="#FFFFFF"/>
      <circle cx="50" cy="78" r="1.5" fill="#FFFFFF"/>
    </svg>

    <!-- 8. Scalloped Clay Photo Frame with Ribbon Bow (from fridge magnet) -->
    <svg class="float-svg pos-clay-frame" viewBox="0 0 100 100" fill="none">
      <path d="M26 26 Q30 20 38 22 Q46 18 54 22 Q62 18 70 22 Q78 20 80 28 Q84 36 80 44 Q84 52 80 60 Q84 68 80 76 Q76 82 68 80 Q60 84 52 80 Q44 84 36 80 Q28 82 24 74 Q20 66 24 58 Q20 50 24 42 Q20 34 26 26 Z" fill="#f4ecd8" stroke="#FFFFFF" stroke-width="2.5"/>
      <rect x="36" y="34" width="34" height="38" rx="4" fill="#716c4a" stroke="#FFFFFF" stroke-width="2"/>
      <ellipse cx="30" cy="26" rx="6" ry="4" transform="rotate(-30 30 26)" fill="#c96232"/>
      <ellipse cx="22" cy="32" rx="6" ry="4" transform="rotate(30 22 32)" fill="#c96232"/>
      <circle cx="26" cy="28" r="3" fill="#a83e3e"/>
    </svg>

    <!-- 9. Retro Cross-Stitch Camera (from Cross stitch cards) -->
    <svg class="float-svg pos-cross-stitch-cam" viewBox="0 0 100 100" fill="none">
      <rect x="22" y="32" width="56" height="46" rx="8" fill="#5078c8" stroke="#FFFFFF" stroke-width="2.5"/>
      <path d="M22 40 L78 40 L78 36 C78 34 76 32 74 32 L26 32 C24 32 22 34 22 36 Z" fill="#f7f5f0"/>
      <rect x="28" y="26" width="10" height="6" rx="2" fill="#c84646"/>
      <circle cx="50" cy="56" r="14" fill="#3a4f66" stroke="#FFFFFF" stroke-width="3"/>
      <circle cx="50" cy="56" r="8" fill="#1e201b"/>
      <circle cx="47" cy="53" r="2.5" fill="#FFFFFF"/>
      <rect x="64" y="35" width="8" height="6" rx="1.5" fill="#1e201b"/>
    </svg>

    <!-- 10. Pencil House Bookmark (from book marks) -->
    <svg class="float-svg pos-pencil-bookmark" viewBox="0 0 100 100" fill="none">
      <rect x="36" y="36" width="28" height="52" rx="3" fill="#d9b860" stroke="#FFFFFF" stroke-width="2.5"/>
      <polygon points="36,36 64,36 50,14" fill="#f4ecd8" stroke="#FFFFFF" stroke-width="2.5"/>
      <polygon points="46,20 54,20 50,14" fill="#3a4f66"/>
      <circle cx="45" cy="28" r="1.5" fill="#2d3436"/>
      <circle cx="55" cy="28" r="1.5" fill="#2d3436"/>
      <path d="M48 31 Q50 33 52 31" stroke="#2d3436" stroke-width="1.5" stroke-linecap="round" fill="none"/>
      <rect x="40" y="44" width="7" height="9" rx="1.5" fill="#f7f5f0" stroke="#3a4f66" stroke-width="1"/>
      <rect x="53" y="44" width="7" height="9" rx="1.5" fill="#f7f5f0" stroke="#3a4f66" stroke-width="1"/>
      <path d="M45 76 L45 88 L55 88 L55 76 C55 73 45 73 45 76 Z" fill="#a83e3e"/>
    </svg>

    <!-- 11. Crystal Suncatcher Plant Stake (from Plant charms) -->
    <svg class="float-svg pos-suncatcher" viewBox="0 0 100 100" fill="none">
      <path d="M50 8 C66 12 70 30 56 36 C42 42 44 26 52 24" stroke="#cca94e" stroke-width="2.5" stroke-linecap="round" fill="none"/>
      <line x1="56" y1="36" x2="56" y2="92" stroke="#cca94e" stroke-width="2" stroke-linecap="round"/>
      <path d="M44 42 C50 44 52 52 46 56 C42 60 36 58 38 52 C40 54 46 54 44 48 C43 45 40 43 44 42 Z" fill="#cca94e"/>
      <polygon points="56,48 59,51 59,57 56,60 53,57 53,51" fill="#f0a098" stroke="#FFFFFF" stroke-width="1"/>
      <polygon points="56,68 61,74 61,86 56,92 51,86 51,74" fill="#e59086" stroke="#FFFFFF" stroke-width="1.5"/>
    </svg>

    <!-- 12. Denim & Plaid Camera Pouch (from Pouches,wallets & tablet sleeves) -->
    <svg class="float-svg pos-denim-pouch" viewBox="0 0 100 100" fill="none">
      <rect x="24" y="42" width="52" height="42" rx="6" fill="#3b5266" stroke="#FFFFFF" stroke-width="2.5"/>
      <path d="M26 36 L74 36 L72 56 C72 58 70 60 68 60 L32 60 C30 60 28 58 28 56 Z" fill="#d9827c" stroke="#FFFFFF" stroke-width="2"/>
      <line x1="28" y1="46" x2="72" y2="46" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
      <line x1="28" y1="52" x2="72" y2="52" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
      <line x1="42" y1="36" x2="42" y2="60" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
      <line x1="58" y1="36" x2="58" y2="60" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
      <path d="M34 68 C34 74 42 74 42 68" stroke="#FFFFFF" stroke-width="2" fill="none"/>
      <rect x="76" y="58" width="8" height="12" rx="1.5" fill="#f7f5f0" stroke="#FFFFFF" stroke-width="1"/>
    </svg>
  </div>

  <!-- Top Sticky Header with Official Logo -->
  <header>
    <div class="header-inner">
      <div class="brand-wrap" onclick="showCategoriesView()">
        <img src="logo.png" alt="Oopsie" class="logo-header-img">
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="header-stat-pill">🌸 {len(categories)} Collections • {total_products} Items</span>
        <button class="btn-search-toggle" id="btn-search-toggle" onclick="toggleSearch()" title="Search catalog" aria-label="Search">
          <svg class="search-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="10.5" cy="10.5" r="7"/>
            <path d="M16 16L21.5 21.5"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Search Input -->
    <div class="search-box-wrap" id="search-box-wrap">
      <div class="search-input-inner">
        <svg class="search-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#716c4a" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="10.5" cy="10.5" r="7"/>
          <path d="M16 16L21.5 21.5"/>
        </svg>
        <input type="text" id="search-input" class="search-input-field" placeholder="Search collection or product...">
        <button type="button" class="search-clear-btn" id="search-clear-btn" onclick="clearSearch()" title="Clear">✕</button>
      </div>
    </div>
  </header>

  <main>
    <!-- VIEW 1: Categories Only in 2 Columns (NO IMAGES - TEXT & COUNT TABLE) -->
    <div class="view-categories-wrap" id="view-categories">
      <div class="catalog-hero">
        <img src="logo.png" alt="Oopsie Handcrafted" class="hero-big-logo">
        <br>
        <span class="catalog-hero-pill">🌼 handmade with love & smiles 💕</span>
        <h2>Explore Collections</h2>
        <p>Select any collection to view all products ♡</p>
      </div>

      <!-- 2-Column Category Table (No images, just name & count!) -->
      <div class="two-col-cat-table" id="categories-grid">
        <!-- Dynamically rendered via JS -->
      </div>
    </div>

    <!-- VIEW 2: Products Inside Selected Category in 2 Columns -->
    <div class="view-products-wrap" id="view-products">
      <div class="category-hero-solid" id="category-hero-solid">
        <div class="hero-top-row">
          <button class="btn-back-solid" onclick="showCategoriesView()">
            ← All Collections ✿
          </button>
          <span class="hero-count-solid" id="hero-count-solid">0 Items</span>
        </div>

        <div class="hero-info-row">
          <div class="hero-text-block">
            <h2 id="hero-title-text">Category Name</h2>
            <p id="hero-tagline-text">Handmade collection</p>
          </div>
        </div>
      </div>

      <!-- Products Grid (Responsive Columns) -->
      <div class="two-col-product-grid" id="products-grid">
        <!-- Dynamically rendered via JS -->
      </div>
    </div>
  </main>

  <!-- Fullscreen Lightbox -->
  <div class="lightbox-screen" id="lightbox">
    <div class="lb-top-bar">
      <span class="lb-item-title" id="lb-badge">Product #1</span>
      <button class="lb-close-round" onclick="closeLightbox()">✕</button>
    </div>

    <button class="lb-arrow-btn prev" onclick="prevLightboxImage()">‹</button>
    <div class="lb-img-box">
      <img src="" alt="" class="lb-preview-img" id="lb-img">
    </div>
    <button class="lb-arrow-btn next" onclick="nextLightboxImage()">›</button>

    <div class="lb-counter-bottom">
      <span id="lb-counter">1 of 8</span>
    </div>
  </div>

  <script>
    const CATEGORIES = {categories_json};

    let activeCategory = null;
    let currentLightboxList = [];
    let currentLightboxIdx = 0;

    const viewCategories = document.getElementById('view-categories');
    const viewProducts = document.getElementById('view-products');
    const categoriesGrid = document.getElementById('categories-grid');
    const productsGrid = document.getElementById('products-grid');
    const searchBoxWrap = document.getElementById('search-box-wrap');
    const searchInput = document.getElementById('search-input');
    const heroSolidBanner = document.getElementById('category-hero-solid');

    // 1. Render Categories View: Simple, Clean Tile (Name & Count Only, NO Icons, NO Buttons)
    function renderCategories(filterText = '') {{
      categoriesGrid.innerHTML = '';
      const q = filterText.toLowerCase().trim();

      const filtered = CATEGORIES.filter(cat =>
        cat.name.toLowerCase().includes(q)
      );

      filtered.forEach(cat => {{
        const card = document.createElement('div');
        card.className = 'cat-tile';
        card.style.setProperty('--cat-color', cat.color);
        card.style.setProperty('--cat-text-color', cat.text_color);
        card.onclick = () => openCategory(cat.slug);

        card.innerHTML = 
          '<div class="cat-tile-name">' + cat.name + '</div>' +
          '<div class="cat-tile-count">' + cat.pill_text + '</div>';

        categoriesGrid.appendChild(card);
      }});
    }}

    // 2. Open Category & Render Products (Responsive Grid with Product Photos)
    function openCategory(slug) {{
      const cat = CATEGORIES.find(c => c.slug === slug);
      if (!cat) return;

      activeCategory = cat;
      window.location.hash = 'category=' + slug;

      // Update Hero Banner Styling with Category Custom Solid Color
      document.documentElement.style.setProperty('--current-color', cat.color);
      heroSolidBanner.style.backgroundColor = cat.color;

      document.getElementById('hero-title-text').textContent = cat.name;
      document.getElementById('hero-tagline-text').textContent = cat.count + ' cute handcrafted products';
      document.getElementById('hero-count-solid').textContent = cat.count + ' Products';

      renderProducts(cat);

      viewCategories.style.display = 'none';
      viewProducts.style.display = 'block';
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    function renderProducts(cat, filterText = '') {{
      productsGrid.innerHTML = '';
      const q = filterText.toLowerCase().trim();

      const items = cat.items.filter(item =>
        item.title.toLowerCase().includes(q) ||
        item.filename.toLowerCase().includes(q)
      );

      currentLightboxList = items;

      items.forEach((item, idx) => {{
        const card = document.createElement('div');
        card.className = 'product-box-solid';
        card.onclick = () => openLightbox(idx);

        card.innerHTML = 
          '<div class="product-img-frame">' +
            '<img src="' + item.src + '" alt="' + item.title + '" class="product-full-img" loading="lazy">' +
            '<div class="product-badge-num">#' + item.index + '</div>' +
            '<div class="product-zoom-solid">♡</div>' +
          '</div>' +
          '<div class="product-meta-foot">' +
            '<span class="product-filename-text">' + item.filename + '</span>' +
          '</div>';

        productsGrid.appendChild(card);
      }});
    }}

    // 3. Return to Categories View
    function showCategoriesView() {{
      activeCategory = null;
      window.location.hash = '';
      viewProducts.style.display = 'none';
      viewCategories.style.display = 'block';
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    // 4. Search Filter
    function toggleSearch() {{
      const btn = document.getElementById('btn-search-toggle');
      searchBoxWrap.classList.toggle('active');
      if (searchBoxWrap.classList.contains('active')) {{
        if (btn) btn.classList.add('active');
        searchInput.focus();
      }} else {{
        if (btn) btn.classList.remove('active');
        clearSearch();
      }}
    }}

    function clearSearch() {{
      searchInput.value = '';
      const clearBtn = document.getElementById('search-clear-btn');
      if (clearBtn) clearBtn.style.display = 'none';
      if (activeCategory) {{
        renderProducts(activeCategory);
      }} else {{
        renderCategories();
      }}
    }}

    searchInput.addEventListener('input', (e) => {{
      const text = e.target.value;
      const clearBtn = document.getElementById('search-clear-btn');
      if (clearBtn) clearBtn.style.display = text ? 'block' : 'none';
      if (activeCategory) {{
        renderProducts(activeCategory, text);
      }} else {{
        renderCategories(text);
      }}
    }});

    // 5. Back Button (Hash Change)
    window.addEventListener('hashchange', () => {{
      const hash = window.location.hash;
      if (hash.startsWith('#category=')) {{
        const slug = hash.replace('#category=', '');
        if (!activeCategory || activeCategory.slug !== slug) {{
          openCategory(slug);
        }}
      }} else {{
        if (activeCategory) {{
          showCategoriesView();
        }}
      }}
    }});

    // 6. Lightbox Viewer
    const lb = document.getElementById('lightbox');
    const lbImg = document.getElementById('lb-img');
    const lbBadge = document.getElementById('lb-badge');
    const lbCounter = document.getElementById('lb-counter');

    function openLightbox(idx) {{
      if (!currentLightboxList[idx]) return;
      currentLightboxIdx = idx;
      updateLightbox();
      lb.classList.add('active');
      document.body.style.overflow = 'hidden';
    }}

    function closeLightbox() {{
      lb.classList.remove('active');
      document.body.style.overflow = '';
    }}

    function updateLightbox() {{
      const item = currentLightboxList[currentLightboxIdx];
      if (!item) return;

      lbImg.src = item.src;
      lbBadge.textContent = item.title;
      lbCounter.textContent = (currentLightboxIdx + 1) + ' of ' + currentLightboxList.length;

      if (activeCategory) {{
        lbBadge.style.backgroundColor = activeCategory.color;
        lbBadge.style.color = activeCategory.text_color;
      }}
    }}

    function nextLightboxImage() {{
      currentLightboxIdx = (currentLightboxIdx + 1) % currentLightboxList.length;
      updateLightbox();
    }}

    function prevLightboxImage() {{
      currentLightboxIdx = (currentLightboxIdx - 1 + currentLightboxList.length) % currentLightboxList.length;
      updateLightbox();
    }}

    // Keyboard navigation
    window.addEventListener('keydown', (e) => {{
      if (!lb.classList.contains('active')) return;
      if (e.key === 'ArrowRight') nextLightboxImage();
      else if (e.key === 'ArrowLeft') prevLightboxImage();
      else if (e.key === 'Escape') closeLightbox();
    }});

    // Mobile touch swipe gestures
    let touchX = 0;
    lb.addEventListener('touchstart', (e) => {{
      touchX = e.changedTouches[0].screenX;
    }}, {{ passive: true }});

    lb.addEventListener('touchend', (e) => {{
      const diff = e.changedTouches[0].screenX - touchX;
      if (Math.abs(diff) > 40) {{
        if (diff < 0) nextLightboxImage();
        else prevLightboxImage();
      }}
    }}, {{ passive: true }});

    // Initial check for hash on load
    renderCategories();
    if (window.location.hash.startsWith('#category=')) {{
      const initialSlug = window.location.hash.replace('#category=', '');
      openCategory(initialSlug);
    }}

    // Live Auto-Sync: When served locally over HTTP, check for catalog updates every 2s
    if (window.location.protocol.startsWith('http')) {{
      let lastCategoriesCount = CATEGORIES.length;
      let lastTotalItems = CATEGORIES.reduce((acc, c) => acc + c.count, 0);
      setInterval(() => {{
        fetch('/api/status?t=' + Date.now())
          .then(res => res.json())
          .then(data => {{
            if (data && (data.categories !== lastCategoriesCount || data.products !== lastTotalItems)) {{
              console.log('🌸 [Auto-Sync] Detected changes in oppsie categories! Refreshing catalog...');
              window.location.reload();
            }}
          }})
          .catch(() => {{}});
      }}, 2000);
    }}
  </script>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Also save JSON data
    json_path = os.path.join(os.path.dirname(output_path) or '.', 'catalog_data.json')
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    print(f"Generated cute catalog: {output_path} ({len(categories)} categories, {total_products} items)")

if __name__ == '__main__':
    cats, total = scan_catalog_data('.')
    generate_catalog_html(cats, total, 'index.html')
