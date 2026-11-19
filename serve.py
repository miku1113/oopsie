#!/usr/bin/env python3
"""
Oopsie Handcrafted Studio - local server + catalog admin

- Serves the catalog on your Wi-Fi network so phones can open it
- /admin.html lets you add, rename, delete and reorder categories and products,
  upload and delete photos, and move photos into products (drag and drop or menu)
- Every change is saved to catalog.json + images/ in this repo and index.html is rebuilt
- "Publish" in the admin commits those files and pushes them to GitHub (live site)
"""

import hashlib
import http.server
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser

from generate_catalog import (
    CatalogError, IMAGE_EXTS, IMAGES_DIR, catalog_images, load_catalog, save_catalog,
)

MAX_UPLOAD_BYTES = 40 * 1024 * 1024
LIVE_URL = 'https://miku1113.github.io/oopsie/'
PUBLISH_PATHS = ['catalog.json', 'index.html', IMAGES_DIR]

_lock = threading.Lock()


def store_image(data, filename):
    """Save uploaded bytes under images/<content-hash>.<ext> and return the repo path."""
    ext = os.path.splitext(filename or '')[1].lower()
    if ext == '.jpe':
        ext = '.jpg'
    if ext not in IMAGE_EXTS:
        raise CatalogError(f'unsupported file type "{ext or filename}" (use {", ".join(IMAGE_EXTS)})')
    if not data:
        raise CatalogError('empty upload')
    os.makedirs(IMAGES_DIR, exist_ok=True)
    path = f'{IMAGES_DIR}/{hashlib.sha1(data).hexdigest()[:16]}{ext}'
    if not os.path.exists(path):
        tmp = path + '.part'
        with open(tmp, 'wb') as f:
            f.write(data)
        os.replace(tmp, path)
    return path


def update_catalog(new_catalog):
    """Save a full catalog. Photos that were in the old catalog but not the new one are deleted."""
    with _lock:
        before = set(catalog_images(load_catalog('.')))
        saved = save_catalog(new_catalog, '.')
        removed = before - set(catalog_images(saved))
        for path in removed:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
        return saved


def run_git(*args, timeout=60):
    return subprocess.run(['git', *args], capture_output=True, text=True, timeout=timeout)


def publish():
    """Commit catalog.json, index.html and images/ and push the current branch."""
    with _lock:
        save_catalog(load_catalog('.'), '.')
        add = run_git('add', '-A', '--', *PUBLISH_PATHS)
        if add.returncode != 0:
            return False, add.stderr.strip()
        if run_git('diff', '--cached', '--quiet', '--', *PUBLISH_PATHS).returncode == 0:
            pushed = run_git('push', 'origin', 'HEAD', timeout=120)
            if pushed.returncode != 0:
                return False, pushed.stderr.strip() or pushed.stdout.strip()
            return True, 'Nothing new to publish. The live site is up to date.'
        msg = f"Catalog update ({time.strftime('%Y-%m-%d %H:%M:%S')})"
        commit = run_git('commit', '-m', msg, '--', *PUBLISH_PATHS)
        if commit.returncode != 0:
            return False, commit.stderr.strip() or commit.stdout.strip()
        pushed = run_git('push', 'origin', 'HEAD', timeout=120)
        if pushed.returncode != 0:
            return False, 'Committed locally but the push failed: ' + (pushed.stderr.strip() or pushed.stdout.strip())
        return True, f'Published. The live site updates in a minute or two: {LIVE_URL}'


class OopsieHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ('/', '/index.html', '/admin.html', '/catalog.json') or path.startswith('/api/'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self, limit):
        length = int(self.headers.get('Content-Length') or 0)
        if length > limit:
            raise CatalogError(f'upload is too large (max {limit // (1024 * 1024)} MB)')
        return self.rfile.read(length)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == '/favicon.ico':
            self.path = '/logo.png'
        elif path == '/api/catalog':
            return self.send_json(200, load_catalog('.'))
        elif path in ('/admin', '/admin/'):
            self.path = '/admin.html'
        return super().do_GET()

    def do_PUT(self):
        if urllib.parse.urlparse(self.path).path != '/api/catalog':
            return self.send_json(404, {'error': 'not found'})
        try:
            catalog = json.loads(self.read_body(5 * 1024 * 1024) or b'null')
            return self.send_json(200, update_catalog(catalog))
        except (CatalogError, json.JSONDecodeError) as e:
            return self.send_json(400, {'error': str(e)})

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        try:
            if url.path == '/api/upload':
                name = urllib.parse.parse_qs(url.query).get('name', [''])[0]
                return self.send_json(200, {'path': store_image(self.read_body(MAX_UPLOAD_BYTES), name)})
            if url.path == '/api/publish':
                ok, message = publish()
                return self.send_json(200 if ok else 500, {'ok': ok, 'message': message})
        except CatalogError as e:
            return self.send_json(400, {'error': str(e)})
        return self.send_json(404, {'error': 'not found'})

    def log_message(self, format, *args):
        if len(args) >= 2 and str(args[1]) not in ('200', '304'):
            super().log_message(format, *args)


class ThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


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


def run_server(open_browser=True):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    save_catalog(load_catalog('.'), '.')

    port = int(os.environ.get('PORT') or find_available_port(8080))
    try:
        with ThreadingServer(('0.0.0.0', port), OopsieHandler) as httpd:
            desktop_url = f'http://localhost:{port}'
            print('\n🌸 ' + '=' * 60 + ' 🌸')
            print('        OOPSIE HANDCRAFTED STUDIO • CATALOG SERVER')
            print('🌸 ' + '=' * 60 + ' 🌸')
            print(f'🌍 Live website:   {LIVE_URL}')
            print(f'💻 Catalog:        {desktop_url}')
            print(f'🛠  Admin:          {desktop_url}/admin.html')
            print(f'📱 On your Wi-Fi:  http://{get_local_ip()}:{port}')
            print('=' * 64)
            print('Edit categories, products and photos in the admin page.')
            print('Press "Publish" there to push your changes to the live site.')
            print('Press Ctrl+C to stop the server.\n')
            if open_browser:
                try:
                    webbrowser.open(desktop_url + '/admin.html')
                except Exception:
                    pass
            httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n\n🌸 Server stopped. Have a wonderful day!\n')
        sys.exit(0)


if __name__ == '__main__':
    run_server(open_browser='--no-browser' not in sys.argv)
