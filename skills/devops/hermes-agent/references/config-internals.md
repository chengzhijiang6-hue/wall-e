# Hermes Agent Config Internals (from Source Code)

来源：本次会话中对 `/mnt/c/wsl/hermes_official` 的源码分析。

## 配置文件加载路径

| 文件 | 用途 |
|------|------|
| `~/.hermes/config.yaml` | 所有设置（model, providers, fallback, toolsets 等） |
| `~/.hermes/.env` | API Key 和密钥（通过 python-dotenv 加载） |
| `~/.hermes/SOUL.md` | 会话身份定义（注入 system prompt） |
| `~/.hermes/auth.json` | 凭据池（缓存 exhaustion 状态） |

## Config 解析流程

1. `hermes_cli/config.py` — `load_config()` → YAML 加载 → 环境变量展开 → 规范化
2. `hermes_cli/config.py` — `validate_config()` → 校验各字段（如 fallback_model 的 provider+model 完整性）
3. `run_agent.py` — `RunAgent.__init__()` → 读取 `fallback_model` 构建 `_fallback_chain`
4. `cli.py` — 也独立读取 `fallback_model`（通过 `CLI_CONFIG.get("fallback_providers") or CLI_CONFIG.get("fallback_model")`）

## `model` 字段解析

代码位置：`runtime_provider.py` 的 `_get_model_config()`（第110-129行）

```python
def _get_model_config() -> Dict[str, Any]:
    config = load_config()
    model_cfg = config.get("model")
    if isinstance(model_cfg, dict):
        cfg = dict(model_cfg)
        # Accept "model" as alias for "default" (users intuitively write model.model)
        if not cfg.get("default") and cfg.get("model"):
            cfg["default"] = cfg["model"]
        default = (cfg.get("default") or "").strip()
        base_url = (cfg.get("base_url") or "").strip()
        is_local = "localhost" in base_url or "127.0.0.1" in base_url
        is_fallback = not default
        if is_local and is_fallback and base_url:
            detected = _auto_detect_local_model(base_url)
            if detected:
                cfg["default"] = detected
        return cfg
    if isinstance(model_cfg, str) and model_cfg.strip():
        return {"default": model_cfg.strip()}
    return {}
```

关键点：
- `model` 可以是字符串（旧格式）或字典
- 当用户写 `model.model` 时（直觉写法），会被当作 `model.default` 的别名
- `base_url` 包含 localhost 时且 `default` 为空，自动检测本地模型名

## `fallback_model` 解析

代码位置：`run_agent.py` 第1494-1513行

```python
if isinstance(fallback_model, list):
    self._fallback_chain = [
        f for f in fallback_model
        if isinstance(f, dict) and f.get("provider") and f.get("model")
    ]
elif isinstance(fallback_model, dict) and fallback_model.get("provider") and fallback_model.get("model"):
    self._fallback_chain = [fallback_model]
else:
    self._fallback_chain = []
```

关键点：
- 列表格式 → 逐个过滤保留有效条目
- 字典格式 → 包装为单元素列表
- 无效格式 → 空列表（不回退）
- `provider` 字段的取值会直接用于查找 `providers` 段中的同名配置

## Providers 解析

dashscope provider 在 Hermes 注册表中（`auth.py:266-273`）：

```python
"alibaba": ProviderConfig(
    id="alibaba",
    name="Alibaba Cloud (DashScope)",
    auth_type="api_key",
    inference_base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    api_key_env_vars=("DASHSCOPE_API_KEY",),
    base_url_env_var="DASHSCOPE_BASE_URL",
),
```

注意：
- 注册表中的 provider ID 是 `alibaba`，不是 `dashscope`
- `dashscope` 作为 provider 名称是用户在 `providers` 段中的自定义名称
- 标准 API Key 环境变量是 `DASHSCOPE_API_KEY`
- 默认 base_url 是 `dashscope-intl.aliyuncs.com`（国际站），用户配置的是 `dashscope.aliyuncs.com`（国内站）

## 验证配置的命令

| 命令 | 用途 |
|------|------|
| `hermes config` | 显示完整配置（model, API keys, settings） |
| `hermes config check` | 完整性检查（验证版本、必填字段） |
| `hermes config edit` | 打开编辑器 |
| `hermes config set <key> <value>` | 设置值 |
| `hermes config path` | 显示路径 |
| `hermes config env-path` | 显示 .env 路径 |
| `hermes fallback list` | 显示回退链 |
