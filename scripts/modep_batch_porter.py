#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Cyber Audio
# SPDX-License-Identifier: MIT
# Master Batch Transpiler & Auto-Porter for Complete MOD & Blokas Library (700+ Plugins)

import os
import sys
import json
import time
import shutil
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Master Batch Porter for Full MOD/Blokas Library")
    parser.add_argument("--catalog", default="scripts/modep_master_catalog.json", help="Path to catalog JSON")
    parser.add_argument("--category", default="all", help="Filter by category (drive, delay, reverb, modulation, dynamics, utility, synth, all)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of suites to port (0 = all)")
    parser.add_argument("--range", default="", help="Index range to port, e.g. 0:20 or 20:40")
    parser.add_argument("--output-dir", default="dist/universal_plugins", help="Output directory")
    parser.add_argument("--update-site", action="store_true", default=True, help="Update site/data/plugins.json")
    args = parser.parse_args()

    cat_path = os.path.abspath(args.catalog)
    if not os.path.exists(cat_path):
        cat_path = os.path.abspath("scripts/modep_catalog.json")

    with open(cat_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    # Filter by category if specified
    if args.category != "all":
        catalog = [p for p in catalog if p.get('category', '').lower() == args.category.lower()]

    # Range slicing
    if args.range and ":" in args.range:
        parts = args.range.split(":")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else len(catalog)
        catalog = catalog[start:end]
    elif args.limit > 0:
        catalog = catalog[:args.limit]

    out_base = os.path.abspath(args.output_dir)
    os.makedirs(out_base, exist_ok=True)

    print("=" * 75)
    print("  MOD MASTER LIBRARY TO UNIVERSAL MULTI-ARCH BATCH PORTER (700+ PLUGINS)")
    print(f"  Category: {args.category.upper()} | Total Suites in Queue: {len(catalog)}")
    print("=" * 75)

    results = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    engine_path = os.path.join(script_dir, "porter_engine.py")

    for i, plugin in enumerate(catalog):
        p_id = plugin['id']
        p_name = plugin['name']
        p_repo = plugin['repo']
        p_cat = plugin.get('category', 'utility')
        print(f"\n[{i+1}/{len(catalog)}] Processing Suite: {p_name} ({p_id}) [{p_cat}]")
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
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
            elapsed = time.time() - start_t
            if res.returncode == 0:
                print(f"  ✓ Processed in {elapsed:.1f}s")
                plugin_entry = dict(plugin)
                plugin_entry['version'] = "1.0.0"
                plugin_entry['platforms'] = ["Windows", "Linux", "RPi ARM32", "RPi ARM64"]
                plugin_entry['download_url'] = f"https://github.com/danny1marshall1587-maker/mod-universal-plugin-hub/releases/download/v1.0.0/{p_id}-universal-fat.lv2.zip"
                plugin_entry['github_url'] = p_repo
                results.append(plugin_entry)
            else:
                first_err = res.stderr.strip().splitlines()[0] if res.stderr.strip() else "Notice"
                print(f"  ✕ Build notice for {p_id}: {first_err[:120]}")
        except Exception as e:
            print(f"  ✕ Error processing {p_id}: {e}")

    print("\n" + "=" * 75)
    print(f"  BATCH COMPLETED: {len(results)}/{len(catalog)} Suites Processed Successfully!")
    print("=" * 75)

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
            print(f"[+] Added {added} new suites to site/data/plugins.json!")

            docs_json_path = os.path.abspath("docs/data/plugins.json")
            if os.path.exists(os.path.dirname(docs_json_path)):
                os.makedirs(os.path.dirname(docs_json_path), exist_ok=True)
                shutil.copy2(site_json_path, docs_json_path)
                print(f"[+] Synced to docs/data/plugins.json for live GitHub Pages!")

if __name__ == "__main__":
    main()
