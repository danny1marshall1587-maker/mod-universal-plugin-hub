# 📖 MOD Universal Plugin Hub — Developer Guide

This guide provides technical specifications and implementation details for plugin developers, MODEP maintainers, and community contributors.

---

## 📑 Table of Contents
1. [Overview & Architecture](#1-overview--architecture)
2. [Multi-Architecture Bundle Specification](#2-multi-architecture-bundle-specification)
3. [Auto-MODGUI Synthesis Engine](#3-auto-modgui-synthesis-engine)
4. [Intel SSE to ARM NEON Translation (`sse2neon`)](#4-intel-sse-to-arm-neon-translation)
5. [Community Store JSON Feed Schema](#5-community-store-json-feed-schema)
6. [Integrating with GitHub Actions in Your Own Repos](#6-integrating-with-github-actions-in-your-own-repos)
7. [Running the Porter Locally (CLI / Docker)](#7-running-the-porter-locally)

---

## 1. Overview & Architecture

The **MOD Universal Plugin Hub** bridges the gap between desktop x86_64 machines (Windows, macOS, Linux) and embedded ARM devices (Raspberry Pi 3/4/5 running Blokas MODEP or Patchbox OS).

```
┌────────────────────────────────────────────────────────┐
│               Source Input (Git / ZIP)                 │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
  [C/C++ / CMake / Faust]        [LV2 TTL Descriptor]
             │                           │
  ┌──────────┼──────────┐                ▼
  ▼          ▼          ▼        [Auto-MODGUI Synthesizer]
Win x64   Linux x64   ARM32/64           │
(.dll)     (.so)       (.so)             ▼
  │          │          │        [HTML5/CSS3/JS Pedal]
  └──────────┼──────────┘                │
             ▼                           ▼
   ┌───────────────────────────────────────────┐
   │        Universal FAT Bundle Packager      │
   │           (Multi-Arch manifest.ttl)       │
   └─────────────────────┬─────────────────────┘
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
    [GitHub Release Asset]   [Community Store Feed]
```

---

## 2. Multi-Architecture Bundle Specification

In standard LV2, plugins declare binary dependencies in `manifest.ttl`. Using standard RDF statements, we can declare multiple binaries inside a single bundle:

```turtle
@prefix lv2:  <http://lv2plug.in/ns/lv2core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://cyber-audio.co.uk/plugins/my-overdrive>
    a lv2:Plugin ;
    lv2:binary <my_overdrive.dll> ;                  # Windows 64-bit
    lv2:binary <my_overdrive_linux_x86_64.so> ;      # Linux Desktop 64-bit
    lv2:binary <my_overdrive_armv7.so> ;             # Raspberry Pi 3/4 32-bit (MODEP)
    lv2:binary <my_overdrive_arm64.so> ;             # Raspberry Pi 4/5 64-bit (MODEP 64)
    rdfs:seeAlso <my_overdrive.ttl> , <modgui.ttl> .
```

When `mod-host` or `lilv` loads the bundle:
- On Windows: it automatically finds and links `my_overdrive.dll`.
- On Linux x86: it links `my_overdrive_linux_x86_64.so`.
- On Raspberry Pi 32-bit: it links `my_overdrive_armv7.so`.
- On Raspberry Pi 64-bit: it links `my_overdrive_arm64.so`.

---

## 3. Auto-MODGUI Synthesis Engine

If your repository contains no `modgui/` directory, `scripts/porter_engine.py` automatically parses your plugin's `.ttl` port definitions:

1. **Knobs**: Generated for every `lv2:ControlPort` with `lv2:InputPort`.
2. **Toggles / Switches**: Generated for ports marked with `lv2:toggled` or `lv2:integer`.
3. **Bypass / Footswitch**: Standard MOD footswitch with glowing LED status.
4. **Drag Controllers**: Touch-ready vertical mouse and touch drag handlers bound to `event.set_port_value(symbol, value)`.

---

## 4. Intel SSE to ARM NEON Translation

Audio DSP algorithms frequently use SIMD instructions. To ensure your code builds without errors across both Intel and ARM:

- **Include path**: `/usr/local/include/sse2neon/` is automatically provided.
- **In C/C++ Code**:
  ```cpp
  #if defined(__ARM_NEON) || defined(__aarch64__)
      #include <sse2neon.h>
  #else
      #include <immintrin.h>
      #include <xmmintrin.h>
  #endif
  ```

---

## 5. Community Store JSON Feed Schema

The community catalog at `site/data/plugins.json` uses this open schema:

```json
{
  "id": "unique-plugin-id",
  "name": "Display Name",
  "brand": "Manufacturer / Author",
  "category": "drive | dynamics | modulation | delay | reverb | utility | nam",
  "version": "1.0.0",
  "desc": "Short description of the pedal and features.",
  "platforms": ["Windows", "macOS", "Linux", "RPi ARM32", "RPi ARM64"],
  "download_url": "https://github.com/user/repo/releases/download/v1.0.0/bundle.zip",
  "github_url": "https://github.com/user/repo",
  "icon": "🟦",
  "color": "#2563eb"
}
```

---

## 6. Integrating with GitHub Actions in Your Own Repos

You can copy `.github/workflows/universal_lv2_builder.yml` directly into your own plugin repository. Whenever you create a new tag (e.g. `git tag v1.0.0 && git push origin --tags`), GitHub will automatically compile all 4 architectures and create the release for you!

---

## 7. Running the Porter Locally

On Linux / WSL2:
```bash
# 1. Install prerequisites
sudo apt-get install -y gcc-arm-linux-gnueabihf gcc-aarch64-linux-gnu gcc-mingw-w64 lv2-dev

# 2. Run the Porter Engine
python3 scripts/porter_engine.py \
    --source "https://github.com/user/my-plugin" \
    --theme "gold" \
    --output-dir "dist"
```
The output directory will contain the ready-to-use `my-plugin-universal-fat.lv2.zip`!
