#!/usr/bin/env python3
"""
OOPSIE — Little things, happy feelings
Dynamic Catalog Generator matching the authentic design from
https://oopsie-collection.kush-a-jariwala21.chatgpt.site/
- Reads 'oppsie categories' and auto-organizes root folders in real time
- Renders the exact Avenir/Palatino dark-olive palette, minimalist category tiles,
  native gallery dialog modal, and full-size photo viewer with arrow navigation!
"""

import os
import re
import json
import shutil
import urllib.parse

# Preferred display names and order matching Oopsie Studio collection
PREFERRED_ORDER = [
    'jewelery',
    'fabric charms',
    'charms',
    'beaded flowers',
    'Crochet keychains & toys',
    'Plant charms',
    'Car charms & wall hanging',
    'Specs holder',
    'Pouches,wallets & tablet sleeves',
    'ceramic pics',
    'candals',
    'small frams',
    'fridge magnet',
    'greeting card',
    'post cards',
    'Cross stitch cards',
    'Stickers card',
    'stickers',
    'book marks',
    'dairy',
    'Calender',
    'Selected felt & fabric charms for keychains,bag,car,wall hanging'
]

DISPLAY_NAMES = {
    'jewelery': 'Jewellery',
    'fabric charms': 'Fabric charms',
    'charms': 'Charms',
    'beaded flowers': 'Beaded flowers',
    'Crochet keychains & toys': 'Crochet keychains & toys',
    'Plant charms': 'Plant charms',
    'Car charms & wall hanging': 'Car charms & wall hangings',
    'Specs holder': 'Specs holders',
    'Pouches,wallets & tablet sleeves': 'Pouches, wallets & tablet sleeves',
    'ceramic pics': 'Ceramics',
    'candals': 'Candles',
    'small frams': 'Small frames',
    'fridge magnet': 'Fridge magnets',
    'greeting card': 'Greeting cards',
    'post cards': 'Postcards',
    'Cross stitch cards': 'Cross-stitch cards',
    'Stickers card': 'Sticker cards',
    'stickers': 'Stickers',
    'book marks': 'Bookmarks',
    'dairy': 'Diaries',
    'Calender': 'Calendars',
    'Selected felt & fabric charms for keychains,bag,car,wall hanging': 'Felt & Fabric Charms',
}

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

def format_folder_name(folder_name):
    """Turns folder_name like 'clay_pins' or 'hair-clips' into 'Clay Pins' or 'Hair Clips'"""
    cleaned = folder_name.replace('_', ' ').replace('-', ' ').replace(',', ', ').strip()
    words = [word.capitalize() for word in cleaned.split() if word]
    return ' '.join(words)

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
        '__pycache__', 'scratch', 'node_modules', '.gemini', '.vscode', '.idea',
        'archive'
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

        # Check if entry contains images
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

def scan_catalog_data(base_dir='.'):
    """
    Scans the categories directory and returns:
    (collection, total_products)
    Where collection is a list of:
    {
      "name": "Jewellery",
      "folder": "jewelery",
      "images": ["oppsie%20categories/jewelery/...", ...]
    }
    """
    try:
        organize_root_categories(base_dir)
    except Exception:
        pass

    cat_dir, prefix = get_categories_dir(base_dir)
    ignored = {
        'oppsie categories', 'oopsie categories', 'categories',
        '.git', '.vscode', '.idea', '__pycache__', 'scratch', 'node_modules', '.gemini',
        'archive'
    }

    try:
        entries = [e for e in os.listdir(cat_dir) if not e.startswith('.') and e not in ignored]
    except OSError:
        entries = []

    # Sort entries according to PREFERRED_ORDER, then alphabetically
    order_map = {name.lower(): i for i, name in enumerate(PREFERRED_ORDER)}
    def sort_key(name):
        return (order_map.get(name.lower(), 9999), natural_sort_key(name))

    entries.sort(key=sort_key)

    collection = []
    total_products = 0

    for entry in entries:
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

        display_name = DISPLAY_NAMES.get(entry, format_folder_name(entry))

        encoded_prefix = urllib.parse.quote(prefix) if prefix else ''
        encoded_folder = urllib.parse.quote(entry)

        image_urls = []
        for img in images:
            encoded_img = urllib.parse.quote(img)
            if encoded_prefix:
                url = f"{encoded_prefix}/{encoded_folder}/{encoded_img}"
            else:
                url = f"{encoded_folder}/{encoded_img}"
            image_urls.append(url)

        collection.append({
            "name": display_name,
            "folder": entry,
            "images": image_urls
        })
        total_products += len(image_urls)

    return collection, total_products

def generate_catalog_html(collection, total_products, output_path='index.html'):
    """
    Generates the complete index.html matching https://oopsie-collection.kush-a-jariwala21.chatgpt.site/
    with:
    - 5-color wave animation preloader
    - Pre-rendered static category markup for instant visual paint
    - Anti-cache meta headers
    - Live real-time polling to update categories dynamically on both localhost and GitHub Pages
    """
    categories_count = len(collection)
    collection_json = json.dumps(collection, ensure_ascii=False)

    # Pre-render category buttons for instantaneous paint
    category_buttons = []
    for idx, cat in enumerate(collection):
        name = cat['name']
        count = len(cat['images'])
        btn = f'<button class="category" aria-haspopup="dialog" onclick="openGallery({idx}, this)"><span class="name">{name}</span><span class="count" aria-label="{count} photos">{count}</span></button>'
        category_buttons.append(btn)
    categories_inner_html = '\n'.join(category_buttons)

    html_content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#716c4a">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<link rel="icon" href="logo.png?v=2">
<title>OOPSIE — Little things, happy feelings</title>
<style>
:root{{--paper:#716c4a;--ink:#fff8ea;--quiet:#f2ecda;--pink:#f6a499;--sage:#abbfb6;--blue:#557dca;--line:#928d6b;--white:#716c4a;--surface:#625e40;--brand-burgundy:#662020;--focus:#ffceb7;color-scheme:dark;font-family:'Avenir Next',Avenir,'Trebuchet MS',sans-serif;color:var(--ink);background:var(--paper)}}*{{box-sizing:border-box}}body{{margin:0}}button{{font:inherit;color:inherit;cursor:pointer}}button:focus-visible{{outline:3px solid var(--focus);outline-offset:5px}}button{{ -webkit-tap-highlight-color:transparent}}::selection{{background:var(--pink);color:var(--brand-burgundy)}}.index{{max-width:1120px;margin:auto;padding:38px 64px 30px;min-height:100dvh;display:flex;flex-direction:column}}.masthead{{display:flex;justify-content:center;position:relative}}.logo{{width:auto;height:96px;max-width:240px;object-fit:contain}}.small-note{{position:absolute;right:0;top:32px;font-size:12px;color:var(--quiet)}}.intro{{text-align:center;margin:36px auto 38px;max-width:650px}}.intro h1{{font-family:'Palatino Linotype',Palatino,'Book Antiqua',serif;font-weight:400;letter-spacing:-1.8px;font-size:clamp(35px,4.2vw,54px);line-height:1.12;margin:0 0 16px}}.intro p{{font-size:14px;line-height:1.8;color:var(--quiet);margin:0}}.categories{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px 18px}}.category{{position:relative;border:1px solid transparent;border-bottom-color:var(--line);background:transparent;min-height:59px;padding:13px 14px;display:flex;align-items:center;text-align:left;gap:14px;border-radius:9px;transition:background .2s,border-color .2s,transform .2s}}.category:hover{{color:var(--brand-burgundy);background:var(--pink);border-color:var(--pink);transform:translateY(-2px)}}.category .name{{font-size:14px;line-height:1.4;flex:1}}.count{{font-size:11px;color:var(--quiet);background:var(--surface);width:25px;height:25px;border-radius:50%;display:grid;place-items:center;flex:none}}.category:hover .count{{background:#fff0dc;color:var(--brand-burgundy)}}.end{{display:flex;align-items:center;justify-content:space-between;gap:20px;font-size:11px;color:var(--quiet);margin-top:auto;padding-top:40px}}.dots{{display:flex;gap:6px}}.dots i{{width:7px;height:7px;border-radius:50%;background:var(--sage)}}.dots i:nth-child(2){{background:var(--brand-burgundy)}}.dots i:nth-child(3){{background:var(--pink)}}.dots i:nth-child(4){{background:#f77916}}.dots i:nth-child(5){{background:var(--blue)}}dialog{{border:0;padding:0;color:var(--ink);max-width:none;max-height:none}}dialog::backdrop{{background:rgba(35,33,21,.55);backdrop-filter:blur(9px)}}.gallery{{width:min(1160px,calc(100% - 64px));height:calc(100dvh - 64px);border-radius:24px;background:var(--white);box-shadow:0 24px 90px #211e194d;overflow:hidden}}.gallery[open]{{display:flex;flex-direction:column;animation:arrive .3s ease-out}}.gallery-head{{padding:26px 36px 24px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;flex:none}}.gallery-heading{{flex:1;min-width:0}}.gallery-heading h2{{font-family:Palatino,'Book Antiqua',serif;font-size:32px;font-weight:400;letter-spacing:-.7px;margin:0 0 5px}}.gallery-heading p{{font-size:12px;color:var(--quiet);margin:0}}.close{{border:1px solid var(--line);background:transparent;border-radius:100px;min-height:42px;padding:9px 17px;font-size:12px;white-space:nowrap}}.close:hover{{background:var(--surface)}}.photos{{overflow:auto;overscroll-behavior:contain;padding:30px 36px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));align-content:start;gap:28px 22px}}.photo{{border:0;padding:0;background:none;text-align:left;min-width:0}}.image-wrap{{height:310px;border-radius:12px;background:var(--surface);overflow:hidden;display:flex;align-items:center;justify-content:center}}.photo img{{height:100%;width:100%;object-fit:contain;transition:transform .35s}}.photo:hover img{{transform:scale(1.025)}}.caption{{display:flex;justify-content:space-between;align-items:center;padding:12px 2px;font-size:11px;color:var(--quiet)}}.caption span:last-child{{font-size:17px;color:var(--ink)}}.viewer{{background:var(--paper);width:100%;height:100dvh;overflow:hidden}}.viewer[open]{{display:flex;flex-direction:column}}.viewer-head{{display:flex;justify-content:space-between;align-items:center;padding:20px 30px;gap:20px}}.viewer-head p{{font-size:13px;margin:0}}.viewer-stage{{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;position:relative;padding:10px 80px 30px}}.viewer-stage img{{display:block;max-width:100%;max-height:100%;object-fit:contain;border-radius:5px}}.step{{position:absolute;top:50%;width:44px;height:44px;border:1px solid var(--line);border-radius:50%;background:var(--surface);font-size:24px;display:grid;place-items:center}}.previous{{left:20px}}.next{{right:20px}}.viewer-foot{{text-align:center;font-size:11px;color:var(--quiet);padding:0 20px 18px}}.empty{{padding:30px}}body.modal-open{{overflow:hidden}}@keyframes arrive{{from{{opacity:0;transform:translateY(18px) scale(.985)}}to{{opacity:1;transform:none}}}}@media(min-width:1450px){{.index{{padding-top:55px;padding-bottom:40px}}.intro{{margin-top:45px;margin-bottom:45px}}.category{{min-height:65px}}}}@media(max-width:800px){{.index{{padding:28px 28px 24px}}.small-note{{display:none}}.categories{{gap:6px 12px;grid-template-columns:repeat(2,minmax(0,1fr))}}.intro{{margin:28px auto}}.category{{min-height:58px;padding:10px}}.gallery{{width:calc(100% - 24px);height:calc(100dvh - 24px);border-radius:18px}}.gallery-head{{padding:20px 24px}}.gallery-heading h2{{font-size:27px}}.photos{{grid-template-columns:repeat(2,minmax(0,1fr));padding:24px;gap:16px}}.image-wrap{{height:300px}}.end{{padding-top:32px}}}}@media(max-width:480px){{.index{{padding:23px 18px}}.logo{{width:auto;height:80px;max-width:180px}}.intro{{margin:25px auto 26px}}.intro h1{{font-size:37px;letter-spacing:-1.3px}}.intro p{{font-size:12px;max-width:260px;margin:auto}}.categories{{gap:4px 8px}}.category{{padding:10px 6px;gap:7px;min-height:60px}}.category .name{{font-size:12px}}.count{{width:21px;height:21px;font-size:10px}}.end{{font-size:10px}}.gallery-head{{padding:20px 18px;gap:10px;align-items:flex-start}}.gallery-heading h2{{font-size:26px}}.gallery-head .close{{font-size:11px;padding:8px 12px;min-height:38px}}.photos{{padding:18px;gap:16px 12px}}.image-wrap{{height:225px;border-radius:8px}}.caption{{font-size:10px}}.viewer-head{{padding:16px}}.viewer-stage{{padding:8px 10px 75px}}.step{{top:auto;bottom:12px}}.previous{{left:calc(50% - 55px)}}.next{{right:calc(50% - 55px)}}}}@media(prefers-reduced-motion:reduce){{*,*::before,*::after{{animation:none!important;transition:none!important;scroll-behavior:auto!important}}}}

/* ========================================================
   5-DOT WAVE PRELOADER (Delightful Ocean-Wave Animation)
   ======================================================== */
.preloader {{
  position: fixed;
  inset: 0;
  z-index: 999999;
  background: var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 1;
  visibility: visible;
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1), visibility 0.4s ease;
}}
.preloader.hidden {{
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
}}
.wave-dots {{
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}}
.wave-dots i {{
  width: 15px;
  height: 15px;
  border-radius: 50%;
  display: block;
  animation: dotWave 1.35s ease-in-out infinite;
}}
.wave-dots i:nth-child(1) {{ background: var(--sage); animation-delay: 0.0s; }}
.wave-dots i:nth-child(2) {{ background: var(--brand-burgundy); animation-delay: 0.15s; }}
.wave-dots i:nth-child(3) {{ background: var(--pink); animation-delay: 0.3s; }}
.wave-dots i:nth-child(4) {{ background: #f77916; animation-delay: 0.45s; }}
.wave-dots i:nth-child(5) {{ background: var(--blue); animation-delay: 0.6s; }}

@keyframes dotWave {{
  0%, 100% {{
    transform: translateY(0);
    opacity: 0.55;
  }}
  32% {{
    transform: translateY(-16px);
    opacity: 1;
  }}
}}
</style>
</head>
<body>
<!-- 5-Dot Wave Preloader -->
<div id="preloader" class="preloader" aria-label="Loading Oopsie...">
  <div class="wave-dots" aria-hidden="true">
    <i></i><i></i><i></i><i></i><i></i>
  </div>
</div>

<main class="index">
<header class="masthead"><img class="logo" src="logo.png?v=2" alt="OOPSIE"><span class="small-note">The collection</span></header>
<div class="intro"><h1>Little things.<br>Happy feelings.</h1><p>A world of colour, charm and everyday joy.<br>Pick a category. Find something that makes you smile.</p></div>
<nav class="categories" aria-label="Product categories" id="categories">{categories_inner_html}</nav>
<footer class="end"><span>{categories_count} categories to fall in love with.</span><span class="dots" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span><span>A little world of OOPSIE.</span></footer>
</main>
<dialog class="gallery" id="gallery" aria-labelledby="gallery-title"><header class="gallery-head"><div class="gallery-heading"><h2 id="gallery-title"></h2><p id="gallery-meta"></p></div><button class="close" id="close-gallery" autofocus>All categories <span aria-hidden="true">×</span></button></header><div class="photos" id="photos"></div></dialog>
<dialog class="viewer" id="viewer" aria-label="Full-size photo viewer"><header class="viewer-head"><p id="viewer-label" aria-live="polite"></p><button class="close" id="close-viewer" autofocus>Back to gallery ×</button></header><div class="viewer-stage"><img id="full-image" alt=""><button class="step previous" id="previous" aria-label="Previous photo">‹</button><button class="step next" id="next" aria-label="Next photo">›</button></div><div class="viewer-foot">Use the arrow keys to browse. Press Esc to go back.</div></dialog>
<script>
let collection = {collection_json};
const $ = id => document.getElementById(id);
const gallery = $('gallery'), viewer = $('viewer'), preloader = $('preloader');
let active = 0, currentPhoto = 0, lastCategory = null, lastPhoto = null;

// Smoothly dismiss preloader
function dismissPreloader() {{
  if (!preloader || preloader.classList.contains('hidden')) return;
  preloader.classList.add('hidden');
  setTimeout(() => {{
    preloader.style.display = 'none';
  }}, 500);
}}

const loadStartTime = Date.now();
function finishLoading() {{
  const elapsed = Date.now() - loadStartTime;
  const delay = Math.max(0, 650 - elapsed);
  setTimeout(dismissPreloader, delay);
}}

// Render Categories List in the DOM dynamically
function renderCategoriesList(items) {{
  const container = $('categories');
  if (!container) return;
  container.innerHTML = '';

  items.forEach((category, index) => {{
    const button = document.createElement('button');
    button.className = 'category';
    button.setAttribute('aria-haspopup', 'dialog');
    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = category.name;
    const count = document.createElement('span');
    count.className = 'count';
    count.textContent = category.images.length;
    count.setAttribute('aria-label', category.images.length + ' photos');
    button.append(name, count);
    button.addEventListener('click', () => openGallery(index, button));
    container.append(button);
  }});

  const countSpan = document.querySelector('.end span:first-child');
  if (countSpan) {{
    countSpan.textContent = items.length + ' categories to fall in love with.';
  }}
}}

// Real-Time Dynamic Fetch (Bypasses Browser Cache)
function fetchLatestCatalog(isInitial = false) {{
  const cacheBuster = 't=' + Date.now();
  fetch('catalog_data.json?' + cacheBuster, {{ cache: 'no-store' }})
    .then(res => {{
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    }})
    .then(latestCollection => {{
      const oldSig = JSON.stringify(collection.map(c => [c.name, c.images.length]));
      const newSig = JSON.stringify(latestCollection.map(c => [c.name, c.images.length]));

      if (oldSig !== newSig) {{
        console.log('🌸 [Live Sync] Categories updated in real time!');
        collection = latestCollection;
        renderCategoriesList(collection);
      }}
    }})
    .catch(() => {{}})
    .finally(() => {{
      if (isInitial) {{
        finishLoading();
      }}
    }});
}}

// Initial load check
fetchLatestCatalog(true);

// Background poll every 4s (ensures real-time auto updates on GitHub Pages and local)
setInterval(() => {{
  fetchLatestCatalog(false);
}}, 4000);

window.addEventListener('load', () => {{
  finishLoading();
}});
setTimeout(dismissPreloader, 3500);

function openGallery(index, trigger) {{
  active = index;
  lastCategory = trigger;
  const c = collection[index];
  if (!c) return;
  $('gallery-title').textContent = c.name;
  $('gallery-meta').textContent = c.images.length + ' photos · Select a photo for a closer look';
  $('photos').replaceChildren();
  c.images.forEach((src, i) => {{
    const button = document.createElement('button');
    button.className = 'photo';
    button.setAttribute('aria-label', 'View ' + c.name + ' photo ' + (i + 1));
    const wrap = document.createElement('span');
    wrap.className = 'image-wrap';
    const img = document.createElement('img');
    img.src = src;
    img.alt = c.name + ' — photo ' + (i + 1);
    img.loading = i < 6 ? 'eager' : 'lazy';
    img.decoding = 'async';
    wrap.append(img);
    const caption = document.createElement('span');
    caption.className = 'caption';
    const label = document.createElement('span');
    label.textContent = 'Photo ' + String(i + 1).padStart(2, '0');
    const icon = document.createElement('span');
    icon.textContent = '＋';
    icon.setAttribute('aria-hidden', 'true');
    caption.append(label, icon);
    button.append(wrap, caption);
    button.addEventListener('click', () => {{
      lastPhoto = button;
      currentPhoto = i;
      updateViewer();
      viewer.showModal();
    }});
    $('photos').append(button);
  }});
  gallery.showModal();
  document.body.classList.add('modal-open');
  $('photos').scrollTop = 0;
}}

function updateViewer() {{
  const c = collection[active];
  if (!c) return;
  $('full-image').src = c.images[currentPhoto];
  $('full-image').alt = c.name + ' — photo ' + (currentPhoto + 1);
  $('viewer-label').textContent = c.name + ' · ' + (currentPhoto + 1) + ' / ' + c.images.length;
}}

function step(delta) {{
  if (!collection[active] || !collection[active].images.length) return;
  currentPhoto = (currentPhoto + delta + collection[active].images.length) % collection[active].images.length;
  updateViewer();
}}

$('close-gallery').onclick = () => gallery.close();
$('close-viewer').onclick = () => viewer.close();
$('previous').onclick = () => step(-1);
$('next').onclick = () => step(1);

viewer.addEventListener('keydown', e => {{
  if (e.key === 'ArrowRight') {{ e.preventDefault(); step(1); }}
  if (e.key === 'ArrowLeft') {{ e.preventDefault(); step(-1); }}
}});

// Mobile swipe support for viewer
let touchStartX = 0, touchEndX = 0;
viewer.addEventListener('touchstart', e => {{
  touchStartX = e.changedTouches[0].screenX;
}}, {{ passive: true }});
viewer.addEventListener('touchend', e => {{
  touchEndX = e.changedTouches[0].screenX;
  if (touchEndX < touchStartX - 50) {{ step(1); }}
  if (touchEndX > touchStartX + 50) {{ step(-1); }}
}}, {{ passive: true }});

gallery.addEventListener('click', e => {{
  if (e.target === gallery) {{
    const r = gallery.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) gallery.close();
  }}
}});

gallery.addEventListener('close', () => {{
  document.body.classList.remove('modal-open');
  lastCategory?.focus({{ preventScroll: true }});
}});

viewer.addEventListener('close', () => lastPhoto?.focus({{ preventScroll: true }}));
</script>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Save JSON data
    json_path = os.path.join(os.path.dirname(output_path) or '.', 'catalog_data.json')
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(collection, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return output_path

def main():
    collection, total = scan_catalog_data('.')
    generate_catalog_html(collection, total, 'index.html')
    print(f"✨ Generated Oopsie Catalog: index.html ({len(collection)} categories, {total} items)")

if __name__ == '__main__':
    main()
