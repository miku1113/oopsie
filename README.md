# OOPSIE catalog

The product catalog website for OOPSIE, hosted on GitHub Pages at <https://miku1113.github.io/oopsie/>.

Everything the site shows lives in this repo:

| Path | What it is |
|---|---|
| `catalog.json` | Categories, the products inside each category, which photos belong where, and the Trash. This is the single source of truth. |
| `images/` | Every photo. Files are named by a hash of their content, so the same photo is never stored twice. |
| `index.html` | The public page. It is generated from `catalog.json`; do not edit it by hand. |
| `admin.html` | The admin page for editing the catalog. |

## Edit the catalog

1. Double-click `start_server.command` (or run `python3 serve.py`). The admin page opens at `http://localhost:8080/admin.html`.
2. In the admin page you can:
   - add, rename, reorder (↑ ↓) and delete **categories**;
   - add, rename, reorder and delete **products** inside a category;
   - **upload** photos with "Upload photos", or by dropping files from your computer onto any box;
   - **move photos into a product**: drag them onto the product box, or use a photo's `⋯` menu → "Move to", or select several photos and use "Move selected to…" / "New product from selection";
   - move photos to another category (drag them onto the category on the left, or use the menus);
   - set a product's cover photo (`⋯` → "Make cover photo", or drag a photo in front of the first one);
   - delete photos (they go to **Trash**, see below).
3. Every change is saved straight away to `catalog.json` and `images/`, and `index.html` is rebuilt.
4. Click **Publish** to commit those files and push them. GitHub Pages updates the live site a minute or two later.

Deleting never removes photo files from the repo. Deleted photos (including the photos of a deleted category) move to **Trash** in the sidebar: they stay in `images/`, are hidden from the site, and remember where they came from. **Restore** puts a photo back in its category and product, recreating either one if it was deleted too.

On the public site, opening a product (or a category's photos) shows the big photo with all the other photos as thumbnails on the left, like a shop product page. On phones the thumbnails are a row under the photo.

The admin page only works with the local server. On the live site it shows a short note instead.

On the public site, each product appears as one tile with its cover photo; opening it shows all of its photos. Photos that are not in a product ("Unsorted") appear as single photos. Categories without photos are hidden.

## Other tools

- `python3 generate_catalog.py` rebuilds `index.html` from `catalog.json` (GitHub Actions runs this on every push to `main`).
- `update_catalog.command` rebuilds and publishes without opening the admin page.
