#!/usr/bin/env python3
"""
Oopsie Handcrafted Studio - Live Mobile Server & Auto-Sync Engine
- Serves the cute catalog on your local Wi-Fi network so phones can open it
- Watches the project directory in real-time
- Adding any new folder or dropping photos instantly creates a new category
  and updates the catalog with 0 manual steps!
"""

import http.server
import socketserver
import socket
import webbrowser
import os
import sys
import time
import json
import threading
import urllib.parse
import subprocess
from generate_catalog import scan_catalog_data, generate_catalog_html, get_categories_dir, organize_root_categories

_rebuild_lock = threading.Lock()
_last_fingerprint = None
_last_counts = (0, 0)

def get_catalog_fingerprint(base_dir='.'):
    """
    Computes a fast fingerprint of all category folders and image files.
    Monitors 'oppsie categories' and its subdirectories, as well as root directories.
    Detects:
    - Added, deleted, or renamed category folders (in oppsie categories or root)
    - Added, deleted, or modified image files inside category folders
    """
    cat_dir, prefix = get_categories_dir(base_dir)
    items = []

    # 1. Check root directory for any newly created folder from Google Drive / Finder
    try:
        base_stat = os.stat(base_dir)
        items.append(('__root__', base_stat.st_mtime))
        ignored = {
            'oppsie categories', 'oopsie categories', 'categories',
            '.git', '.github', '.tmp.driveupload', '.tmp.drivedownload',
            '__pycache__', 'scratch', 'node_modules', '.gemini', '.vscode', '.idea'
        }
        for entry in os.listdir(base_dir):
            if entry.startswith('.') or entry in ignored:
                continue
            p = os.path.join(base_dir, entry)
            if os.path.isdir(p):
                try:
                    s = os.stat(p)
                    items.append(('__root_sub__', entry, s.st_mtime))
                except OSError:
                    pass
    except OSError:
        pass

    # 2. Check main categories directory
    try:
        cat_dir_stat = os.stat(cat_dir)
        items.append(('__cat_dir__', cat_dir_stat.st_mtime))

        entries = sorted(os.listdir(cat_dir))
        for entry in entries:
            if entry.startswith('.'):
                continue
            entry_path = os.path.join(cat_dir, entry)
            if os.path.isdir(entry_path):
                try:
                    stat = os.stat(entry_path)
                    items.append((entry, stat.st_mtime))
                    files = sorted(os.listdir(entry_path))
                    for f in files:
                        if not f.startswith('.') and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.heic', '.avif')):
                            f_path = os.path.join(entry_path, f)
                            try:
                                f_stat = os.stat(f_path)
                                items.append((entry, f, f_stat.st_mtime, f_stat.st_size))
                            except OSError:
                                pass
                except OSError:
                    pass
    except OSError:
        pass
    return tuple(items)

def git_sync_push(base_dir='.'):
    """
    Automatically commits and pushes changes to GitHub origin main
    so the live website updates in real time.
    """
    try:
        status = subprocess.run(['git', 'status', '--porcelain'], cwd=base_dir, capture_output=True, text=True)
        if not status.stdout.strip():
            return False

        print("🌸 [Live Sync] Detected new files! Staging changes...")
        subprocess.run(['git', 'add', '-A'], cwd=base_dir, check=True)

        msg = f"Auto-sync: update categories & products ({time.strftime('%Y-%m-%d %H:%M:%S')})"
        subprocess.run(['git', 'commit', '-m', msg], cwd=base_dir, capture_output=True, text=True)

        print("🚀 [Live Sync] Pushing to GitHub (origin main)...")
        push_res = subprocess.run(['git', 'push', 'origin', 'main'], cwd=base_dir, capture_output=True, text=True, timeout=90)
        if push_res.returncode == 0:
            print("✨ [Live Sync] Successfully published to GitHub! Live website updated.")
            return True
        else:
            print(f"⚠️ [Live Sync] Push output: {push_res.stderr.strip() or push_res.stdout.strip()}")
            return False
    except Exception as err:
        print(f"⚠️ [Live Sync] Git push notice: {err}")
        return False

def sync_catalog(base_dir='.', force=False, verbose=True):
    """
    Scans the directory and rebuilds index.html if any changes are detected.
    Thread-safe.
    """
    global _last_fingerprint, _last_counts
    with _rebuild_lock:
        current_fp = get_catalog_fingerprint(base_dir)
        if not force and current_fp == _last_fingerprint:
            return False, _last_counts[0], _last_counts[1]

        cats, total = scan_catalog_data(base_dir)
        output_path = os.path.join(base_dir, 'index.html')
        generate_catalog_html(cats, total, output_path)

        # Also save catalog_data.json
        try:
            with open(os.path.join(base_dir, 'catalog_data.json'), 'w', encoding='utf-8') as f:
                json.dump(cats, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        _last_fingerprint = get_catalog_fingerprint(base_dir)
        _last_counts = (len(cats), total)

        if verbose:
            print(f"🌸 [Auto-Sync] Catalog updated! {len(cats)} categories, {total} products ready.")

        return True, len(cats), total

def folder_watcher_thread(base_dir='.', auto_push=True):
    """
    Background daemon thread that continuously monitors for folder / image changes.
    When changes occur (e.g. from Google Drive sync or Finder):
    1. Debounces for 3 seconds to let file transfer finish
    2. Rebuilds index.html and catalog_data.json
    3. Pushes to GitHub so the live site updates in real time!
    """
    last_seen_fp = get_catalog_fingerprint(base_dir)
    while True:
        try:
            time.sleep(1.5)
            curr_fp = get_catalog_fingerprint(base_dir)
            if curr_fp != last_seen_fp:
                # Changes detected! Debounce to let Google Drive or file download finish
                time.sleep(3.0)
                # Re-check fingerprint after settling
                settled_fp = get_catalog_fingerprint(base_dir)
                last_seen_fp = settled_fp

                updated, cats, prods = sync_catalog(base_dir, force=True, verbose=True)
                if updated and auto_push:
                    git_sync_push(base_dir)
        except Exception as e:
            time.sleep(2.0)

class OopsieHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler with:
    - Auto-rebuild check on page reload (guarantees real-time accuracy)
    - Anti-caching headers for HTML so mobile browsers show updates immediately
    - JSON API endpoint for catalog status
    """
    def end_headers(self):
        # Prevent mobile Safari/Chrome from aggressively caching the HTML
        if self.path in ('/', '/index.html', '/index.htm', '/api/status'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        clean_path = urllib.parse.urlparse(self.path).path

        # Serve logo for favicon
        if clean_path == '/favicon.ico':
            self.path = '/logo.png'
            return super().do_GET()

        # Handle API status query
        if clean_path == '/api/status':
            sync_catalog('.', force=False, verbose=False)
            cats_count, prods_count = _last_counts
            body = json.dumps({'status': 'ok', 'categories': cats_count, 'products': prods_count}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # When reloading the catalog page, ensure it is up-to-date
        if clean_path in ('/', '/index.html', '/index.htm'):
            sync_catalog('.', force=False, verbose=True)

        return super().do_GET()

    def log_message(self, format, *args):
        # Suppress noisy image GET logs; only show important errors or page loads
        if len(args) >= 1 and ('GET / ' in str(args[0]) or 'GET /index.html' in str(args[0])):
            print(f"📱 Client loaded catalog: {args[0]}")
        elif len(args) >= 2 and str(args[1]) not in ('200', '304'):
            super().log_message(format, *args)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def find_available_port(start_port=8080, max_attempts=20):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def run_server():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Initial sync on startup
    print("\n🌸 Initializing Oopsie Catalog...")
    sync_catalog('.', force=True, verbose=True)

    # Start background folder watcher with GitHub live sync enabled
    watcher = threading.Thread(target=folder_watcher_thread, args=('.', True), daemon=True)
    watcher.start()

    port = find_available_port(8080)
    local_ip = get_local_ip()

    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(('0.0.0.0', port), OopsieHTTPRequestHandler) as httpd:
            desktop_url = f"http://localhost:{port}"
            mobile_url = f"http://{local_ip}:{port}"
            github_url = "https://miku1113.github.io/oopsie/"

            print("\n" + "🌸 " + "=" * 60 + " 🌸")
            print("        OOPSIE HANDCRAFTED STUDIO • REAL-TIME LIVE SYNC")
            print("🌸 " + "=" * 60 + " 🌸")
            print(f"🌍 Live Website URL:  {github_url}")
            print(f"💻 Local Desktop URL: {desktop_url}")
            print(f"📱 Local Wi-Fi URL:   {mobile_url}")
            print("=" * 64)
            print("✨ Real-Time Google Drive & GitHub Sync is ACTIVE!")
            print("   • Adding any folder in Google Drive or Finder:")
            print("     -> Automatically creates new category & products")
            print("     -> Automatically pushes to GitHub & updates live site in real time!")
            print("   • Deleting any folder:")
            print("     -> Automatically removes it from the catalog & live site!")
            print("=" * 64)
            print("Press Ctrl+C to stop the server anytime.\n")

            # Try opening on desktop
            try:
                webbrowser.open(desktop_url)
            except Exception:
                pass

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🌸 Server stopped. Have a wonderful day!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_server()
