# GitLab Template README 合并案例

## 场景

GitLab 创建仓库时自动生成模板 README.md，用户本地已有完整项目且包含自己的 README.md。
两边各有一个 `Initial commit`，历史完全分叉。

## 远程仓库模板 README 特征

```bash
git show <remote-commit>:README.md | head -20
# 内容以 "# Getting started" 开头，包含 GitLab 官方模板链接
```

## 推荐处理方式

用户选择"合并"时的完整操作序列：

```bash
git fetch origin
git pull --rebase origin main
# 出现 CONFLICT (add/add): Merge conflict in README.md

# 查看冲突文件，确认远程是模板、本地是项目文档
# 保留本地版本：
git checkout --theirs README.md
git add README.md
git commit -m "Initial commit: LLM Wiki v1.0"
git rebase --continue

# 推送
git push origin main
```

## 最终提交历史

```
8326b97 Initial commit: LLM Wiki v1.0   ← 本地完整项目
19d05e4 Initial commit                   ← GitLab 模板 README（作为基础）
```

这样保留了 GitLab 模板提交记录，同时本地项目完整覆盖了 README.md。
