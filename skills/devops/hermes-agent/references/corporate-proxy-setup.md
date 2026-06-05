# 公司网络代理配置记录

## 环境

- **代理地址**: `http://10.197.216.7:3128`
- **SSL 解密**: 是（公司代理做 SSL 中间人）
- **系统**: WSL2 Ubuntu-24.04
- **Hermes**: 0.11.0 (venv: `/mnt/c/wsl/hermes_official/venv/`)
- **DashScope 端点**: `https://dashscope.aliyuncs.com/compatible-mode/v1`

## Hermes 代理配置修复

### 问题

在 Hermes Agent 中配置了 qwen3.6-flash (dashscope) 作为主模型后，启动**新对话会话**时出现连接失败：

```
⚠️  API call failed (attempt 1/3): APIConnectionError
   🔌 Provider: custom  Model: qwen3.6-flash
   🌐 Endpoint: https://dashscope.aliyuncs.com/compatible-mode/v1
   📝 Error: Connection error.
```

但**当前正在运行的会话**（shell 中有 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量）正常工作。

### 根因

Hermes 启动时通过 `env_loader.py` → `python-dotenv` 加载 `~/.hermes/.env` 到 `os.environ`。Hermes 底层使用 `httpx` 作为 HTTP 客户端，httpx 自动读取 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量走代理。

但 `~/.hermes/.env` 中只有 API Key，**没有代理配置**。代理变量仅存在于 `.bashrc` 中，只在 interactive bash shell 启动时才生效。当 Hermes 从非 bash 上下文启动时（桌面快捷方式、cron、env-clean 子进程等），代理变量缺失，导致连接 DashScope 直接走直连，但公司网络直接访问外网被防火墙拦截。

### 修复

将代理环境变量写入 `~/.hermes/.env`：

```env
HTTP_PROXY=http://10.197.216.7:3128
HTTPS_PROXY=http://10.197.216.7:3128
http_proxy=http://10.197.216.7:3128
https_proxy=http://10.197.216.7:3128
```

Hermes 启动时自动加载此文件，httpx 会识别 `HTTP_PROXY`/`HTTPS_PROXY` 并走代理。

### 验证方法

模拟干净环境（无继承的 shell 环境变量）：

```bash
env -i HOME=$HOME PATH="/mnt/c/wsl/hermes_official/venv/bin:/usr/bin:/bin" \
  hermes -z "只回复'测试通过'四个字即可"
```

应返回 `测试通过`（或其他预期回复）。

### 底层机制

- 加载文件: `~/.hermes/.env`
- 加载函数: `hermes_cli.env_loader.load_hermes_dotenv()`
- 底层库: `python-dotenv` → `dotenv.load_dotenv(dotenv_path, override=True)`
- HTTP 客户端: `httpx[socks]` → 自动读取标准 `HTTP_PROXY`/`HTTPS_PROXY` env vars
- 覆盖模式: `override=True` 意味着 `.env` 中的值会覆盖已存在的环境变量

### 注意事项

- Hermes **没有内置的 proxy 配置项**（config.yaml 中无 proxy 字段）
- 代理配置**必须**通过环境变量传递
- `.bashrc` 中的代理变量只对 interactive bash 有效
- `~/.hermes/.env` 是**唯一可靠**的放置位置
- SSL 解密环境下，Python 需要信任公司 CA 证书：
  ```bash
  sudo cp /path/to/corporate-ca.crt /usr/local/share/ca-certificates/
  sudo update-ca-certificates
  ```
