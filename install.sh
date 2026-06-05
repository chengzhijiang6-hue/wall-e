#!/bin/bash
# Hermes Agent 一键安装脚本
# 用法：./install.sh

set -e

echo "=========================================="
echo "  Hermes Agent 便携版安装"
echo "=========================================="

# 1. 检查环境
echo "[1/6] 检查环境..."
if ! command -v hermes &> /dev/null; then
    echo "错误: hermes CLI 未安装"
    echo "请先安装: pip install hermes-agent"
    exit 1
fi

# 2. 创建目录结构
echo "[2/6] 创建目录结构..."
mkdir -p ~/.hermes/skills
mkdir -p ~/.hermes/memories
mkdir -p ~/.config/systemd/user

# 3. 复制配置
echo "[3/6] 复制配置文件..."
cp config.yaml ~/.hermes/
cp -r skills/* ~/.hermes/skills/

# 4. 配置环境变量
echo "[4/6] 配置环境变量..."
if [ ! -f ~/.hermes/.env ]; then
    cp .env.template ~/.hermes/.env
    echo "请编辑 ~/.hermes/.env 填入你的 API Keys"
    echo "然后重新运行此脚本"
    exit 0
fi

# 5. 安装 Mem0 MCP Server
echo "[5/6] 安装 Mem0 MCP Server..."
if [ ! -f /mnt/c/wsl/mem0/mcp-server/mem0_mcp_server.py ]; then
    mkdir -p /mnt/c/wsl/mem0/mcp-server
    cp mem0-mcp/mem0_mcp_server.py /mnt/c/wsl/mem0/mcp-server/
fi

# 创建 systemd 服务
cat > ~/.config/systemd/user/mem0-mcp.service << 'EOF'
[Unit]
Description=Mem0 MCP Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/mnt/c/wsl/mem0/mcp-server
ExecStart=$(which python3) mem0_mcp_server.py
Environment=MCP_PORT=59180
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable mem0-mcp.service
systemctl --user start mem0-mcp.service

# 6. 验证安装
echo "[6/6] 验证安装..."
sleep 2
if curl -s http://localhost:59180/health | grep -q "ok"; then
    echo "✅ Mem0 MCP Server 运行正常"
else
    echo "⚠️ Mem0 MCP Server 启动失败，请检查日志"
fi

echo ""
echo "=========================================="
echo "  安装完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 编辑 ~/.hermes/.env 填入你的 API Keys"
echo "2. 运行 hermes 验证配置"
echo "3. 查看 SOUL.md 了解行为规范"
