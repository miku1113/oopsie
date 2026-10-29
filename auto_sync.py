#!/usr/bin/env python3
"""
Oopsie Handcrafted Studio - Dedicated Real-Time Sync Daemon
- Watches 'oppsie categories' and project root in real-time
- Detects new folders / photos added via Google Drive, Mac Finder, or Mobile Drive app
- Automatically reorganizes, rebuilds index.html, and pushes live to GitHub!
"""

import os
import sys
import time
import subprocess
from generate_catalog import scan_catalog_data, generate_catalog_html, get_categories_dir, organize_root_categories
from serve import get_catalog_fingerprint, sync_catalog, git_sync_push

def run_sync_daemon():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("\n" + "🌸 " + "=" * 60 + " 🌸")
    print("      OOPSIE REAL-TIME GOOGLE DRIVE & GITHUB SYNC ENGINE")
    print("🌸 " + "=" * 60 + " 🌸")
    print("🌍 Live Website:  https://miku1113.github.io/oopsie/")
    print("📂 Sync Folder:   oppsie categories/")
    print("☁️ Cloud Drive:   Google Drive Active")
    print("=" * 64)
    print("✨ Sync daemon is RUNNING in real time.")
    print("   Whenever you create/delete a category or add photos:")
    print("   1. Changes are detected in seconds")
    print("   2. Catalog is regenerated")
    print("   3. Automatically committed & pushed to GitHub")
    print("   4. Live website is updated automatically!")
    print("=" * 64)
    print("Press Ctrl+C to stop sync anytime.\n")

    # Initial check & sync
    updated, cats, prods = sync_catalog('.', force=True, verbose=True)
    git_sync_push('.')

    last_seen_fp = get_catalog_fingerprint('.')

    try:
        while True:
            time.sleep(2.0)
            curr_fp = get_catalog_fingerprint('.')
            if curr_fp != last_seen_fp:
                print("\n🌸 [Sync Engine] Activity detected! Waiting 3s for files to finish transfer...")
                time.sleep(3.0)
                settled_fp = get_catalog_fingerprint('.')
                last_seen_fp = settled_fp

                updated, cats, prods = sync_catalog('.', force=True, verbose=True)
                if updated:
                    git_sync_push('.')
    except KeyboardInterrupt:
        print("\n\n🌸 Sync daemon stopped. Goodbye!\n")
        sys.exit(0)

if __name__ == '__main__':
    run_sync_daemon()
