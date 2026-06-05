# Node.js Proxy Quirks in Corporate Environments

## Problem: fetch() Ignores HTTP_PROXY

Node.js native `fetch()` (undici-based) does NOT use `HTTP_PROXY`/`HTTPS_PROXY` environment variables. This affects:
- npm postinstall scripts that download binaries
- Any Node.js tool using `fetch()` for downloads
- Camoufox, Playwright, Puppeteer browser binary downloads

**Error pattern:**
```
Error: getaddrinfo ENOTFOUND api.github.com
```

## Workaround Pattern

1. Identify what the tool is trying to download (check the script source)
2. Use `curl -x http://PROXY:PORT` to download manually
3. Place the file in the expected cache directory

## Example: Camoufox Binary Download

```bash
# 1. Find the release URL
curl -x http://10.197.216.7:3128 -sL "https://github.com/daijro/camoufox/releases/latest" -o /dev/null -w "%{url_effective}"
# Returns: https://github.com/.../releases/tag/v150.0.2-beta.25

# 2. Find the asset URL
curl -x http://10.197.216.7:3128 -sL "https://github.com/.../releases/expanded_assets/v150.0.2-beta.25" | grep -o 'href="[^"]*lin[^"]*x86_64[^"]*\.zip"'

# 3. Download to cache dir
mkdir -p ~/.cache/camoufox
curl -x http://10.197.216.7:3128 -L "https://github.com/.../camoufox-xxx-lin.x86_64.zip" -o ~/.cache/camoufox/camoufox.zip

# 4. Extract
python3 -c "import zipfile, os; zipfile.ZipFile(os.path.expanduser('~/.cache/camoufox/camoufox.zip')).extractall(os.path.expanduser('~/.cache/camoufox'))"
```

## npm Native Module Platform Mismatch

In WSL, npm may install Windows native modules instead of Linux ones (because node_modules from Windows side gets cached).

**Fix:**
```bash
# 1. Find the correct platform package
npm pack <package>-linux-x64-gnu@<version>

# 2. Extract to node_modules
tar -xzf <package>-linux-x64-gnu-<version>.tgz
mv package node_modules/<package>-linux-x64-gnu
```

## GitHub API Rate Limit

When using curl with proxy, the exit IP may be shared. GitHub API rate limit:
- Unauthenticated: 60 req/hour per IP
- Check: `curl -x proxy -s https://api.github.com/rate_limit`
- Workaround: use `git ls-remote` (not rate-limited) or wait
