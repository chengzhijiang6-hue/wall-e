# Git 敏感信息脱敏操作手册

## 案例：隐藏公司代理 IP 和端口

### 背景

项目中多处硬编码了公司代理 `http://10.197.216.7:3128`（文档、配置示例、docker-compose.yml 等）。
用户要求：**本地文件保留实际地址，推送到 GitLab 的版本替换为占位符**。

### 实际执行过程

#### 第一步：定位敏感信息

```bash
grep -rn "10\.197\.216\.7" --include="*.md" --include="*.yml" --include="*.example" .
```

涉及文件：`.env.example`, `CHANGELOG.md`, `docker-compose.yml`, `LLM-WIKI-DOC.md`, `LLM-WIKI-PLAN.md`, `README.md`

#### 第二步：选择方案

| 方案 | 本地文件 | 远程历史 | 适用场景 |
|------|---------|---------|---------|
| Clean/Smudge 过滤器 | 不变 | 仅当前 HEAD 干净 | 长期防护 |
| 追加提交替换 | 被替换 | 旧提交残留 | 简单快速 |
| Force push 重写历史 | 不变 | 完全干净 | 彻底清除 |

#### 第三步：配置 Clean/Smudge 过滤器

脚本 `.git/scripts/proxy-filter.sh`：
- clean 模式：提交时 `sed` 替换敏感信息为占位符
- smudge 模式：检出时 `sed` 还原占位符为实际地址

`.gitattributes` 配置：
```
*.md filter=proxy
*.yml filter=proxy
*.txt filter=proxy
*.env.example filter=proxy
```

#### 第四步：处理已提交的历史

由于 GitLab main 分支保护，无法 force push。采用追加提交方式：
1. 替换工作区文件中的敏感信息
2. `git add` + `git commit`
3. `git push`

### 遇到的问题

1. **GitLab 保护分支**：`pre-receive hook declined` — 需临时取消保护或回退到追加提交
2. **临时仓库认证失败**：新目录缺少 `credential.helper` 配置 — 设置全局 `git config --global credential.helper store`
3. **远程有新提交**：用户通过 GitLab Web 编辑了 README — 需 `git pull --rebase` 或 `git merge` 合并后重新应用替换
4. **filter-branch 被阻止**：安全策略限制 — 使用 orphan 分支或临时目录方案替代

### 最终提交历史

```
f72870e 添加 .gitattributes: 自动过滤代理信息
b8ab358 合并远程更新
64b3a33 安全: 移除文档中的硬编码代理地址，替换为占位符
a0ffde7 Edit README.md
8326b97 Initial commit: LLM Wiki v1.0
19d05e4 Initial commit
```

早期提交（19d05e4 ~ 8326b97）中仍保留敏感信息。彻底清除需在 GitLab 取消 main 保护后 force push。

### 第五步：取消保护后彻底重写历史

用户在 GitLab Settings → Repository → Protected branches 取消 main 保护后：

```python
# 在原仓库中操作（复用凭证），创建 orphan 分支
git checkout --orphan clean-main
git rm -rf --cached .           # 清空暂存区

# 用 Python 脚本遍历所有已跟踪文件，替换敏感信息后写回
# 排除 .git/, var/, diff/, .env（gitignored 的不处理）
# 提交并 force push 到远程 main
git push --force origin clean-main:main

# 切回 main 并指向新提交
git checkout main
git reset --hard clean-main
git branch -D clean-main
```

**关键**：在原仓库内操作，而非临时目录，避免凭证问题。

### 最终提交历史（重写后）

```
a22bca4 LLM Wiki v1.0    ← 单个干净提交，无敏感信息
```
