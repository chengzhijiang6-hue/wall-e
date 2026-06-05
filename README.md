# Hermes Agent 便携版

一键部署的 Hermes Agent 配置，包含完整的行为规范、技能和记忆系统。

## 包含内容

- **SOUL.md** - 行为规范（响应标准、工作流程、用户偏好）
- **skills/** - 20 个预训练技能（Docker、PLMS、知识库等）
- **config.yaml** - 模型配置（mimo-v2.5-pro + deepseek-v4-flash）
- **mem0-mcp/** - Mem0 MCP Server（记忆系统）

## 快速安装

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/hermes-portable.git
cd hermes-portable

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 配置 API Keys
vim ~/.hermes/.env

# 4. 验证
hermes
```

## 配置说明

### 模型配置
- **主力模型**: mimo-v2.5-pro (小米)
- **兜底模型**: deepseek-v4-flash
- **嵌入模型**: DashScope text-embedding-v3

### 网络配置
- 公司代理: `http://YOUR_PROXY:3128`
- 本地服务不走代理

### 记忆系统
- **系统记忆**: SOUL.md 中的 MEMORY 部分
- **Mem0 记忆**: 通过 MCP Server 管理

## 自定义

### 添加新技能
```bash
hermes skill create my-skill --category devops
```

### 修改行为规范
编辑 `~/.hermes/SOUL.md` 中的 MEMORY 部分。

## 目录结构

```
hermes-portable/
├── README.md
├── install.sh
├── config.yaml
├── .env.template
├── SOUL.md
├── skills/
│   ├── docker-management/
│   ├── plms-troubleshooting/
│   └── ... (20 个技能)
└── mem0-mcp/
    └── mem0_mcp_server.py
```

## 注意事项

1. **API Keys**: 安装后需要配置你自己的 API Keys
2. **代理**: 公司网络需要配置代理
3. **Mem0**: 需要单独部署 Mem0 服务（Docker）

## 更新日志

- 2026-06-04: 初始版本，包含完整行为规范和 20 个技能
