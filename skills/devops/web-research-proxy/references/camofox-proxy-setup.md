# Camofox Browser — Proxy Setup Guide

Deploying Camofox (Node.js browser automation server) behind corporate proxy in WSL2.

## Architecture

```
Camofox Server (Node.js, port 9377)
├── Camoufox browser binary (~/.cache/camoufox/)
├── uBlock Origin addon (~/.cache/camoufox/addons/UBO/)
├── Native modules (better-sqlite3, impit)
└── Playwright (Firefox-based)
```

## Step-by-Step Setup

### 1. Clone with proxy
```bash
cd /mnt/c/wsl
git -c http.proxy=http://10.197.216.7:3128 clone https://github.com/jo-inc/camofox-browser.git
```

### 2. npm install with proxy
```bash
cd /mnt/c/wsl/camofox-browser
npm config set proxy http://10.197.216.7:3128
npm config set https-proxy http://10.197.216.7:3128
npm install
```

### 3. Download Camoufox binary (Node.js fetch ignores HTTP_PROXY)
```bash
# Find the download URL
curl -x http://10.197.216.7:3128 -sL "https://github.com/daijro/camoufox/releases/latest" -o /dev/null -w "%{url_effective}"
# → e.g. https://github.com/daijro/camoufox/releases/tag/v150.0.2-beta.25

# Find the asset URL
curl -x http://10.197.216.7:3128 -sL "https://github.com/daijro/camoufox/releases/expanded_assets/v150.0.2-beta.25" | grep -o 'href="[^"]*lin[^"]*x86_64[^"]*\.zip"' | head -1

# Download
mkdir -p ~/.cache/camoufox
curl -x http://10.197.216.7:3128 -L "https://github.com/.../camoufox-xxx-lin.x86_64.zip" -o ~/.cache/camoufox/camoufox.zip

# Extract and setup
python3 -c "
import zipfile, os, json, shutil
cache = os.path.expanduser('~/.cache/camoufox')
with zipfile.ZipFile(os.path.join(cache, 'camoufox.zip'), 'r') as z:
    z.extractall(os.path.join(cache, 'tmp'))
for item in os.listdir(os.path.join(cache, 'tmp')):
    shutil.move(os.path.join(cache, 'tmp', item), os.path.join(cache, item))
os.rmdir(os.path.join(cache, 'tmp'))
os.remove(os.path.join(cache, 'camoufox.zip'))
with open(os.path.join(cache, 'version.json'), 'w') as f:
    json.dump({'version': {'major': 150}, 'release': 'latest'}, f)
os.chmod(cache, 0o755)
for r, ds, fs in os.walk(cache):
    for d in ds: os.chmod(os.path.join(r, d), 0o755)
    for f in fs: os.chmod(os.path.join(r, f), 0o755)
"
```

### 4. Download uBlock Origin addon
```bash
mkdir -p ~/.cache/camoufox/addons/UBO
curl -x http://10.197.216.7:3128 -L "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi" -o /tmp/ubo.xpi
cd ~/.cache/camoufox/addons/UBO && python3 -c "
import zipfile
with zipfile.ZipFile('/tmp/ubo.xpi', 'r') as z:
    z.extractall('.')
" && rm /tmp/ubo.xpi
```

### 5. Fix native modules (WSL2 may install Windows binaries)
```bash
# Rebuild all native modules for Linux
cd /mnt/c/wsl/camofox-browser
export PATH=~/.nvm/versions/node/v24.15.0/bin:$PATH
npm rebuild better-sqlite3 --build-from-source

# impit may need manual Linux binary
npm pack impit-linux-x64-gnu@0.13.1
tar -xzf impit-linux-x64-gnu-*.tgz
mv package node_modules/impit-linux-x64-gnu
rm impit-linux-x64-gnu-*.tgz
```

### 6. Configure Hermes integration
Add to `~/.hermes/.env`:
```
CAMOFOX_URL=http://localhost:9377
```

### 7. Start with NO_XVFB (WSL2 requirement)
```bash
cd /mnt/c/wsl/camofox-browser
NO_XVFB=1 CAMOFOX_PORT=9377 ~/.nvm/versions/node/v24.15.0/bin/node server.js
```

## WSL2 xvfb Flash Problem

**Symptom**: After starting Camofox, Windows host shows flashing WSL terminal windows.

**Cause**: Camofox uses xvfb (X Virtual Frame Buffer) on Linux. In WSL2, xvfb triggers Windows GUI bridge, causing screen flashes.

**Fix**: Set `NO_XVFB=1` environment variable. This forces headless mode (no virtual display).

**Code change in server.js** (line ~920):
```javascript
// Before:
if (os.platform() === 'linux') {

// After:
if (os.platform() === 'linux' && !process.env.NO_XVFB) {
```

## Pitfalls

### Pitfall: Node.js fetch() ignores HTTP_PROXY
`fetch()` in Node.js does NOT use `HTTP_PROXY`/`HTTPS_PROXY` env vars. Camoufox binary download and addon downloads use `fetch()` internally.

**Fix**: Download manually with `curl -x proxy` and place in expected directories.

### Pitfall: npm installs wrong platform native modules
When running `npm install` in WSL2 for a project with optional native deps (e.g. `impit-linux-x64-gnu`), npm may install the Windows variant (`impit-win32-x64-msvc`) because it detects the Windows filesystem.

**Fix**: Manually download and install the correct platform package:
```bash
npm pack impit-linux-x64-gnu@<version>
tar -xzf impit-linux-x64-gnu-*.tgz
mv package node_modules/impit-linux-x64-gnu
```

### Pitfall: better-sqlite3 has Windows ELF header
**Symptom**: `invalid ELF header` error when launching Camofox.
**Cause**: `node_modules/better-sqlite3/build/Release/better_sqlite3.node` is a PE32+ DLL (Windows).
**Detection**: `file node_modules/better-sqlite3/build/Release/better_sqlite3.node` shows "PE32+ executable (DLL)"
**Fix**: `npm rebuild better-sqlite3 --build-from-source` (with Linux npm in PATH)

### Pitfall: manifest.json missing for addon
**Symptom**: `manifest.json is missing. Addon path must be a path to an extracted addon.`
**Cause**: uBlock Origin addon directory exists but is empty (download failed).
**Fix**: Download and extract the .xpi file manually (Step 4 above).

### Pitfall: GitHub API rate limit (60/hr unauthenticated)
Camofox setup requires downloading from GitHub releases. Anonymous API access is limited to 60 requests/hour.

**Workaround**: Use `curl -x proxy` for direct file downloads (not API). Release asset URLs don't count against API rate limit.
