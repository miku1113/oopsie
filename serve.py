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
from generate_catalog import scan_catalog_data, generate_catalog_html, get_categories_dir

_rebuild_lock = threading.Lock()
_last_fingerprint = None
_last_counts = (0, 0)

def get_catalog_fingerprint(base_dir='.'):
    """
    Computes a fast fingerprint of all category folders and image files.
    Monitors 'oppsie categories' and its subdirectories.
    Detects:
    - Added, deleted, or renamed category folders
    - Added, deleted, or modified image files inside category folders
    """
    cat_dir, prefix = get_categories_dir(base_dir)
    items = []
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

        _last_fingerprint = current_fp
        _last_counts = (len(cats), total)

        if verbose:
            print(f"🌸 [Auto-Sync] Catalog updated! {len(cats)} categories, {total} products ready.")

        return True, len(cats), total

def folder_watcher_thread(base_dir='.'):
    """
    Background daemon thread that continuously monitors for folder / image changes.
    """
    while True:
        try:
            time.sleep(1.0)
            sync_catalog(base_dir, force=False, verbose=True)
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

    # Start background folder watcher
    watcher = threading.Thread(target=folder_watcher_thread, args=('.',), daemon=True)
    watcher.start()

    port = find_available_port(8080)
    local_ip = get_local_ip()

    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(('0.0.0.0', port), OopsieHTTPRequestHandler) as httpd:
            desktop_url = f"http://localhost:{port}"
            mobile_url = f"http://{local_ip}:{port}"

            print("\n" + "🌸 " + "=" * 58 + " 🌸")
            print("        OOPSIE HANDCRAFTED STUDIO • LIVE MOBILE SERVER")
            print("🌸 " + "=" * 58 + " 🌸")
            print(f"💻 Desktop URL:       {desktop_url}")
            print(f"📱 Mobile Phone URL:  {mobile_url}")
            print("=" * 62)
            print("✨ Real-Time Folder Detection is ACTIVE on 'oppsie categories'!")
            print("👉 Open the 'oppsie categories' folder in Finder:")
            print("   • Add any new folder  -> instantly appears as a new category!")
            print("   • Delete any folder   -> instantly removed from the catalog!")
            print("   • Live auto-reload is active on both laptop & mobile!")
            print("=" * 62)
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
