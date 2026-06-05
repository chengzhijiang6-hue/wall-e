#!/bin/bash
# 推送到 GitHub 的脚本
# 用法：./push_to_github.sh YOUR_TOKEN

if [ -z "$1" ]; then
    echo "用法: ./push_to_github.sh YOUR_GITHUB_TOKEN"
    exit 1
fi

TOKEN=$1
REPO_URL="https://${TOKEN}@github.com/chengzhijiang6-hue/wall-e.git"

cd /tmp/hermes-portable
git remote add origin $REPO_URL
git branch -M main
git push -u origin main

echo "推送完成！"
echo "仓库地址: https://github.com/chengzhijiang6-hue/wall-e"
