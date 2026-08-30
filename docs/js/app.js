// SPDX-FileCopyrightText: 2026 Cyber Audio
// SPDX-License-Identifier: MIT
// MOD Universal Plugin Hub — Interactive Application Logic

document.addEventListener('DOMContentLoaded', () => {
    // 1. Tab Navigation
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = `tab-${tab.getAttribute('data-tab')}`;
            navTabs.forEach(t => t.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add('active');
        });
    });

    // 2. Target Chips Toggle
    const targetChips = document.querySelectorAll('.target-chip');
    targetChips.forEach(chip => {
        const checkbox = chip.querySelector('input[type="checkbox"]');
        chip.addEventListener('click', (e) => {
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
            }
            chip.classList.toggle('active', checkbox.checked);
        });
    });

    // 3. Theme Color Dots
    const themeDots = document.querySelectorAll('.theme-dot');
    let selectedTheme = 'copper';
    themeDots.forEach(dot => {
        dot.addEventListener('click', () => {
            themeDots.forEach(d => d.classList.remove('active'));
            dot.classList.add('active');
            selectedTheme = dot.getAttribute('data-color');
        });
    });

    // 4. Drag & Drop File Zone
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');

    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleLocalFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleLocalFile(e.target.files[0]);
            }
        });
    }

    let uploadedFile = null;
    function handleLocalFile(file) {
        uploadedFile = file;
        const dropText = dropzone.querySelector('.dropzone-text');
        dropText.innerHTML = `<strong>Selected:</strong> ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        document.getElementById('input-url').value = `local://${file.name}`;
    }

    // 5. Build Runner & Live Terminal Animation
    const btnStartBuild = document.getElementById('btn-start-build');
    const terminalLog = document.getElementById('terminal-log');
    const buildBadge = document.getElementById('build-status-badge');
    const resultBox = document.getElementById('result-box');

    if (btnStartBuild) {
        btnStartBuild.addEventListener('click', () => {
            const inputUrl = document.getElementById('input-url').value.trim();
            const customName = document.getElementById('input-name').value.trim() || 'Custom Plugin';

            if (!inputUrl) {
                alert('Please enter a GitHub repository URL or select a local ZIP file.');
                return;
            }

            // Reset UI
            terminalLog.innerHTML = '';
            resultBox.style.display = 'none';
            buildBadge.className = 'status-badge building';
            buildBadge.textContent = 'BUILDING';
            btnStartBuild.disabled = true;

            const logs = [
                { text: `> Initializing cloud cross-compilation environment...`, type: 'prompt', delay: 200 },
                { text: `[*] Fetching source from: ${inputUrl}`, type: 'info', delay: 600 },
                { text: `[+] Source tree analyzed: C/C++ LV2 DSP descriptors detected`, type: 'info', delay: 1000 },
                { text: `[*] Cross-compiling for Linux x86_64 (GCC -O3 -fPIC)...`, type: 'info', delay: 1500 },
                { text: `  -> [OK] Generated plugin_linux_x86_64.so (482 KB)`, type: 'success', delay: 2000 },
                { text: `[*] Cross-compiling for Windows 64-bit (MinGW-w64 x86_64)...`, type: 'info', delay: 2500 },
                { text: `  -> [OK] Generated plugin.dll (469 KB)`, type: 'success', delay: 3000 },
                { text: `[*] Cross-compiling for Raspberry Pi 3/4 (ARMv7 NEON hardfp)...`, type: 'info', delay: 3500 },
                { text: `  -> [OK] Generated plugin_armv7.so (448 KB)`, type: 'success', delay: 4000 },
                { text: `[*] Cross-compiling for Raspberry Pi 4/5 (AArch64 ARM64)...`, type: 'info', delay: 4400 },
                { text: `  -> [OK] Generated plugin_arm64.so (491 KB)`, type: 'success', delay: 4900 },
                { text: `[*] Synthesizing Multi-Architecture manifest.ttl...`, type: 'info', delay: 5300 },
                { text: `[*] Generating custom MODGUI HTML5/CSS3 pedal layout (theme: ${selectedTheme})...`, type: 'info', delay: 5800 },
                { text: `[+] Multi-Arch FAT LV2 Bundle packaged successfully!`, type: 'success', delay: 6300 }
            ];

            logs.forEach(l => {
                setTimeout(() => {
                    const line = document.createElement('div');
                    line.className = `term-line ${l.type}`;
                    line.textContent = l.text;
                    terminalLog.appendChild(line);
                    terminalLog.scrollTop = terminalLog.scrollHeight;
                }, l.delay);
            });

            setTimeout(() => {
                buildBadge.className = 'status-badge success';
                buildBadge.textContent = 'COMPLETED';
                btnStartBuild.disabled = false;

                document.getElementById('result-plugin-name').textContent = customName;
                document.getElementById('result-meta').textContent = `Universal FAT Bundle (Win64, Linux64, ARM32, ARM64) • Theme: ${selectedTheme.toUpperCase()}`;
                resultBox.style.display = 'block';

                document.getElementById('btn-download-bundle').onclick = () => {
                    alert(`Starting download of ${customName.toLowerCase().replace(/\\s+/g, '-')}-universal.lv2.zip`);
                };
            }, 6600);
        });
    }

    // 6. Community Library Store Loader
    const pluginsGallery = document.getElementById('plugins-gallery');
    const searchLibrary = document.getElementById('search-library');
    const catPills = document.querySelectorAll('.cat-pill');

    let allPlugins = [];

    fetch('data/plugins.json')
        .then(r => r.json())
        .then(data => {
            allPlugins = data;
            renderPlugins(allPlugins);
        })
        .catch(() => {
            // Fallback sample data if opened locally via file://
            allPlugins = [
                {
                    id: "cyber-strobe-tuner",
                    name: "Cyber Strobe & Peak Tuner",
                    brand: "CyberAudio",
                    category: "utility",
                    version: "1.0.0",
                    desc: "Studio Strobe & Peak Tuner system upgrade for MOD Desktop & MODEP with Gain boost, live VU meter, and 1-click MIDI Learn.",
                    platforms: ["Windows", "macOS", "Linux", "RPi ARM"],
                    download_url: "https://github.com/danny1marshall1587-maker/cyber-strobe-tuner/releases/tag/v1.0.0",
                    icon: "🍴"
                },
                {
                    id: "cyber-blues-driver",
                    name: "Cyber Blues Driver",
                    brand: "CyberAudio",
                    category: "drive",
                    version: "1.0.1",
                    desc: "Authentic classic blues overdrive LV2 pedal with touch-sensitive multi-stage clipping.",
                    platforms: ["Windows", "Linux", "RPi ARM32", "RPi ARM64"],
                    download_url: "https://github.com/danny1marshall1587-maker/cyber-blues-driver-lv2/releases/tag/v1.0.1",
                    icon: "🟦"
                },
                {
                    id: "cyber-klon",
                    name: "Cyber Klon Centaur",
                    brand: "CyberAudio",
                    category: "drive",
                    version: "1.0.1",
                    desc: "Legendary transparent overdrive LV2 pedal with dual-ganged clean blend.",
                    platforms: ["Windows", "Linux", "RPi ARM32", "RPi ARM64"],
                    download_url: "https://github.com/danny1marshall1587-maker/cyber-klon-lv2/releases/tag/v1.0.1",
                    icon: "🟨"
                }
            ];
            renderPlugins(allPlugins);
        });

    function renderPlugins(plugins) {
        if (!pluginsGallery) return;
        pluginsGallery.innerHTML = '';

        if (!plugins.length) {
            pluginsGallery.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #71717a; padding: 40px;">No plugins found matching your search.</p>';
            return;
        }

        plugins.forEach(p => {
            const card = document.createElement('div');
            card.className = 'pedal-card';
            card.innerHTML = `
                <div class="pedal-card-header">
                    <span class="pedal-badge-brand">${p.brand || 'CYBER AUDIO'}</span>
                    <div class="pedal-preview-icon">${p.icon || '🎛️'}</div>
                </div>
                <div class="pedal-card-body">
                    <h4 class="pedal-title">${p.name} <span style="font-size:10px; color:#a1a1aa;">v${p.version}</span></h4>
                    <p class="pedal-desc">${p.desc}</p>
                    <div class="pedal-platforms">
                        ${p.platforms.map(pl => `<span class="platform-tag">${pl}</span>`).join('')}
                    </div>
                    <a href="${p.download_url}" target="_blank" class="pedal-btn-download">⬇ Universal FAT Download</a>
                </div>
            `;
            pluginsGallery.appendChild(card);
        });
    }

    let activeCat = 'all';

    catPills.forEach(pill => {
        pill.addEventListener('click', () => {
            catPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            activeCat = pill.getAttribute('data-cat');
            filterPlugins();
        });
    });

    if (searchLibrary) {
        searchLibrary.addEventListener('input', filterPlugins);
    }

    function filterPlugins() {
        const query = searchLibrary ? searchLibrary.value.toLowerCase().trim() : '';
        const filtered = allPlugins.filter(p => {
            const matchCat = (activeCat === 'all' || p.category === activeCat);
            const matchQuery = !query || p.name.toLowerCase().includes(query) || p.desc.toLowerCase().includes(query) || (p.brand && p.brand.toLowerCase().includes(query));
            return matchCat && matchQuery;
        });
        renderPlugins(filtered);
    }
});
