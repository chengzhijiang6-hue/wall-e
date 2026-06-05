# Hermes Dashboard Frontend Build

The PyPI package does NOT include pre-built frontend assets. After installing or upgrading hermes-agent, the frontend must be built.

## Quick Steps

```bash
# 1. Load nvm
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# 2. Sparse clone (only web/ directory)
cd /tmp && git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/NousResearch/hermes-agent.git hermes-agent-src
cd hermes-agent-src && git sparse-checkout set web

# 3. Build
cd web && npm ci && npm run build

# 4. Copy to venv (output goes to ../hermes_cli/web_dist relative to web/)
VENV_SITE="/mnt/c/wsl/hermes_official/venv/lib/python3.12/site-packages"
cp -r hermes_cli/web_dist "$VENV_SITE/hermes_cli/web_dist"

# 5. Clean up
rm -rf /tmp/hermes-agent-src
```

## Key Details

- `npm run build` output dir is `../hermes_cli/web_dist` (per `vite.config.ts` `outDir`)
- In a sparse clone, this resolves to `/tmp/hermes-agent-src/hermes_cli/web_dist`
- Must copy to the actual venv site-packages location
- After build, verify: `ls $VENV_SITE/hermes_cli/web_dist/index.html`

## When to Rebuild

- After `pip install --upgrade hermes-agent` (source files change)
- After `hermes dashboard` returns 404 with "Frontend not built"
- The `--skip-build` flag serves existing dist without checking freshness
