#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Cyber Audio
# SPDX-License-Identifier: MIT
# Automated Batch Porter & Transpiler for MODEP & Blokas LV2 Library

import os
import sys
import json
import time
import shutil
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Automated Batch Porter for MODEP ARM Library")
    parser.add_argument("--catalog", default="scripts/modep_catalog.json", help="Path to catalog JSON")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of plugins to port (0 = all)")
    parser.add_argument("--output-dir", default="dist/universal_plugins", help="Output directory")
    parser.add_argument("--update-site", action="store_true", default=True, help="Update site/data/plugins.json")
    args = parser.parse_args()

    cat_path = os.path.abspath(args.catalog)
    if not os.path.exists(cat_path):
        print(f"ERROR: Catalog not found at {cat_path}")
        sys.exit(1)

    with open(cat_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    if args.limit > 0:
        catalog = catalog[:args.limit]

    out_base = os.path.abspath(args.output_dir)
    os.makedirs(out_base, exist_ok=True)

    print("=" * 65)
    print("  MODEP ARM -> UNIVERSAL DESKTOP & MULTI-ARCH BATCH PORTER")
    print(f"  Total Plugins in Queue: {len(catalog)}")
    print("=" * 65)

    results = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    engine_path = os.path.join(script_dir, "porter_engine.py")

    for i, plugin in enumerate(catalog):
        p_id = plugin['id']
        p_name = plugin['name']
        p_repo = plugin['repo']
        print(f"\n[{i+1}/{len(catalog)}] Processing: {p_name} ({p_id})")
        print(f"  Source: {p_repo}")

        p_out = os.path.join(out_base, p_id)
        os.makedirs(p_out, exist_ok=True)

        cmd = [
            sys.executable,
            engine_path,
            "--source", p_repo,
            "--name", p_id,
            "--theme", "copper",
            "--output-dir", p_out
        ]

        start_t = time.time()
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            elapsed = time.time() - start_t
            if res.returncode == 0:
                print(f"  ✓ Successfully ported in {elapsed:.1f}s")
                plugin_entry = dict(plugin)
                plugin_entry['version'] = "1.0.0"
                plugin_entry['platforms'] = ["Windows", "Linux", "RPi ARM32", "RPi ARM64"]
                plugin_entry['download_url'] = f"https://github.com/danny1marshall1587-maker/mod-universal-plugin-hub/releases/download/v1.0.0/{p_id}-universal-fat.lv2.zip"
                plugin_entry['github_url'] = p_repo
                plugin_entry['icon'] = "🎛️"
                results.append(plugin_entry)
            else:
                print(f"  ✕ Build notice for {p_id}: {res.stderr[:200]}")
        except Exception as e:
            print(f"  ✕ Error processing {p_id}: {e}")

    print("\n" + "=" * 65)
    print(f"  BATCH COMPLETED: {len(results)}/{len(catalog)} Plugins Ported Successfully!")
    print("=" * 65)

    # Update site/data/plugins.json
    if args.update_site:
        site_json_path = os.path.abspath("site/data/plugins.json")
        if os.path.exists(site_json_path):
            with open(site_json_path, 'r', encoding='utf-8') as sf:
                current_plugins = json.load(sf)
            
            existing_ids = {p['id'] for p in current_plugins}
            added = 0
            for r in results:
                if r['id'] not in existing_ids:
                    current_plugins.append(r)
                    added += 1

            with open(site_json_path, 'w', encoding='utf-8') as sf:
                json.dump(current_plugins, sf, indent=2)
            print(f"[+] Added {added} new ported plugins to site/data/plugins.json!")

            # Also sync to docs/data/plugins.json for GitHub Pages
            docs_json_path = os.path.abspath("docs/data/plugins.json")
            if os.path.exists(os.path.dirname(docs_json_path)):
                os.makedirs(os.path.dirname(docs_json_path), exist_ok=True)
                shutil.copy2(site_json_path, docs_json_path)
                print(f"[+] Synced to docs/data/plugins.json for live GitHub Pages!")

if __name__ == "__main__":
    main()
