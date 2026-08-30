#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Cyber Audio
# SPDX-License-Identifier: MIT
# Master Scraper for Complete MOD & Blokas Plugin Library (700+ Plugins)

import os
import sys
import json
import re
import urllib.request
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

CATEGORY_MAP = {
    'delay': ['delay', 'echo', 'tap', 'bollie', 'space'],
    'reverb': ['reverb', 'verb', 'room', 'hall', 'plate', 'shimmer', 'convo', 'shiro'],
    'drive': ['drive', 'dist', 'fuzz', 'overdrive', 'distortion', 'tube', 'clipping', 'amp', 'boost', 'screamer', 'klon', 'ds1', 'guvnor'],
    'dynamics': ['comp', 'compressor', 'gate', 'limiter', 'swell', 'slowgear', 'fizz', 'denoiser', 'noise', 'de-noise'],
    'modulation': ['chorus', 'flange', 'flanger', 'phase', 'phaser', 'wah', 'vibrato', 'tremolo', 'talkbox', 'rotary', 'whirl'],
    'utility': ['util', 'gain', 'split', 'switch', 'meter', 'tuner', 'tune', 'midifilter', 'transpose', 'seq', 'clock', 'cv'],
    'synth': ['synth', 'piano', 'organ', 'drum', 'bass', 'nekobi', 'amsynth', 'epiano', 'fluid', 'soundfont', '303']
}

def guess_category(name, desc=""):
    combined = f"{name} {desc}".lower()
    for cat, keywords in CATEGORY_MAP.items():
        if any(k in combined for k in keywords):
            return cat
    return 'utility'

def main():
    print("=" * 70)
    print("  MODEP & BLOKAS FULL REPOSITORY SCRAPER (700+ PLUGINS)")
    print("=" * 70)

    api_url = 'https://api.github.com/repos/moddevices/mod-plugin-builder/contents/plugins/package?per_page=300'
    print(f"\n[*] Fetching package directory from mod-plugin-builder...")

    req = urllib.request.Request(api_url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        packages = json.loads(resp.read().decode('utf-8'))

    print(f"[+] Discovered {len(packages)} master package definitions.")

    catalog = []
    seen_sites = set()

    for i, p in enumerate(packages):
        name = p['name']
        mk_url = f"https://raw.githubusercontent.com/moddevices/mod-plugin-builder/master/plugins/package/{name}/{name}.mk"
        try:
            req_mk = urllib.request.Request(mk_url, headers=HEADERS)
            with urllib.request.urlopen(req_mk, timeout=10) as resp_mk:
                mk_text = resp_mk.read().decode('utf-8', errors='ignore')
                
                # Extract _SITE URL
                site_match = re.search(r'_SITE\s*=\s*(http[^\s\n]+|git[^\s\n]+)', mk_text)
                if not site_match:
                    continue
                site_url = site_match.group(1).rstrip("$").rstrip("/")

                # Skip mirrors, tarballs, or non-git/http repos if duplicate
                if site_url in seen_sites or "custom-package" in site_url:
                    continue
                seen_sites.add(site_url)

                cat = guess_category(name)
                display_name = name.replace("-lv2", "").replace("_lv2", "").replace("-labs", "").replace("-", " ").title()

                entry = {
                    "id": name,
                    "name": display_name,
                    "brand": "MOD Community",
                    "category": cat,
                    "repo": site_url,
                    "desc": f"Community LV2 audio effect/instrument: {display_name}."
                }
                catalog.append(entry)
                print(f"  [{len(catalog)}/{len(packages)}] {name} ({cat}) -> {site_url}")
        except Exception as e:
            pass

    out_file = os.path.abspath("scripts/modep_master_catalog.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2)

    print("\n" + "=" * 70)
    print(f"  SCRAPE COMPLETE! Saved {len(catalog)} unique package repositories to:")
    print(f"  {out_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
