# 🎸 MOD Universal Plugin Hub & Cloud Porter

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/danny1marshall1587-maker/mod-universal-plugin-hub/blob/main/notebooks/MOD_Universal_Plugin_Porter.ipynb)
[![Universal LV2 Builder](https://github.com/danny1marshall1587-maker/mod-universal-plugin-hub/actions/workflows/universal_lv2_builder.yml/badge.svg)](https://github.com/danny1marshall1587-maker/mod-universal-plugin-hub/actions/workflows/universal_lv2_builder.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform Matrix](https://img.shields.io/badge/Platforms-Win64%20%7C%20Linux64%20%7C%20ARM32%20%7C%20ARM64-blue.svg)]()

A complete **Cloud Compilation, Automated Repackaging, and Community Distribution System** that converts any LV2 guitar/audio plugin into a **Universal Multi-Architecture FAT Bundle** — 100% cross-compatible across **MOD Desktop (Windows, macOS, Linux)** and **MODEP / Patchbox OS (Raspberry Pi 3, 4, 5)**.

---

## 🌟 The Problem & The Solution

| The Old Way (Fragmented) | The Universal Hub Way (Unified) |
| :--- | :--- |
| ❌ Plugins compiled only for Raspberry Pi ARM. | ✅ **Automated 4-Arch Cross-Compilation** in parallel. |
| ❌ Windows/Mac users left without `.dll` binaries. | ✅ **Universal FAT Bundle**: 1 bundle runs on all platforms. |
| ❌ Generic grey boxes for plugins without web GUIs. | ✅ **Auto-MODGUI Synthesis**: Generates boutique pedal graphics. |
| ❌ Developers need 4 different physical test devices. | ✅ **1-Click Web & Colab Conversion**: Free cloud builds. |

---

## 🚀 3 Ways to Use This System

### 1. 🌐 Web Portal (Drag-and-Drop & Live Store)
Open `site/index.html` (or host it on GitHub Pages):
- **Drag & Drop** any LV2 `.zip` archive or paste a GitHub repo URL.
- Pick your target platforms and choose a pedal color finish.
- Watch the live build terminal compile your bundle and download it in 1 click.
- Browse and download community plugins in the **Live Store**.

### 2. 📓 Google Colab Notebook (1-Click Cloud Compute)
Click the badge below to run the build farm inside Google Colab with zero local setup:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/danny1marshall1587-maker/mod-universal-plugin-hub/blob/main/notebooks/MOD_Universal_Plugin_Porter.ipynb)

### 3. ⚡ GitHub Actions Automated CI/CD
Trigger the [Universal LV2 Builder Action](.github/workflows/universal_lv2_builder.yml) directly on GitHub:
- Enter any repository URL in `workflow_dispatch`.
- GitHub compiles all 4 targets, runs headless tests, and creates an official release with `.zip` assets attached.

---

## 📦 Anatomy of a Universal FAT LV2 Bundle

A Universal FAT Bundle contains native compiled binaries for every operating system and CPU architecture, declared cleanly inside a single `manifest.ttl`:

```
cyber-blues-driver.lv2/
├── manifest.ttl                     <-- Multi-architecture binary router
├── cyber-blues-driver.ttl           <-- LV2 port & parameter descriptors
├── modgui.ttl                       <-- Web interface descriptor
├── modgui/
│   ├── icon.html                    <-- HTML5 pedal interface
│   ├── stylesheet.css               <-- CSS3 boutique styling
│   ├── script.js                    <-- Rotary dial drag controller
│   ├── screenshot.png               <-- Store preview
│   └── thumbnail.png                <-- Pedalboard icon
├── cyber_blues_driver.dll           <-- 🪟 Windows 64-bit binary
├── cyber_blues_driver_linux_x86_64.so <-- 🐧 Linux Desktop binary
├── cyber_blues_driver_armv7.so      <-- 🍓 Raspberry Pi 3/4 32-bit (MODEP)
└── cyber_blues_driver_arm64.so      <-- ⚡ Raspberry Pi 4/5 64-bit (MODEP 64)
```

### Multi-Architecture `manifest.ttl` Syntax:
```turtle
@prefix lv2:  <http://lv2plug.in/ns/lv2core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://cyber-audio.co.uk/plugins/cyber-blues-driver>
    a lv2:Plugin ;
    lv2:binary <cyber_blues_driver.dll> ;
    lv2:binary <cyber_blues_driver_linux_x86_64.so> ;
    lv2:binary <cyber_blues_driver_armv7.so> ;
    lv2:binary <cyber_blues_driver_arm64.so> ;
    rdfs:seeAlso <cyber-blues-driver.ttl> , <modgui.ttl> .
```

---

## 🛡️ Vector Math: Intel SSE &rarr; ARM NEON Translation

To prevent compilation failures on Raspberry Pi when code uses Intel vector intrinsics (`_mm_add_ps`, `_mm_mul_ps`, etc.), the Porter automatically injects **`sse2neon.h`**. This translates all x86 vector registers directly into native ARM NEON SIMD instructions at compile time with zero overhead.

---

## 🔌 Installing Generated Bundles

Simply copy the generated `*.lv2` folder into your platform's plugin directory:

- **🪟 Windows (MOD Desktop)**: `C:\Program Files\MOD Desktop\plugins\`
- **🍓 Raspberry Pi (MODEP / Patchbox OS)**: `/var/modep/lv2/` or `~/.lv2/`
- **🍎 macOS (MOD Desktop)**: `~/Library/Audio/Plug-Ins/LV2/`
- **🐧 Linux (MOD Desktop)**: `~/.lv2/` or `/usr/lib/lv2/`

---

## 📄 License
MIT License. Copyright © 2026 Cyber Audio & Community Contributors.
