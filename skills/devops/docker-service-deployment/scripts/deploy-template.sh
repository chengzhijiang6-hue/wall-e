#!/usr/bin/env bash
# 一键部署脚本模板 — 复制后根据项目需求修改
# 用法: bash deploy.sh
set -euo pipefail

# ── 颜色 ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; }
ask()   { echo -en "${CYAN}[?]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── 检查前置要求 ──
echo ""
echo "=============================="
echo "  项目名称 一键部署"
echo "=============================="
echo ""

if ! command -v docker &>/dev/null; then
    error "未找到 Docker，请先安装 Docker Desktop"
    exit 1
fi
info "Docker 已安装: $(docker --version)"

if ! docker compose version &>/dev/null && ! command -v docker-compose &>/dev/null; then
    error "未找到 docker compose，请升级 Docker Desktop"
    exit 1
fi
info "Docker Compose 可用"

# ── 如果已存在 .env，询问是否覆盖 ──
if [ -f .env ]; then
    echo ""
    warn "已存在 .env 文件"
    ask "是否重新配置? (y/N): "
    read -r RECONFIG
    if [[ ! "$RECONFIG" =~ ^[yY]$ ]]; then
        info "保留现有 .env，跳过配置"
    else
        rm .env
    fi
fi

# ── 交互式配置 ──
# TODO: 根据项目需求修改以下配置项
if [ ! -f .env ]; then
    echo ""
    echo "── 配置向导 ──"
    echo ""

    # 必填项
    while true; do
        ask "API Key (必填): "
        read -r API_KEY
        if [ -n "$API_KEY" ]; then break; fi
        error "API Key 不能为空"
    done

    # 可选项（带默认值）
    ask "服务端口 [8080]: "
    read -r PORT
    PORT="${PORT:-8080}"

    # 代理（可选）
    ask "HTTP 代理 (无需代理回车跳过): "
    read -r PROXY

    # 生成 .env
    cat > .env <<EOF
API_KEY=${API_KEY}
PORT=${PORT}
HTTP_PROXY=${PROXY}
HTTPS_PROXY=${PROXY}
NO_PROXY=localhost,127.0.0.1
EOF

    info ".env 配置已生成"
fi

# ── 确定 compose 命令 ──
if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# ── 构建并启动 ──
echo ""
info "正在构建并启动容器..."
$COMPOSE_CMD up -d --build

# ── 健康检查轮询 ──
echo ""
info "等待服务启动..."

PORT=$(grep "^PORT=" .env 2>/dev/null | cut -d= -f2 || echo "8080")
MAX_WAIT=60
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    HTTP_CODE=$(curl --noproxy '*' -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/health" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo -n "."
done
echo ""

# ── 验证结果 ──
HTTP_CODE=$(curl --noproxy '*' -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo ""
    echo "=============================="
    echo -e "  ${GREEN}部署成功！${NC}"
    echo "=============================="
    echo ""
    echo "  服务地址: http://localhost:${PORT}"
    echo "  健康检查: http://localhost:${PORT}/health"
    echo ""
    echo "  常用命令:"
    echo "    查看日志:   $COMPOSE_CMD logs -f"
    echo "    停止服务:   $COMPOSE_CMD down"
    echo "    重启服务:   $COMPOSE_CMD restart"
    echo ""
else
    error "服务启动超时，请检查日志:"
    echo "  $COMPOSE_CMD logs"
    exit 1
fi
