#!/usr/bin/env python3
"""
OOPSIE — Little things, happy feelings
Catalog store + static site generator.

The repo is the single source of truth:
- catalog.json  : categories, products and the photos inside them
- images/       : every photo, named by content hash (e.g. images/6cc2e0b0dd8dad73.jpeg)

Run `python3 generate_catalog.py` to rebuild index.html from catalog.json.
Edit the catalog with the admin page (`python3 serve.py`, then open /admin.html).
"""

import html
import json
import os
import re

CATALOG_FILE = 'catalog.json'
IMAGES_DIR = 'images'
IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif')
IMAGE_PATH_RE = re.compile(r'^images/[A-Za-z0-9_-]+\.(?:jpg|jpeg|png|webp|gif|avif)$')
ID_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,63}$')


class CatalogError(ValueError):
    pass


def load_catalog(base_dir='.'):
    with open(os.path.join(base_dir, CATALOG_FILE), encoding='utf-8') as f:
        return json.load(f)


def catalog_images(catalog):
    """Every image path referenced by the catalog, in display order."""
    for cat in catalog['categories']:
        for product in cat['products']:
            yield from product['images']
        yield from cat['images']


def validate_catalog(catalog, base_dir='.'):
    """Raise CatalogError if the catalog is malformed or points at missing files."""
    if not isinstance(catalog, dict) or not isinstance(catalog.get('categories'), list):
        raise CatalogError('catalog must be an object with a "categories" list')

    ids, seen_images = set(), set()

    def check_id(value, what):
        if not isinstance(value, str) or not ID_RE.match(value):
            raise CatalogError(f'{what} has an invalid id: {value!r}')
        if value in ids:
            raise CatalogError(f'duplicate id: {value}')
        ids.add(value)

    def check_name(value, what):
        if not isinstance(value, str) or not value.strip() or len(value) > 120:
            raise CatalogError(f'{what} needs a name (1-120 characters)')

    def check_images(images, what):
        if not isinstance(images, list):
            raise CatalogError(f'{what} images must be a list')
        for path in images:
            if not isinstance(path, str) or not IMAGE_PATH_RE.match(path):
                raise CatalogError(f'{what} has an invalid image path: {path!r}')
            if path in seen_images:
                raise CatalogError(f'image is listed twice: {path}')
            if not os.path.isfile(os.path.join(base_dir, path)):
                raise CatalogError(f'image file does not exist: {path}')
            seen_images.add(path)

    for cat in catalog['categories']:
        if not isinstance(cat, dict):
            raise CatalogError('each category must be an object')
        check_id(cat.get('id'), 'category')
        check_name(cat.get('name'), 'category')
        if not isinstance(cat.get('products'), list):
            raise CatalogError(f'category {cat["id"]} products must be a list')
        for product in cat['products']:
            if not isinstance(product, dict):
                raise CatalogError('each product must be an object')
            check_id(product.get('id'), 'product')
            check_name(product.get('name'), 'product')
            check_images(product.get('images'), f'product {product["id"]}')
        check_images(cat.get('images'), f'category {cat["id"]}')


def clean_catalog(catalog):
    """Return only the known fields, with trimmed names."""
    return {
        'version': 1,
        'categories': [
            {
                'id': cat['id'],
                'name': cat['name'].strip(),
                'products': [
                    {'id': p['id'], 'name': p['name'].strip(), 'images': list(p['images'])}
                    for p in cat['products']
                ],
                'images': list(cat['images']),
            }
            for cat in catalog['categories']
        ],
    }


def save_catalog(catalog, base_dir='.'):
    """Validate, write catalog.json atomically, and rebuild index.html."""
    validate_catalog(catalog, base_dir)
    catalog = clean_catalog(catalog)
    path = os.path.join(base_dir, CATALOG_FILE)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write('\n')
    os.replace(tmp, path)
    generate_catalog_html(catalog, os.path.join(base_dir, 'index.html'))
    return catalog


def public_categories(catalog):
    """Categories that have at least one photo, as shown on the public site."""
    return [
        cat for cat in catalog['categories']
        if cat['images'] or any(p['images'] for p in cat['products'])
    ]


def item_count(cat):
    """Tiles a visitor sees in a category: products with photos + unsorted photos."""
    return sum(1 for p in cat['products'] if p['images']) + len(cat['images'])


def generate_catalog_html(catalog, output_path='index.html'):
    cats = public_categories(catalog)
    buttons = '\n'.join(
        f'<button class="category" aria-haspopup="dialog" onclick="openGallery({i}, this)">'
        f'<span class="name">{html.escape(cat["name"])}</span>'
        f'<span class="count" aria-label="{item_count(cat)} items">{item_count(cat)}</span></button>'
        for i, cat in enumerate(cats)
    )
    data_json = json.dumps({'version': 1, 'categories': cats}, ensure_ascii=False).replace('<', '\\u003c')
    page = (
        HTML_TEMPLATE
        .replace('__CATEGORY_BUTTONS__', buttons)
        .replace('__CATEGORY_COUNT__', str(len(cats)))
        .replace('__CATALOG_JSON__', data_json)
    )
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(page)
    return output_path


HTML_TEMPLATE = r"""<!doctype html>
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
:root{--paper:#716c4a;--ink:#fff8ea;--quiet:#f2ecda;--pink:#f6a499;--sage:#abbfb6;--blue:#557dca;--line:#928d6b;--white:#716c4a;--surface:#625e40;--brand-burgundy:#662020;--focus:#ffceb7;color-scheme:dark;font-family:'Avenir Next',Avenir,'Trebuchet MS',sans-serif;color:var(--ink);background:var(--paper)}*{box-sizing:border-box}body{margin:0}button{font:inherit;color:inherit;cursor:pointer}button:focus-visible{outline:3px solid var(--focus);outline-offset:5px}button{ -webkit-tap-highlight-color:transparent}::selection{background:var(--pink);color:var(--brand-burgundy)}.index{max-width:1120px;margin:auto;padding:38px 64px 30px;min-height:100dvh;display:flex;flex-direction:column}.masthead{display:flex;justify-content:center;position:relative}.logo{width:auto;height:96px;max-width:240px;object-fit:contain}.small-note{position:absolute;right:0;top:32px;font-size:12px;color:var(--quiet)}.intro{text-align:center;margin:36px auto 38px;max-width:650px}.intro h1{font-family:'Palatino Linotype',Palatino,'Book Antiqua',serif;font-weight:400;letter-spacing:-1.8px;font-size:clamp(35px,4.2vw,54px);line-height:1.12;margin:0 0 16px}.intro p{font-size:14px;line-height:1.8;color:var(--quiet);margin:0}.categories{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px 18px}.category{position:relative;border:1px solid transparent;border-bottom-color:var(--line);background:transparent;min-height:59px;padding:13px 14px;display:flex;align-items:center;text-align:left;gap:14px;border-radius:9px;transition:background .2s,border-color .2s,transform .2s}.category:hover{color:var(--brand-burgundy);background:var(--pink);border-color:var(--pink);transform:translateY(-2px)}.category .name{font-size:14px;line-height:1.4;flex:1}.count{font-size:11px;color:var(--quiet);background:var(--surface);width:25px;height:25px;border-radius:50%;display:grid;place-items:center;flex:none}.category:hover .count{background:#fff0dc;color:var(--brand-burgundy)}.end{display:flex;align-items:center;justify-content:space-between;gap:20px;font-size:11px;color:var(--quiet);margin-top:auto;padding-top:40px}.dots{display:flex;gap:6px}.dots i{width:7px;height:7px;border-radius:50%;background:var(--sage)}.dots i:nth-child(2){background:var(--brand-burgundy)}.dots i:nth-child(3){background:var(--pink)}.dots i:nth-child(4){background:#f77916}.dots i:nth-child(5){background:var(--blue)}dialog{border:0;padding:0;color:var(--ink);max-width:none;max-height:none}dialog::backdrop{background:rgba(35,33,21,.55);backdrop-filter:blur(9px)}.gallery{width:min(1160px,calc(100% - 64px));height:calc(100dvh - 64px);border-radius:24px;background:var(--white);box-shadow:0 24px 90px #211e194d;overflow:hidden}.gallery[open]{display:flex;flex-direction:column;animation:arrive .3s ease-out}.gallery-head{padding:26px 36px 24px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;flex:none}.gallery-heading{flex:1;min-width:0}.gallery-heading h2{font-family:Palatino,'Book Antiqua',serif;font-size:32px;font-weight:400;letter-spacing:-.7px;margin:0 0 5px}.gallery-heading p{font-size:12px;color:var(--quiet);margin:0}.close{border:1px solid var(--line);background:transparent;border-radius:100px;min-height:42px;padding:9px 17px;font-size:12px;white-space:nowrap}.close:hover{background:var(--surface)}.photos{overflow:auto;overscroll-behavior:contain;padding:30px 36px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));align-content:start;gap:28px 22px}.photo{border:0;padding:0;background:none;text-align:left;min-width:0}.image-wrap{position:relative;height:310px;border-radius:12px;background:var(--surface);overflow:hidden;display:flex;align-items:center;justify-content:center}.photo img{height:100%;width:100%;object-fit:contain;transition:transform .35s}.photo:hover img{transform:scale(1.025)}.stack{position:absolute;right:10px;bottom:10px;font-size:11px;background:rgba(35,33,21,.7);color:var(--ink);border-radius:100px;padding:4px 10px}.caption{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 2px;font-size:11px;color:var(--quiet)}.caption .title{font-size:13px;color:var(--ink)}.caption span:last-child{font-size:17px;color:var(--ink)}.viewer{background:var(--paper);width:100%;height:100dvh;overflow:hidden}.viewer[open]{display:flex;flex-direction:column}.viewer-head{display:flex;justify-content:space-between;align-items:center;padding:20px 30px;gap:20px}.viewer-head p{font-size:13px;margin:0}.viewer-stage{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;position:relative;padding:10px 80px 30px}.viewer-stage img{display:block;max-width:100%;max-height:100%;object-fit:contain;border-radius:5px}.step{position:absolute;top:50%;width:44px;height:44px;border:1px solid var(--line);border-radius:50%;background:var(--surface);font-size:24px;display:grid;place-items:center}.step[hidden]{display:none}.previous{left:20px}.next{right:20px}.viewer-foot{text-align:center;font-size:11px;color:var(--quiet);padding:0 20px 18px}.empty{padding:30px}body.modal-open{overflow:hidden}@keyframes arrive{from{opacity:0;transform:translateY(18px) scale(.985)}to{opacity:1;transform:none}}@media(min-width:1450px){.index{padding-top:55px;padding-bottom:40px}.intro{margin-top:45px;margin-bottom:45px}.category{min-height:65px}}@media(max-width:800px){.index{padding:28px 28px 24px}.small-note{display:none}.categories{gap:6px 12px;grid-template-columns:repeat(2,minmax(0,1fr))}.intro{margin:28px auto}.category{min-height:58px;padding:10px}.gallery{width:calc(100% - 24px);height:calc(100dvh - 24px);border-radius:18px}.gallery-head{padding:20px 24px}.gallery-heading h2{font-size:27px}.photos{grid-template-columns:repeat(2,minmax(0,1fr));padding:24px;gap:16px}.image-wrap{height:300px}.end{padding-top:32px}}@media(max-width:480px){.index{padding:23px 18px}.logo{width:auto;height:80px;max-width:180px}.intro{margin:25px auto 26px}.intro h1{font-size:37px;letter-spacing:-1.3px}.intro p{font-size:12px;max-width:260px;margin:auto}.categories{gap:4px 8px}.category{padding:10px 6px;gap:7px;min-height:60px}.category .name{font-size:12px}.count{width:21px;height:21px;font-size:10px}.end{font-size:10px}.gallery-head{padding:20px 18px;gap:10px;align-items:flex-start}.gallery-heading h2{font-size:26px}.gallery-head .close{font-size:11px;padding:8px 12px;min-height:38px}.photos{padding:18px;gap:16px 12px}.image-wrap{height:225px;border-radius:8px}.caption{font-size:10px}.caption .title{font-size:11px}.viewer-head{padding:16px}.viewer-stage{padding:8px 10px 75px}.step{top:auto;bottom:12px}.previous{left:calc(50% - 55px)}.next{right:calc(50% - 55px)}}@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}

/* 5-dot wave preloader */
.preloader{position:fixed;inset:0;z-index:999999;background:var(--paper);display:flex;align-items:center;justify-content:center;opacity:1;visibility:visible;transition:opacity .4s cubic-bezier(.4,0,.2,1),visibility .4s ease}
.preloader.hidden{opacity:0;visibility:hidden;pointer-events:none}
.wave-dots{display:flex;align-items:center;justify-content:center;gap:14px}
.wave-dots i{width:15px;height:15px;border-radius:50%;display:block;animation:dotWave 1.35s ease-in-out infinite}
.wave-dots i:nth-child(1){background:var(--sage);animation-delay:0s}
.wave-dots i:nth-child(2){background:var(--brand-burgundy);animation-delay:.15s}
.wave-dots i:nth-child(3){background:var(--pink);animation-delay:.3s}
.wave-dots i:nth-child(4){background:#f77916;animation-delay:.45s}
.wave-dots i:nth-child(5){background:var(--blue);animation-delay:.6s}
@keyframes dotWave{0%,100%{transform:translateY(0);opacity:.55}32%{transform:translateY(-16px);opacity:1}}
</style>
</head>
<body>
<div id="preloader" class="preloader" aria-label="Loading Oopsie...">
  <div class="wave-dots" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
</div>

<main class="index">
<header class="masthead"><img class="logo" src="logo.png?v=2" alt="OOPSIE"><span class="small-note">The collection</span></header>
<div class="intro"><h1>Little things.<br>Happy feelings.</h1><p>A world of colour, charm and everyday joy.<br>Pick a category. Find something that makes you smile.</p></div>
<nav class="categories" aria-label="Product categories" id="categories">__CATEGORY_BUTTONS__</nav>
<footer class="end"><span>__CATEGORY_COUNT__ categories to fall in love with.</span><span class="dots" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span><span>A little world of OOPSIE.</span></footer>
</main>
<dialog class="gallery" id="gallery" aria-labelledby="gallery-title"><header class="gallery-head"><div class="gallery-heading"><h2 id="gallery-title"></h2><p id="gallery-meta"></p></div><button class="close" id="close-gallery" autofocus>All categories <span aria-hidden="true">×</span></button></header><div class="photos" id="photos"></div></dialog>
<dialog class="viewer" id="viewer" aria-label="Full-size photo viewer"><header class="viewer-head"><p id="viewer-label" aria-live="polite"></p><button class="close" id="close-viewer" autofocus>Back to gallery ×</button></header><div class="viewer-stage"><img id="full-image" alt=""><button class="step previous" id="previous" aria-label="Previous photo">‹</button><button class="step next" id="next" aria-label="Next photo">›</button></div><div class="viewer-foot">Use the arrow keys to browse. Press Esc to go back.</div></dialog>
<script>
let collection = (__CATALOG_JSON__).categories;
const $ = id => document.getElementById(id);
const gallery = $('gallery'), viewer = $('viewer'), preloader = $('preloader');
let active = 0, lastCategory = null, lastPhoto = null;
// The photo set the viewer is browsing: {title, images, index}
let viewing = { title: '', images: [], index: 0 };

function dismissPreloader() {
  if (!preloader || preloader.classList.contains('hidden')) return;
  preloader.classList.add('hidden');
  setTimeout(() => { preloader.style.display = 'none'; }, 500);
}
const loadStartTime = Date.now();
function finishLoading() {
  setTimeout(dismissPreloader, Math.max(0, 650 - (Date.now() - loadStartTime)));
}

function visibleCategories(categories) {
  return categories.filter(c => c.images.length || c.products.some(p => p.images.length));
}
function itemCount(c) {
  return c.products.filter(p => p.images.length).length + c.images.length;
}

function renderCategoriesList(items) {
  const container = $('categories');
  if (!container) return;
  container.replaceChildren();
  items.forEach((category, index) => {
    const button = document.createElement('button');
    button.className = 'category';
    button.setAttribute('aria-haspopup', 'dialog');
    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = category.name;
    const count = document.createElement('span');
    count.className = 'count';
    count.textContent = itemCount(category);
    count.setAttribute('aria-label', itemCount(category) + ' items');
    button.append(name, count);
    button.addEventListener('click', () => openGallery(index, button));
    container.append(button);
  });
  const countSpan = document.querySelector('.end span:first-child');
  if (countSpan) countSpan.textContent = items.length + ' categories to fall in love with.';
}

// Pick up catalog changes published while the page is open.
function fetchLatestCatalog(isInitial = false) {
  fetch('catalog.json?t=' + Date.now(), { cache: 'no-store' })
    .then(res => { if (!res.ok) throw new Error('HTTP ' + res.status); return res.json(); })
    .then(data => {
      const latest = visibleCategories(data.categories || []);
      if (JSON.stringify(latest) !== JSON.stringify(collection)) {
        collection = latest;
        renderCategoriesList(collection);
      }
    })
    .catch(() => {})
    .finally(() => { if (isInitial) finishLoading(); });
}
fetchLatestCatalog(true);
setInterval(() => fetchLatestCatalog(false), 4000);
window.addEventListener('load', finishLoading);
setTimeout(dismissPreloader, 3500);

function tile(src, alt, title, meta, isProduct, eager, onOpen) {
  const button = document.createElement('button');
  button.className = 'photo';
  button.setAttribute('aria-label', 'View ' + alt);
  const wrap = document.createElement('span');
  wrap.className = 'image-wrap';
  const img = document.createElement('img');
  img.src = src;
  img.alt = alt;
  img.loading = eager ? 'eager' : 'lazy';
  img.decoding = 'async';
  wrap.append(img);
  if (meta) {
    const stack = document.createElement('span');
    stack.className = 'stack';
    stack.textContent = meta;
    wrap.append(stack);
  }
  const caption = document.createElement('span');
  caption.className = 'caption';
  const label = document.createElement('span');
  label.textContent = title;
  if (isProduct) label.className = 'title';
  const icon = document.createElement('span');
  icon.textContent = '＋';
  icon.setAttribute('aria-hidden', 'true');
  caption.append(label, icon);
  button.append(wrap, caption);
  button.addEventListener('click', () => { lastPhoto = button; onOpen(); });
  return button;
}

function openGallery(index, trigger) {
  active = index;
  lastCategory = trigger;
  const c = collection[index];
  if (!c) return;
  const products = c.products.filter(p => p.images.length);
  $('gallery-title').textContent = c.name;
  const parts = [];
  if (products.length) parts.push(products.length + (products.length === 1 ? ' product' : ' products'));
  if (c.images.length) parts.push(c.images.length + (c.images.length === 1 ? ' photo' : ' photos'));
  $('gallery-meta').textContent = parts.join(' · ') + ' · Select one for a closer look';
  const photos = $('photos');
  photos.replaceChildren();
  let n = 0;
  products.forEach(p => {
    const meta = p.images.length > 1 ? p.images.length + ' photos' : '';
    photos.append(tile(p.images[0], p.name, p.name, meta, true, n++ < 6, () => openViewer(p.name, p.images, 0)));
  });
  c.images.forEach((src, i) => {
    photos.append(tile(src, c.name + ' — photo ' + (i + 1), 'Photo ' + String(i + 1).padStart(2, '0'), '', false, n++ < 6,
      () => openViewer(c.name, c.images, i)));
  });
  gallery.showModal();
  document.body.classList.add('modal-open');
  photos.scrollTop = 0;
}

function openViewer(title, images, index) {
  viewing = { title, images, index };
  updateViewer();
  viewer.showModal();
}

function updateViewer() {
  const { title, images, index } = viewing;
  $('full-image').src = images[index];
  $('full-image').alt = title + ' — photo ' + (index + 1);
  $('viewer-label').textContent = title + ' · ' + (index + 1) + ' / ' + images.length;
  $('previous').hidden = $('next').hidden = images.length < 2;
}

function step(delta) {
  const len = viewing.images.length;
  if (len < 2) return;
  viewing.index = (viewing.index + delta + len) % len;
  updateViewer();
}

$('close-gallery').onclick = () => gallery.close();
$('close-viewer').onclick = () => viewer.close();
$('previous').onclick = () => step(-1);
$('next').onclick = () => step(1);

viewer.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
});

let touchStartX = 0;
viewer.addEventListener('touchstart', e => { touchStartX = e.changedTouches[0].screenX; }, { passive: true });
viewer.addEventListener('touchend', e => {
  const touchEndX = e.changedTouches[0].screenX;
  if (touchEndX < touchStartX - 50) step(1);
  if (touchEndX > touchStartX + 50) step(-1);
}, { passive: true });

gallery.addEventListener('click', e => {
  if (e.target === gallery) {
    const r = gallery.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) gallery.close();
  }
});
gallery.addEventListener('close', () => {
  document.body.classList.remove('modal-open');
  lastCategory?.focus({ preventScroll: true });
});
viewer.addEventListener('close', () => lastPhoto?.focus({ preventScroll: true }));
</script>
</body>
</html>
"""


def main():
    catalog = load_catalog('.')
    validate_catalog(catalog, '.')
    generate_catalog_html(catalog, 'index.html')
    cats = public_categories(catalog)
    total = sum(1 for _ in catalog_images(catalog))
    print(f'✨ Generated Oopsie Catalog: index.html ({len(cats)} categories, {total} photos)')


if __name__ == '__main__':
    main()
