#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Cyber Audio
# SPDX-License-Identifier: MIT
# Upgraded Multi-Build System Porter Engine v2.1 for MOD Universal Multi-Architecture

import os
import sys
import shutil
import glob
import re
import json
import zipfile
import tarfile
import argparse
import urllib.request
import subprocess

def run_cmd(cmd, cwd=None, env=None):
    """Run shell command with clean output capture"""
    try:
        res = subprocess.run(cmd, shell=True, cwd=cwd, env=env, capture_output=True, text=True, timeout=300)
        return res.returncode == 0, res.stdout, res.stderr
    except Exception as e:
        return False, "", str(e)

def find_all_cpp_sources(src_dir):
    """Recursively find all C/C++ source files excluding tests"""
    sources = []
    for root, dirs, files in os.walk(src_dir):
        if 'test' in root.lower() or '.git' in root or 'build' in root:
            continue
        for f in files:
            if f.endswith(('.cpp', '.c', '.cc', '.cxx')) and not 'test' in f.lower():
                sources.append(os.path.join(root, f))
    return sources

def main():
    parser = argparse.ArgumentParser(description="MOD Universal LV2 Multi-Architecture Porter Engine v2.1")
    parser.add_argument("--source", required=True, help="GitHub URL or path to ZIP archive")
    parser.add_argument("--name", default="", help="Custom plugin / bundle name")
    parser.add_argument("--theme", default="copper", help="MODGUI Theme color")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()

    engine_dir = os.path.dirname(os.path.abspath(__file__))
    bundled_inc = os.path.join(engine_dir, "include")

    workspace = os.path.abspath("workspace_temp")
    out_dir = os.path.abspath(args.output_dir)
    shutil.rmtree(workspace, ignore_errors=True)
    os.makedirs(workspace, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 70)
    print("  CYBER AUDIO - MOD UNIVERSAL PORTER ENGINE v2.1")
    print("=" * 70)

    # 1. Fetch Source
    src_dir = os.path.join(workspace, "source")
    print(f"\n[1/5] Fetching source from: {args.source}")
    if args.source.startswith("http") and ("github.com" in args.source or args.source.endswith(".git")):
        git_url = args.source.rstrip("/")
        if not git_url.endswith(".git") and "/archive/" not in git_url and "/releases/" not in git_url:
            git_url += ".git"
        subprocess.run(["git", "clone", "--depth", "1", "--recursive", git_url, src_dir], check=True)
    elif args.source.startswith("http"):
        zip_dest = os.path.join(workspace, "downloaded.zip")
        urllib.request.urlretrieve(args.source, zip_dest)
        with zipfile.ZipFile(zip_dest, 'r') as zf:
            zf.extractall(src_dir)
    elif os.path.exists(args.source):
        if args.source.endswith(".zip"):
            with zipfile.ZipFile(args.source, 'r') as zf:
                zf.extractall(src_dir)
        else:
            shutil.copytree(args.source, src_dir)

    # Determine bundle name & target LV2 directory
    lv2_folders = [os.path.join(r, d) for r, ds, fs in os.walk(src_dir) for d in ds if d.endswith(".lv2")]
    if lv2_folders:
        target_lv2 = lv2_folders[0]
        bundle_name = os.path.basename(target_lv2)
    else:
        target_lv2 = src_dir
        bundle_name = (args.name or os.path.basename(args.source.rstrip("/"))).replace(".git", "")
        if not bundle_name.endswith(".lv2"):
            bundle_name += ".lv2"

    print(f"  -> Target Bundle Name: {bundle_name}")
    base_bin_name = bundle_name.replace(".lv2", "").replace("-", "_")
    final_bundle_dir = os.path.join(out_dir, bundle_name)
    shutil.rmtree(final_bundle_dir, ignore_errors=True)
    os.makedirs(final_bundle_dir, exist_ok=True)

    # 2. Detect Build System
    has_cmake = os.path.exists(os.path.join(src_dir, "CMakeLists.txt"))
    has_makefile = os.path.exists(os.path.join(src_dir, "Makefile")) or os.path.exists(os.path.join(src_dir, "makefile"))
    has_dpf = os.path.exists(os.path.join(src_dir, "dpf")) or os.path.exists(os.path.join(src_dir, "distrho"))
    
    print("\n[2/5] Build System Analysis:")
    print(f"  - CMakeLists.txt: {has_cmake}")
    print(f"  - Makefile: {has_makefile}")
    print(f"  - DPF Framework: {has_dpf}")

    # Copy initial TTL and GUI assets if they exist
    for item in os.listdir(target_lv2):
        s = os.path.join(target_lv2, item)
        d = os.path.join(final_bundle_dir, item)
        if os.path.isdir(s) and item != ".git" and item != "build":
            shutil.copytree(s, d, dirs_exist_ok=True)
        elif os.path.isfile(s) and not item.endswith(('.so', '.dll', '.dylib', '.o', '.a')):
            shutil.copy2(s, d)

    # 3. Multi-Architecture Cross-Compilation Matrix
    print("\n[3/5] Executing Multi-Target Cross-Compilation...")

    compiled_binaries = {
        "windows_x64": None,
        "linux_x64": None,
        "armv7": None,
        "arm64": None
    }

    # Build strategy 1: CMake
    if has_cmake:
        print("  [*] Building via CMake...")
        build_dir = os.path.join(src_dir, "build_linux")
        ok, out, err = run_cmd(f"cmake -B {build_dir} -S {src_dir} -DCMAKE_BUILD_TYPE=Release && cmake --build {build_dir} -- -j$(nproc)")
        if ok:
            for root, dirs, files in os.walk(build_dir):
                for f in files:
                    if f.endswith('.so'):
                        dest_so = os.path.join(final_bundle_dir, f"{base_bin_name}_linux_x86_64.so")
                        shutil.copy2(os.path.join(root, f), dest_so)
                        compiled_binaries["linux_x64"] = f"{base_bin_name}_linux_x86_64.so"
                        print(f"  ✓ Linux x86_64 CMake Build Succeeded: {f}")
                        break

    # Build strategy 2: Direct Recursive C/C++ compilation
    cpp_sources = find_all_cpp_sources(src_dir)
    print(f"  [*] Found {len(cpp_sources)} C/C++ source files for direct compilation")

    if cpp_sources:
        include_dirs = [
            "/usr/include",
            "/usr/local/include",
            "/usr/local/include/sse2neon",
            "/usr/include/lv2",
            "/usr/include/lv2/lv2plug.in/ns/lv2core",
            bundled_inc,
            os.path.join(bundled_inc, "lv2"),
            src_dir,
            os.path.join(src_dir, "src"),
            os.path.join(src_dir, "include"),
            os.path.join(src_dir, "dsp"),
            target_lv2
        ]
        inc_flags = " ".join([f"-I\"{d}\"" for d in include_dirs if os.path.exists(d)])
        src_args = " ".join([f"\"{f}\"" for f in cpp_sources])

        # A. Linux x86_64
        if not compiled_binaries["linux_x64"]:
            out_so = os.path.join(final_bundle_dir, f"{base_bin_name}_linux_x86_64.so")
            cmd = f"g++ -O3 -std=c++14 -fPIC -shared {inc_flags} {src_args} -o \"{out_so}\" -lm -lpthread -DNDEBUG || gcc -O3 -fPIC -shared {inc_flags} {src_args} -o \"{out_so}\" -lm -lpthread -DNDEBUG"
            ok, _, err = run_cmd(cmd)
            if ok and os.path.exists(out_so) and os.path.getsize(out_so) > 1024:
                compiled_binaries["linux_x64"] = f"{base_bin_name}_linux_x86_64.so"
                print(f"  ✓ Linux x86_64: [OK] ({os.path.getsize(out_so):,} bytes)")
            else:
                first_err = err.strip().splitlines()[0] if err.strip() else "Unknown error"
                print(f"  ✕ Linux x86_64 failed: {first_err}")

        # B. Windows x86_64 (.dll)
        out_dll = os.path.join(final_bundle_dir, f"{base_bin_name}.dll")
        cmd = f"x86_64-w64-mingw32-g++ -O3 -std=c++14 -shared -static-libgcc -static-libstdc++ {inc_flags} {src_args} -o \"{out_dll}\" -lm -DNDEBUG || x86_64-w64-mingw32-gcc -O3 -shared {inc_flags} {src_args} -o \"{out_dll}\" -lm -DNDEBUG"
        ok, _, err = run_cmd(cmd)
        if ok and os.path.exists(out_dll) and os.path.getsize(out_dll) > 1024:
            compiled_binaries["windows_x64"] = f"{base_bin_name}.dll"
            print(f"  ✓ Windows x86_64 (.dll): [OK] ({os.path.getsize(out_dll):,} bytes)")
        else:
            first_err = err.strip().splitlines()[0] if err.strip() else "Unknown error"
            print(f"  ✕ Windows x86_64 (.dll) failed: {first_err}")

        # C. Raspberry Pi ARMv7 32-bit (.so)
        out_armv7 = os.path.join(final_bundle_dir, f"{base_bin_name}_armv7.so")
        cmd = f"arm-linux-gnueabihf-g++ -O3 -std=c++14 -fPIC -shared -march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard {inc_flags} {src_args} -o \"{out_armv7}\" -lm -lpthread -DNDEBUG"
        ok, _, err = run_cmd(cmd)
        if ok and os.path.exists(out_armv7) and os.path.getsize(out_armv7) > 1024:
            compiled_binaries["armv7"] = f"{base_bin_name}_armv7.so"
            print(f"  ✓ Raspberry Pi ARM32 (MODEP): [OK] ({os.path.getsize(out_armv7):,} bytes)")
        else:
            first_err = err.strip().splitlines()[0] if err.strip() else "Unknown error"
            print(f"  ✕ Raspberry Pi ARM32 failed: {first_err}")

        # D. Raspberry Pi 4/5 AArch64 64-bit (.so)
        out_arm64 = os.path.join(final_bundle_dir, f"{base_bin_name}_arm64.so")
        cmd = f"aarch64-linux-gnu-g++ -O3 -std=c++14 -fPIC -shared -march=armv8-a {inc_flags} {src_args} -o \"{out_arm64}\" -lm -lpthread -DNDEBUG"
        ok, _, err = run_cmd(cmd)
        if ok and os.path.exists(out_arm64) and os.path.getsize(out_arm64) > 1024:
            compiled_binaries["arm64"] = f"{base_bin_name}_arm64.so"
            print(f"  ✓ Raspberry Pi ARM64 (MODEP 64): [OK] ({os.path.getsize(out_arm64):,} bytes)")
        else:
            first_err = err.strip().splitlines()[0] if err.strip() else "Unknown error"
            print(f"  ✕ Raspberry Pi ARM64 failed: {first_err}")

    # 4. Verified Multi-Architecture Manifest Generator
    print("\n[4/5] Synthesizing Verified Multi-Architecture manifest.ttl...")
    manifest_path = os.path.join(final_bundle_dir, "manifest.ttl")
    ttl_files = [f for f in os.listdir(final_bundle_dir) if f.endswith(".ttl") and f != "manifest.ttl" and f != "modgui.ttl"]
    primary_ttl = ttl_files[0] if ttl_files else f"{base_bin_name}.ttl"

    # Extract plugin URI
    plugin_uri = None
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as mf:
            m_match = re.search(r'<([^>]+)>\s+a\s+lv2:Plugin', mf.read())
            if m_match:
                plugin_uri = m_match.group(1)

    if not plugin_uri and os.path.exists(os.path.join(final_bundle_dir, primary_ttl)):
        with open(os.path.join(final_bundle_dir, primary_ttl), 'r', encoding='utf-8', errors='ignore') as pf:
            p_match = re.search(r'<([^>]+)>\s+a\s+lv2:Plugin', pf.read())
            if p_match:
                plugin_uri = p_match.group(1)

    if not plugin_uri:
        plugin_uri = f"http://cyber-audio.co.uk/plugins/{base_bin_name}"

    # ONLY add binary declarations for binaries that ACTUALLY exist and are non-empty!
    binary_statements = []
    if compiled_binaries["windows_x64"] and os.path.exists(os.path.join(final_bundle_dir, compiled_binaries["windows_x64"])):
        binary_statements.append(f"    lv2:binary <{compiled_binaries['windows_x64']}> ;")
    if compiled_binaries["linux_x64"] and os.path.exists(os.path.join(final_bundle_dir, compiled_binaries["linux_x64"])):
        binary_statements.append(f"    lv2:binary <{compiled_binaries['linux_x64']}> ;")
    if compiled_binaries["armv7"] and os.path.exists(os.path.join(final_bundle_dir, compiled_binaries["armv7"])):
        binary_statements.append(f"    lv2:binary <{compiled_binaries['armv7']}> ;")
    if compiled_binaries["arm64"] and os.path.exists(os.path.join(final_bundle_dir, compiled_binaries["arm64"])):
        binary_statements.append(f"    lv2:binary <{compiled_binaries['arm64']}> ;")

    has_modgui = os.path.exists(os.path.join(final_bundle_dir, "modgui")) or os.path.exists(os.path.join(final_bundle_dir, "modgui.ttl"))
    see_also = f"<{primary_ttl}>" + (" , <modgui.ttl>" if has_modgui else "")

    bin_str = "\n".join(binary_statements)
    manifest_content = f"""@prefix lv2:  <http://lv2plug.in/ns/lv2core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<{plugin_uri}>
    a lv2:Plugin ;
{bin_str}
    rdfs:seeAlso {see_also} .
"""
    with open(manifest_path, 'w', encoding='utf-8') as mf:
        mf.write(manifest_content)

    # 5. Packaging
    print("\n[5/5] Packaging Verified Bundle...")
    zip_path = os.path.join(out_dir, f"{bundle_name.replace('.lv2', '')}-universal-fat.lv2.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(final_bundle_dir):
            for f in files:
                fpath = os.path.join(root, f)
                rpath = os.path.join(bundle_name, os.path.relpath(fpath, final_bundle_dir))
                zf.write(fpath, rpath)

    print("\n" + "=" * 70)
    print(f"  BUILD COMPLETED: {zip_path} ({os.path.getsize(zip_path):,} bytes)")
    print("=" * 70)

if __name__ == "__main__":
    main()
