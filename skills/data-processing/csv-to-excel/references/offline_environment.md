# 离线环境 PowerShell 脚本方案

## 背景
目标服务器（如 Bosch 内网隔离服务器）无法连接公网，无法在线安装 PowerShell 模块。

## 方案对比

| 方案 | 依赖 | 复杂度 | 适用场景 |
|------|------|--------|----------|
| 离线导入 ImportExcel | 需搬运模块文件 | 低 | 有 U 盘搬运条件 |
| 内嵌 .NET OpenXML | 零依赖 | 高 | 最可靠但代码量大 |
| CSV + 本地合并脚本 | 宿主机需 Python+openpyxl | 低 | 宿主机有开发环境 |
| CSV + 人工合并 | 无 | 最低 | 临时方案 |

## 检查宿主机环境（从 WSL）
```bash
# 检查 Python
powershell.exe -Command "python --version"

# 检查 openpyxl
powershell.exe -Command "python -c 'import openpyxl; print(openpyxl.__version__)'"

# 检查 pip
powershell.exe -Command "pip --version"

# 安装 openpyxl（宿主机有网时）
powershell.exe -Command "pip install openpyxl"
```

## Windows 宿主机 Python 编码问题（必须处理）
Windows 控制台默认编码 cp1252，无法输出中文字符，会报 `UnicodeEncodeError`。
Python 脚本开头必须加：
```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

## 方案C/D：合并脚本要点
合并脚本放在宿主机桌面，读取 CSV 输出为多 Sheet xlsx。
- 使用 openpyxl 的 Workbook + load_workbook
- 每个 CSV 对应一个 Sheet，Sheet 名从文件名提取
- 保持与原脚本相同的样式规范（表头加粗、隔行着色、自动列宽）
- CSV 编码用 `utf-8-sig`（兼容 BOM 头）
- 脚本内用英文 print 输出（避免编码问题），或用上述编码修复
