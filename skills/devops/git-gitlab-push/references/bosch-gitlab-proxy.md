# Bosch Internal GitLab (code.exaas.bosch.com)

## GitLab URL Pattern

```
https://code.exaas.bosch.com/<username>/<repo>.git
```

Current user: `cze8wx`, email: `cze8wx@bosch.com`

## Git Proxy Configuration

Bosch network requires proxy for git operations:

```bash
cd <project-dir>
git config http.proxy http://10.197.216.7:3128
git config https.proxy http://10.197.216.7:3128
```

Or globally (affects all repos):
```bash
git config --global http.proxy http://10.197.216.7:3128
git config --global https.proxy http://10.197.216.7:3128
```

## Git Identity

```bash
git config user.email "cze8wx@bosch.com"
git config user.name "Ethan"
```

## Full Push Workflow

```bash
# 1. Init and configure
cd <project-dir>
git init
git config user.email "cze8wx@bosch.com"
git config user.name "Ethan"
git config http.proxy http://10.197.216.7:3128
git config https.proxy http://10.197.216.7:3128

# 2. Add remote (repo auto-created on first push)
git remote add origin https://code.exaas.bosch.com/cze8wx/<repo-name>.git

# 3. Stage, commit, push
git add .
git commit -m "feat: initial commit"
git push -u origin master
```

**Note**: Bosch GitLab auto-creates the private project on first push if it doesn't exist.

## Pitfalls

- **CONNECT tunnel failed, response 503**: Proxy not configured. Add `git config http.proxy`.
- **Repository auto-creation**: First push creates the repo automatically. No need to create it via web UI first.
- **Credential helper**: If `credential.helper=store` is set globally, credentials are cached in `~/.git-credentials`. May need to update if password changes.
