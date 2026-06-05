# Camofox Browser — Corporate Proxy Setup Guide

Full step-by-step for deploying Camofox behind a corporate HTTP proxy (SSL inspection).

## Prerequisites
- Node.js via nvm (`~/.nvm/versions/node/v24.15.0/`)
- Corporate proxy at `http://10.197.216.7:3128`

## Step 1: Clone and Install npm Packages

```bash
cd /mnt/c/wsl
git clone https://github.com/jo-inc/camofox-browser.git
cd camofox-browser

# Configure npm proxy BEFORE install
npm config set proxy http://10.197.216.7:3128
npm config set https-proxy http://10.197.216.7:3128

npm install
```

Postinstall will FAIL to download Camoufox binary (Node.js fetch ignores HTTP_PROXY). This is expected.

## Step 2: Download Camoufox Binary Manually

Node.js `fetch()` does not respect `HTTP_PROXY` env vars. Must use curl.

```bash
# Find latest release
LATEST_URL=$(curl -x http://10.197.216.7:3128 -sL \
  "https://github.com/daijro/camoufox/releases/latest" -o /dev/null -w "%{url_effective}")
# e.g. https://github.com/daijro/camoufox/releases/tag/v150.0.2-beta.25

# Find the linux x86_64 asset URL
ASSET_PATH=$(curl -x http://10.197.216.7:3128 -sL \
  "${LATEST_URL/releases/tag/releases}/expanded_assets/$(basename $LATEST_URL)" | \
  grep -o 'href="[^"]*lin[^"]*x86_64[^"]*\.zip"' | head -1 | sed 's/href="//;s/"//')
# e.g. /daijro/camoufox/releases/download/v150.0.2-beta.25/camoufox-150.0.2-alpha.26-lin.x86_64.zip

# Download
mkdir -p ~/.cache/camoufox
curl -x http://10.197.216.7:3128 -L "https://github.com${ASSET_PATH}" \
  -o ~/.cache/camoufox/camoufox.zip
```

## Step 3: Extract Binary and Create version.json

```python
import zipfile, os, json, shutil

cache_dir = os.path.expanduser("~/.cache/camoufox")

# Extract zip
with zipfile.ZipFile(os.path.join(cache_dir, "camoufox.zip")) as z:
    z.extractall(cache_dir)
os.remove(os.path.join(cache_dir, "camoufox.zip"))

# Create version.json (required by camoufox-js)
version_data = {
    "version": {"major": 150, "minor": 0, "patch": 2, "pre": "alpha.26"},
    "release": "v150.0.2-beta.25"
}
with open(os.path.join(cache_dir, "version.json"), "w") as f:
    json.dump(version_data, f, indent=2)

# Set permissions
os.chmod(cache_dir, 0o755)
for root, dirs, files in os.walk(cache_dir):
    for d in dirs: os.chmod(os.path.join(root, d), 0o755)
    for f in files: os.chmod(os.path.join(root, f), 0o755)
```

## Step 4: Download uBlock Origin Addon

The default addon download also fails silently. Must manually download and extract:

```bash
UBO_DIR=~/.cache/camoufox/addons/UBO
mkdir -p "$UBO_DIR"
curl -x http://10.197.216.7:3128 -L \
  "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi" \
  -o /tmp/ubo.xpi

# xpi is a zip file; extract it (must contain manifest.json)
python3 -c "
import zipfile
zipfile.ZipFile('/tmp/ubo.xpi').extractall('$UBO_DIR')
"
rm /tmp/ubo.xpi
```

**Verify**: `ls ~/.cache/camoufox/addons/UBO/manifest.json` must exist, otherwise Camoufox launch fails with:
```
manifest.json is missing. Addon path must be a path to an extracted addon.
```

## Step 5: Fix Native Modules

If `npm` ran from Windows context, native `.node` files are PE32 DLLs (Windows). Rebuild for Linux:

```bash
export PATH=~/.nvm/versions/node/v24.15.0/bin:$PATH

# Rebuild better-sqlite3 (commonly broken)
rm -rf node_modules/better-sqlite3/build
npm rebuild better-sqlite3 --build-from-source

# Rebuild all native modules
npm rebuild
```

**Verify**: `file node_modules/better-sqlite3/build/Release/better_sqlite3.node`
Must show `ELF 64-bit LSB shared object`, NOT `PE32+ executable (DLL)`.

### impit module (if missing)

```bash
# Check if platform-specific package exists
ls node_modules/ | grep impit
# If only impit-win32-* exists, manually install linux version:

npm pack impit-linux-x64-gnu@<version>
tar -xzf impit-linux-x64-gnu-*.tgz
mv package node_modules/impit-linux-x64-gnu
rm impit-linux-x64-gnu-*.tgz
```

## Step 6: Configure and Start

```bash
# Add to ~/.hermes/.env
echo "CAMOFOX_URL=http://localhost:9377" >> ~/.hermes/.env

# Start server (use nvm node path explicitly)
cd /mnt/c/wsl/camofox-browser
CAMOFOX_PORT=9377 ~/.nvm/versions/node/v24.15.0/bin/node server.js &

# Verify
sleep 10
curl -s http://localhost:9377/health
```

Expected: `{"ok":true,"engine":"camoufox","browserConnected":false,...}`
(`browserConnected` becomes `true` after first browser operation)

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `manifest.json is missing` | UBO addon not extracted | Step 4 |
| `invalid ELF header` on `.node` | Native module compiled for Windows | Step 5 |
| `impit couldn't load native bindings` | Missing linux native package | Step 5 (impit) |
| `getaddrinfo ENOTFOUND api.github.com` | Node.js fetch ignores proxy | Step 2 (use curl) |
| Healthcheck `Connection refused` | Browser not launched yet | Normal on startup; wait for first operation |
| `browser_navigate` times out | First launch slow; use REST API directly | See API usage below |

## Direct API Usage (When browser_* Tools Timeout)

```bash
# Create tab and navigate
TAB=$(curl -s -X POST http://localhost:9377/tabs \
  -H "Content-Type: application/json" \
  -d '{"userId":"user","sessionKey":"session","url":"https://example.com"}')
TAB_ID=$(echo $TAB | python3 -c "import sys,json; print(json.load(sys.stdin)['tabId'])")

# Get accessibility snapshot
curl -s "http://localhost:9377/tabs/${TAB_ID}/snapshot?userId=user"

# Click element by ref
curl -s -X POST "http://localhost:9377/tabs/${TAB_ID}/click" \
  -H "Content-Type: application/json" \
  -d '{"userId":"user","ref":"e1"}'

# Type text
curl -s -X POST "http://localhost:9377/tabs/${TAB_ID}/type" \
  -H "Content-Type: application/json" \
  -d '{"userId":"user","ref":"e2","text":"search query","pressEnter":true}'
```
