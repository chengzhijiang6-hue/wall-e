# Bosch Internal GitLab — Push Patterns

## GitLab Instance

- **URL**: `https://code.exaas.bosch.com`
- **Username**: `cze8wx`
- **Pattern**: `https://code.exaas.bosch.com/<username>/<repo>.git`

## Git Proxy Configuration (Required)

Bosch corporate network requires proxy for Git operations:

```bash
# Per-repo (recommended)
cd <project-dir>
git config http.proxy http://10.197.216.7:3128
git config https.proxy http://10.197.216.7:3128

# Global (affects all repos)
git config --global http.proxy http://10.197.216.7:3128
git config --global https.proxy http://10.197.216.7:3128
```

**Pitfall**: Without proxy config, `git push` returns `CONNECT tunnel failed, response 503`.

## Auto-Create on Push

Bosch GitLab supports **auto-create on first push** — no need to create the repo manually first:

```bash
git remote add origin https://code.exaas.bosch.com/cze8wx/my-project.git
git push -u origin master
# GitLab auto-creates the private project
```

The push output will confirm:
```
The private project cze8wx/my-project was successfully created.
```

## Finding GitLab Addresses from Session History

When the user says "I already gave you my GitLab info" but it's not in memory:

1. Search session history: `session_search` with query "gitlab 账号 仓库 地址"
2. Check existing repos: `find /mnt/c -name ".git" -type d` and `git remote -v`
3. Look for Bosch pattern: `code.exaas.bosch.com/<username>/`

## New Project Push Workflow

```bash
[1/4] Initialize git
  cd <project-dir>
  git init
  git config user.email "cze8wx@bosch.com"
  git config user.name "Ethan"

[2/4] Configure proxy
  git config http.proxy http://10.197.216.7:3128
  git config https.proxy http://10.197.216.7:3128

[3/4] Add and commit
  git add .
  git commit -m "feat: initial commit"

[4/4] Push (auto-creates repo)
  git remote add origin https://code.exaas.bosch.com/cze8wx/<repo-name>.git
  git push -u origin master
```
