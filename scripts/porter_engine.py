#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Cyber Audio
# SPDX-License-Identifier: MIT
# Core Porter Engine for MOD Universal Multi-Architecture Compilation

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

def main():
    parser = argparse.ArgumentParser(description="Universal Multi-Architecture LV2 Porter")
    parser.add_argument("--source", required=True, help="GitHub URL or path to ZIP archive")
    parser.add_argument("--name", default="", help="Custom plugin / bundle name")
    parser.add_argument("--theme", default="copper", help="MODGUI Theme color")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()

    workspace = os.path.abspath("workspace_temp")
    out_dir = os.path.abspath(args.output_dir)
    shutil.rmtree(workspace, ignore_errors=True)
    os.makedirs(workspace, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 65)
    print("  MOD UNIVERSAL PLUGIN PORTER ENGINE")
    print("=" * 65)

    # 1. Fetch Source
    src_dir = os.path.join(workspace, "source")
    print(f"\n[1/5] Fetching source from: {args.source}")
    if args.source.startswith("http") and ("github.com" in args.source or args.source.endswith(".git")):
        git_url = args.source.rstrip("/")
        if not git_url.endswith(".git") and "/archive/" not in git_url and "/releases/" not in git_url:
            git_url += ".git"
        subprocess.run(["git", "clone", "--depth", "1", git_url, src_dir], check=True)
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

    # Find LV2 bundle directory if nested
    lv2_folders = [os.path.join(r, d) for r, ds, fs in os.walk(src_dir) for d in ds if d.endswith(".lv2")]
    if lv2_folders:
        target_lv2 = lv2_folders[0]
        bundle_name = os.path.basename(target_lv2)
    else:
        target_lv2 = src_dir
        bundle_name = (args.name or os.path.basename(args.source.rstrip("/"))).replace(".git", "")
        if not bundle_name.endswith(".lv2"):
            bundle_name += ".lv2"

    print(f"  Target Bundle Name: {bundle_name}")

    # 2. Find C/C++ source files
    cpp_files = []
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.endswith(('.cpp', '.c', '.cc', '.cxx')) and not 'test' in f.lower():
                cpp_files.append(os.path.join(root, f))

    print(f"\n[2/5] Found {len(cpp_files)} C/C++ source file(s)")

    base_bin_name = bundle_name.replace(".lv2", "").replace("-", "_")
    final_bundle_dir = os.path.join(out_dir, bundle_name)
    shutil.rmtree(final_bundle_dir, ignore_errors=True)
    os.makedirs(final_bundle_dir, exist_ok=True)

    # Copy existing TTL & asset files into final bundle
    for item in os.listdir(target_lv2):
        s = os.path.join(target_lv2, item)
        d = os.path.join(final_bundle_dir, item)
        if os.path.isdir(s) and item != ".git":
            shutil.copytree(s, d, dirs_exist_ok=True)
        elif os.path.isfile(s) and not item.endswith(('.so', '.dll', '.dylib', '.o')):
            shutil.copy2(s, d)

    # 3. Cross-Compilation Matrix
    print("\n[3/5] Executing Cross-Compilation Matrix...")
    inc_flags = f"-I/usr/include -I/usr/local/include -I{target_lv2} -I{target_lv2}/src -I{src_dir} -I{src_dir}/src -I/usr/local/include/sse2neon"
    src_args = " ".join([f'"{f}"' for f in cpp_files])

    if cpp_files:
        # A. Linux x86_64
        out_so = os.path.join(final_bundle_dir, f"{base_bin_name}_linux_x86_64.so")
        cmd = f"g++ -O3 -fPIC -shared {inc_flags} {src_args} -o \"{out_so}\" -lm -lpthread -DNDEBUG 2>/dev/null || gcc -O3 -fPIC -shared {inc_flags} {src_args} -o \"{out_so}\" -lm -lpthread -DNDEBUG"
        res = os.system(cmd)
        print(f"  -> Linux x86_64: {'[OK]' if res == 0 and os.path.exists(out_so) else '[FAILED]'}")

        # B. Windows x86_64 (.dll)
        out_dll = os.path.join(final_bundle_dir, f"{base_bin_name}.dll")
        cmd = f"x86_64-w64-mingw32-g++ -O3 -shared -static-libgcc -static-libstdc++ {inc_flags} {src_args} -o \"{out_dll}\" -lm -DNDEBUG 2>/dev/null || x86_64-w64-mingw32-gcc -O3 -shared {inc_flags} {src_args} -o \"{out_dll}\" -lm -DNDEBUG"
        res = os.system(cmd)
        print(f"  -> Windows x86_64 (.dll): {'[OK]' if res == 0 and os.path.exists(out_dll) else '[FAILED]'}")

        # C. Raspberry Pi ARMv7 32-bit (.so)
        out_armv7 = os.path.join(final_bundle_dir, f"{base_bin_name}_armv7.so")
        cmd = f"arm-linux-gnueabihf-g++ -O3 -fPIC -shared -march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard {inc_flags} {src_args} -o \"{out_armv7}\" -lm -lpthread -DNDEBUG 2>/dev/null"
        res = os.system(cmd)
        print(f"  -> Raspberry Pi ARM32 (MODEP): {'[OK]' if res == 0 and os.path.exists(out_armv7) else '[FAILED]'}")

        # D. Raspberry Pi 4/5 AArch64 64-bit (.so)
        out_arm64 = os.path.join(final_bundle_dir, f"{base_bin_name}_arm64.so")
        cmd = f"aarch64-linux-gnu-g++ -O3 -fPIC -shared -march=armv8-a {inc_flags} {src_args} -o \"{out_arm64}\" -lm -lpthread -DNDEBUG 2>/dev/null"
        res = os.system(cmd)
        print(f"  -> Raspberry Pi ARM64 (MODEP 64): {'[OK]' if res == 0 and os.path.exists(out_arm64) else '[FAILED]'}")

    # 4. Multi-Architecture Manifest Generator
    print("\n[4/5] Synthesizing Multi-Architecture manifest.ttl...")
    manifest_path = os.path.join(final_bundle_dir, "manifest.ttl")
    ttl_files = [f for f in os.listdir(final_bundle_dir) if f.endswith(".ttl") and f != "manifest.ttl" and f != "modgui.ttl"]
    primary_ttl = ttl_files[0] if ttl_files else f"{base_bin_name}.ttl"

    plugin_uri = None
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as mf:
            m_text = mf.read()
            m_match = re.search(r'<([^>]+)>\s+a\s+lv2:Plugin', m_text)
            if m_match:
                plugin_uri = m_match.group(1)

    if not plugin_uri and os.path.exists(os.path.join(final_bundle_dir, primary_ttl)):
        with open(os.path.join(final_bundle_dir, primary_ttl), 'r', encoding='utf-8', errors='ignore') as pf:
            p_text = pf.read()
            p_match = re.search(r'<([^>]+)>\s+a\s+lv2:Plugin', p_text)
            if p_match:
                plugin_uri = p_match.group(1)

    if not plugin_uri:
        plugin_uri = f"http://cyber-audio.co.uk/plugins/{base_bin_name}"

    manifest_content = f"""@prefix lv2:  <http://lv2plug.in/ns/lv2core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<{plugin_uri}>
    a lv2:Plugin ;
    lv2:binary <{base_bin_name}.dll> ;
    lv2:binary <{base_bin_name}_linux_x86_64.so> ;
    lv2:binary <{base_bin_name}_armv7.so> ;
    lv2:binary <{base_bin_name}_arm64.so> ;
    rdfs:seeAlso <{primary_ttl}> , <modgui.ttl> .
"""
    with open(manifest_path, 'w', encoding='utf-8') as mf:
        mf.write(manifest_content)

    # 5. MODGUI Auto-Synthesis if Missing
    modgui_dir = os.path.join(final_bundle_dir, "modgui")
    if not os.path.exists(os.path.join(modgui_dir, "icon.html")) and not glob.glob(os.path.join(modgui_dir, "icon*.html")):
        print("\n[5/5] Synthesizing authentic MODGUI Pedal Interface...")
        os.makedirs(modgui_dir, exist_ok=True)
        
        ports = []
        if os.path.exists(os.path.join(final_bundle_dir, primary_ttl)):
            with open(os.path.join(final_bundle_dir, primary_ttl), 'r', encoding='utf-8', errors='ignore') as tf:
                ttl_data = tf.read()
                port_blocks = re.findall(r'\[([^\]]+)\]', ttl_data)
                for pb in port_blocks:
                    if "ControlPort" in pb and "InputPort" in pb:
                        sym = re.search(r'lv2:symbol\s+"([^"]+)"', pb)
                        name = re.search(r'lv2:name\s+"([^"]+)"', pb)
                        dflt = re.search(r'lv2:default\s+([0-9\.\-]+)', pb)
                        min_v = re.search(r'lv2:minimum\s+([0-9\.\-]+)', pb)
                        max_v = re.search(r'lv2:maximum\s+([0-9\.\-]+)', pb)
                        if sym and name:
                            s_str = sym.group(1)
                            if s_str not in ["bypass", "enabled"]:
                                ports.append({
                                    "symbol": s_str,
                                    "name": name.group(1),
                                    "default": float(dflt.group(1)) if dflt else 50.0,
                                    "min": float(min_v.group(1)) if min_v else 0.0,
                                    "max": float(max_v.group(1)) if max_v else 100.0,
                                    "is_toggle": "toggled" in pb
                                })

        knob_html = ""
        for p in ports:
            knob_html += f"""        <div class="custom-knob-wrapper">
            <div class="custom-knob-dial" data-symbol="{p['symbol']}" data-min="{p['min']}" data-max="{p['max']}" data-default="{p['default']}">
                <div class="knob-rotor"></div>
            </div>
            <span class="mod-knob-title">{p['name']}</span>
            <div class="mod-knob-image" mod-role="input-control-port" mod-port-symbol="{p['symbol']}" style="display:none;"></div>
        </div>\n"""

        html_template = f"""<div class="mod-pedal mod-pedal-boxy theme-{args.theme}">
    <div mod-role="drag-handle" class="mod-drag-handle"></div>
    <div class="mod-pedal-brand">CYBER AUDIO</div>
    <div class="mod-pedal-name">{bundle_name.replace('.lv2', '').replace('-', ' ').title()}</div>
    <div class="custom-knob-container">
{knob_html}
    </div>
    <div class="custom-footswitch-wrapper">
        <div class="mod-footswitch" mod-role="bypass"></div>
        <div class="mod-led" mod-role="bypass-light"></div>
    </div>
</div>"""
        with open(os.path.join(modgui_dir, "icon.html"), 'w', encoding='utf-8') as hf:
            hf.write(html_template)

        port_ttl_entries = ""
        for idx, p in enumerate(ports):
            port_ttl_entries += f"""        [
            lv2:index {idx} ;
            lv2:symbol "{p['symbol']}" ;
            lv2:name "{p['name']}" ;
        ] ,\n"""
        
        modgui_ttl = f"""@prefix lv2:    <http://lv2plug.in/ns/lv2core#> .
@prefix modgui: <http://moddevices.com/ns/modgui#> .

<{plugin_uri}>
    modgui:gui [
        modgui:resourcesDirectory <modgui> ;
        modgui:iconTemplate <modgui/icon.html> ;
        modgui:stylesheet <modgui/stylesheet.css> ;
        modgui:javascript <modgui/script.js> ;
        modgui:screenshot <modgui/screenshot.png> ;
        modgui:thumbnail <modgui/thumbnail.png> ;
        modgui:brand "CyberAudio" ;
        modgui:label "{bundle_name.replace('.lv2', '').title()}" ;
        modgui:model "boxy" ;
        modgui:panel "custom" ;
        modgui:port [
{port_ttl_entries.rstrip(' ,\n')}
        ] ;
    ] .
"""
        with open(os.path.join(final_bundle_dir, "modgui.ttl"), 'w', encoding='utf-8') as mgf:
            mgf.write(modgui_ttl)

        css_template = f""".mod-pedal.theme-{args.theme} {{
    background: #111111;
    border: 2px solid #333333;
    border-radius: 14px;
    padding: 15px;
    color: #ffffff;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.8);
}}
.mod-pedal-brand {{ font-size: 9px; font-weight: 900; letter-spacing: 2px; color: #00ff66; }}
.mod-pedal-name {{ font-size: 13px; font-weight: bold; margin-bottom: 12px; }}
.custom-knob-container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }}
.custom-knob-dial {{ width: 44px; height: 44px; border-radius: 50%; background: #1a1a1a; border: 2px solid #444; position: relative; cursor: pointer; }}
.knob-rotor {{ width: 2px; height: 16px; background: #00ff66; position: absolute; top: 4px; left: 50%; transform-origin: bottom center; }}
.mod-knob-title {{ font-size: 9px; font-weight: 700; display: block; margin-top: 4px; color: #aaa; }}
"""
        with open(os.path.join(modgui_dir, "stylesheet.css"), 'w', encoding='utf-8') as cf:
            cf.write(css_template)

        js_template = """function (event) {
    var pedal = event.icon;
    pedal.find('.custom-knob-dial').on('mousedown touchstart', function(e) {
        var dial = $(this);
        var sym = dial.attr('data-symbol');
        var min = parseFloat(dial.attr('data-min'));
        var max = parseFloat(dial.attr('data-max'));
        var startY = e.pageY || e.originalEvent.touches[0].pageY;
        var curVal = parseFloat(dial.attr('data-default'));
        $(document).on('mousemove.knob touchmove.knob', function(me) {
            var pageY = me.pageY || me.originalEvent.touches[0].pageY;
            var delta = (startY - pageY) * ((max - min) / 150.0);
            var newVal = Math.max(min, Math.min(max, curVal + delta));
            var deg = -140 + ((newVal - min) / (max - min)) * 280;
            dial.find('.knob-rotor').css('transform', 'rotate(' + deg + 'deg)');
            event.set_port_value(sym, newVal);
        });
        $(document).one('mouseup touchend', function() { $(document).off('.knob'); });
    });
}"""
        with open(os.path.join(modgui_dir, "script.js"), 'w', encoding='utf-8') as jf:
            jf.write(js_template)

    # 6. Create ZIP and TAR.GZ Archives
    zip_path = os.path.join(out_dir, f"{bundle_name.replace('.lv2', '')}-universal-fat.lv2.zip")
    tar_path = os.path.join(out_dir, f"{bundle_name.replace('.lv2', '')}-universal-fat.lv2.tar.gz")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(final_bundle_dir):
            for f in files:
                fpath = os.path.join(root, f)
                rpath = os.path.join(bundle_name, os.path.relpath(fpath, final_bundle_dir))
                zf.write(fpath, rpath)

    with tarfile.open(tar_path, 'w:gz') as tf:
        for root, dirs, files in os.walk(final_bundle_dir):
            for f in files:
                fpath = os.path.join(root, f)
                rpath = os.path.join(bundle_name, os.path.relpath(fpath, final_bundle_dir))
                tf.add(fpath, rpath)

    print("\n" + "=" * 65)
    print("  BUILD COMPLETE! Universal FAT Bundle ready.")
    print("=" * 65)
    print(f"  -> ZIP: {zip_path} ({os.path.getsize(zip_path):,} bytes)")
    print(f"  -> TAR: {tar_path} ({os.path.getsize(tar_path):,} bytes)")

if __name__ == "__main__":
    main()
