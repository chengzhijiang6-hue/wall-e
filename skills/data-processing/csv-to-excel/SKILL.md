---
name: csv-to-excel
description: 将 CSV 数据提取关键信息并整合为多 Sheet Excel 汇总表，支持自动分类统计、格式美化、离线环境方案选择、文件组织规范
trigger: 用户要求将 CSV 文件整理/整合/汇总为 Excel 表，或多 CSV 合并为多 Sheet Excel，或服务器迁移资产清点，或说"整理表格"/"整理下这个表格"
---

# CSV → Excel 整合汇总技能

## 适用场景
- 防火墙连接表、网络流量表等结构化 CSV 数据
- 需要按维度（IP、防火墙、服务等）分类汇总
- 需要带格式的多 Sheet Excel 输出

## 执行步骤

### 1. 读取并解析 CSV
```python
with open(源文件路径, "r", encoding="utf-8") as f:
    raw = f.read()
reader = csv.DictReader(io.StringIO(raw), delimiter=';')  # 根据实际分隔符调整
rows = list(reader)
```

### 2. 分析数据结构
- 打印字段名列表确认列
- 统计关键维度分布（如目标IP、服务、动作等）
- 确定汇总维度

### 3. 生成 Excel（openpyxl）
必需的样式定义：
```python
thin = Border(left=Side('thin'), right=Side('thin'), top=Side('thin'), bottom=Side('thin'))
hdr_font = Font(bold=True, color="FFFFFF", size=11)
hdr_fill = PatternFill("solid", fgColor="4472C4")
sum_fill = PatternFill("solid", fgColor="2F5496")
alt_fill = PatternFill("solid", fgColor="D9E2F3")
green  = PatternFill("solid", fgColor="C6EFCE")
red    = PatternFill("solid", fgColor="FFC7CE")
```

通用格式化函数：
- `fmt_hdr(ws, ncols, fill)` — 表头样式
- `fmt_data(ws, nrows, ncols)` — 数据区隔行着色 + 边框
- `auto_w(ws, ncols, mx=35)` — 自动列宽

### 4. 典型 Sheet 结构

#### 模式A：多CSV合并（服务器资产清点）
| Sheet | 内容 | 排序 |
|-------|------|------|
| Non_MS_Summary | 非微软项目汇总（按风险排序） | 风险等级降序 |
| Summary_Stats | 风险统计概览 | - |
| 各数据Sheet | 原始数据 + Risk_Level列 | 原始顺序 |

#### 模式B：多维度汇总（防火墙连接表等）
| Sheet | 内容 | 排序 |
|-------|------|------|
| 连接明细 | 全字段提取 | 原始顺序 |
| 按目标IP汇总 | 目标维度统计 | 连接数/命中次数降序 |
| 按源IP汇总 | 源维度统计 | 连接数/命中次数降序 |
| 按防火墙汇总 | 防火墙维度统计 | 连接数降序 |
| 按协议服务汇总 | 协议/服务维度统计 | 连接数降序 |

**模式B汇总Sheet字段规范**：
- 按XXX汇总：[XXX, 连接数, 涉及YYY, 协议, 端口, 服务/应用, 动作, 总命中次数]
- 多值字段（协议、端口、服务）用 `\n` 连接，单元格设置 `wrap_text=True`
- 连接数 = 该分组下的记录数
- 总命中次数 = Hits字段求和（需转int，非数字值忽略）
- 按总命中次数降序排列

### 5. 保存路径
- 默认与源文件同目录
- 文件名：`源文件名 - 整合汇总.xlsx`

## 多维度汇总实现模板（模式B）

当数据需要按多个维度汇总统计时（如防火墙连接表），使用以下模板：

```python
from collections import defaultdict

def aggregate_by_key(data, key_col, headers):
    """按指定列分组聚合"""
    groups = defaultdict(lambda: {
        'count': 0,
        'connections': [],
        'protocols': set(),
        'ports': set(),
        'services': set(),
        'actions': set(),
        'total_hits': 0,
        'related_ips': set()
    })
    
    for row in data:
        key = row[key_col] if key_col < len(row) else ''
        g = groups[key]
        g['count'] += 1
        g['connections'].append(row)
        
        # 提取协议、端口、服务、动作（根据实际列名调整）
        proto_idx = headers.index('Protocol') if 'Protocol' in headers else -1
        port_idx = headers.index('Port') if 'Port' in headers else -1
        svc_idx = headers.index('Service_Name') if 'Service_Name' in headers else -1
        action_idx = headers.index('Action') if 'Action' in headers else -1
        hits_idx = headers.index('Hits') if 'Hits' in headers else -1
        
        if proto_idx >= 0 and proto_idx < len(row): g['protocols'].add(row[proto_idx])
        if port_idx >= 0 and port_idx < len(row): g['ports'].add(row[port_idx])
        if svc_idx >= 0 and svc_idx < len(row): g['services'].add(row[svc_idx])
        if action_idx >= 0 and action_idx < len(row): g['actions'].add(row[action_idx])
        if hits_idx >= 0 and hits_idx < len(row):
            try: g['total_hits'] += int(row[hits_idx])
            except: pass
    
    return groups

def create_summary_sheet(wb, name, groups, key_name, headers_extra):
    """创建汇总Sheet"""
    ws = wb.create_sheet(name)
    headers = [key_name, '连接数'] + headers_extra + ['总命中次数']
    ws.append(headers)
    
    # 按总命中次数降序排列
    sorted_groups = sorted(groups.items(), key=lambda x: x[1]['total_hits'], reverse=True)
    
    for key, g in sorted_groups:
        row = [
            key,
            g['count'],
            '\n'.join(sorted(g['protocols'])) or '-',
            '\n'.join(sorted(g['ports'])) or '-',
            '\n'.join(sorted(g['services'])) or '-',
            '\n'.join(sorted(g['actions'])) or '-',
            g['total_hits']
        ]
        ws.append(row)
    
    # 格式化
    fmt_hdr(ws, len(headers))
    fmt_data(ws, len(sorted_groups), len(headers))
    auto_w(ws, len(headers))
    
    # 多值字段设置自动换行
    for r in range(2, ws.max_row+1):
        for c in range(3, len(headers)):  # 协议、端口、服务、动作列
            ws.cell(r, c).alignment = Alignment(wrap_text=True, vertical='center')
        # 增大行高以显示多行内容
        ws.row_dimensions[r].height = max(30, 15 * max(
            str(ws.cell(r, c).value or '').count('\n') + 1 for c in range(1, len(headers)+1)
        ))
    
    return ws
```

## Excel 合并流程（两个文件 → 一个）
当需要合并多个已生成的 Excel 时：
1. 用 `load_workbook` 分别读取
2. 增加"方向"列区分来源（如出站/入站）
3. 用 `copy_sheet_data(src_ws, dst_ws)` 复制数据
4. 同维度汇总表需要合并统计（用 defaultdict 累加）
5. 输出文件名带"完整"前缀

## 多 CSV → 单 Excel 多 Sheet 合并（方案C）

当目标服务器无公网、无法安装 ImportExcel 模块时，采用此方案：
1. PowerShell 脚本输出多个 CSV
2. CSV 复制到宿主机桌面
3. Python 合并脚本（宿主机有 Python + openpyxl 时）或由 Agent 直接合并

合并脚本关键点：
```python
# Windows 控制台编码修复（必须）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# CSV 读取用 utf-8-sig 处理 BOM
with open(csv_path, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
```

交付时必须附带使用说明文件（前置条件、操作步骤、输出说明）。

## 离线环境方案选择
当目标服务器无法连接公网时，ImportExcel 模块不可用。方案优先级：
1. **离线导入模块**：有网机器下载模块，U盘复制到目标服务器离线安装
2. **脚本内嵌 .NET OpenXML**：零依赖，纯原生 PowerShell 调用 System.IO.Packaging
3. **输出 CSV + 本地合并**：脚本输出 CSV，桌面放合并脚本（需宿主机有 Python + openpyxl）
4. **输出 CSV + 人工合并**：最原始方案

选择前必须检查宿主机环境：`powershell.exe -Command "python --version"` 和 `python -c 'import openpyxl'`
详见 `references/offline_environment.md`

## 文件操作安全规范（强制）
- 修改任何文件前必须经用户明确允许，不能自作主张
- 修改外部路径（网络共享、UNC 路径等）文件前，必须先在同路径下备份源文件（如 xxx.bak）
- 覆盖操作必须经用户确认后才能执行
- 绝对不能自作主张覆盖网络共享或外部路径上的原始文件
- 本地桌面文件可直接操作，但仍建议确认

## 文件存放规范（强制）
所有工作数据统一存 `C:\Users\CZE8WX\Desktop\work\`，按工作内容分类建子目录。
**所有文件夹和文件名必须用英文，禁止中文命名。**

```
C:\Users\CZE8WX\Desktop\work\
├── {project-name}\              # 按工作内容命名（如 server-migration）
│   ├── {device-id}\             # 按设备IP或名称建子目录
│   │   ├── {sub-task}\          # 子任务可再建子目录（如 CAS IP Filter）
│   │   │   ├── raw\             # 用户输入的原始文件（CSV等）
│   │   │   └── merged\          # Agent 处理后的输出文件（Excel等）
│   │   ├── raw\                 # 主任务原始文件
│   │   └── merged\              # 主任务输出文件
│   └── ...
└── {project-name}\scripts\      # 脚本文件按项目分目录存放
```

- 不要把工作文件堆在桌面根目录
- 每个新任务先确认目录结构再开始
- CSV/数据文件放 `raw/`，Excel/最终输出放 `merged/`
- 目录名统一用 `raw` 和 `merged`，不用中文或其他名称
- 多设备场景：每个设备一个独立目录（以 IP 命名），互不干扰
- 脚本文件放在 `work\scripts\` 或 `work\{project}\scripts\` 下

## 访问 Windows UNC 网络路径
WSL 中无法直接访问 UNC 路径（`\\server\share`），需通过宿主机 PowerShell：
```python
# 读取 UNC 路径文件（PowerShell -LiteralPath 避免转义问题）
terminal("powershell.exe -Command \"Get-Content -LiteralPath '\\\\\\\\server\\\\share\\\\path\\\\file.txt' -ErrorAction Stop\"")

# 复制 UNC 文件到本地（用双反斜杠转义）
terminal("powershell.exe -Command \"Copy-Item -LiteralPath '\\\\\\\\server\\\\share\\\\file.txt' -Destination 'C:\\\\Users\\\\user\\\\Desktop\\\\file.txt' -Force\"")

# 写回 UNC 路径（同上模式，Copy-Item 反向）
terminal("powershell.exe -Command \"Copy-Item -LiteralPath 'C:\\\\Users\\\\user\\\\Desktop\\\\file.txt' -Destination '\\\\\\\\server\\\\share\\\\file.txt' -Force\"")
```
关键点：
- PowerShell 中 UNC 路径用 `\\\\server\\share`（四个反斜杠在 shell 中表示两个）
- 必须用 `-LiteralPath` 而非 `-Path`，否则 PowerShell 会将 `\\` 解析为本地 `C:\`
- 访问需要域认证，当前用户凭证需有权限

## PowerShell 脚本改造：多 CSV → 单 Excel 多 Sheet
当用户有一个输出多个 CSV 的 PowerShell 脚本，要求合并为单一 Excel 多 Sheet 时：
1. 在脚本开头添加 ImportExcel 模块自动安装逻辑
2. 将所有 `Export-Csv` 替换为 `Export-Excel -WorksheetName "Sheet名"`
3. 输出文件从目录改为单一 `.xlsx` 文件
4. 添加 `-AutoSize -BoldTopRow -FreezeTopRow` 参数美化
5. **必须先备份原脚本再修改**（同路径下 .bak）

模板参见：`references/powershell_importexcel.md`

## 主动加载规则（强制）
当用户要求"整理CSV/Excel"、"合并CSV"、"汇总数据"、"整理表格"、"整理下这个表格"等任务时，必须立即加载此skill并按规范执行，不能先做一个简化版本再被用户纠正。用户说"用你的skill整理"意味着：按skill的目录结构（raw/merged）、样式规范、非微软分析流程一步到位。

关键判断：如果目录下有 .csv 文件 + 用户说"整理/汇总" → 直接走 Excel 生成流程，不要先输出 Markdown。

## Pitfalls

### Windows 控制台编码问题（高频）
宿主机 Python 脚本输出中文时，Windows 默认编码 cp1252 会报 `UnicodeEncodeError`。
修复方法：脚本开头添加：
```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

### execute_code 变量不持久化（高频）
`execute_code` 每次调用是独立沙箱，前一次的变量（如 `wb`、`all_data`）在下一次调用中不存在。
**解决方案**：将整个Excel生成逻辑（读取数据→创建Sheet→样式→保存）放在单个 `execute_code` 调用中完成，不要拆分为多次调用。
如果代码过长，用函数封装但仍在同一调用内执行。

### execute_code 环境中 read_file 返回格式
execute_code 内用 `open()` 直接读文件，不要用 `read_file`（返回格式在 sandbox 中不一致）

### openpyxl 安装路径
- WSL: `/mnt/c/wsl/hermes_official/venv/bin/pip install openpyxl`
- 宿主机: `powershell.exe -Command "pip install openpyxl"`

### 多行内容单元格
设置 `wrap_text=True` + 增大行高（如 `ws.row_dimensions[r].height = 40`）

### 动作/状态字段颜色
- Allowed/Success/Permit: 绿色 `PatternFill("solid", fgColor="C6EFCE")`
- Blocked/Denied/Drop/Timeout/Error: 红色 `PatternFill("solid", fgColor="FFC7CE")`
- CAS 防火墙导出实际值：Allowed / Blocked（不是 Denied/Timeout）

### 数值字段处理
Hits 等数值字段转为 int 类型便于排序求和，用 try/except 防止非数字值

### 先输出 Markdown 汇总再被追问 Excel（高频）
当用户说"整理表格"时，第一反应应该是生成 Excel，而不是先输出 Markdown 文本汇总。
Markdown 汇总是多余步骤 — 用户已经有 CSV，不需要再看一遍纯文本表格。
正确流程：读取 CSV → 分析结构 → 直接生成 Excel → 交付。
只有用户明确说"先分析一下"或"给我看看概要"时才输出纯文本。

### 数据分类逻辑必须内置到 Excel 中
不要只在终端打印分类统计，要把分类维度（按IP/按端口/按协议等）做成独立 Sheet。
用户要的是可交互的 Excel（自动筛选、着色），不是终端输出的文字报告。

## Excel 后处理优化（用户偏好）

用户明确要求生成的Excel报告必须满足以下条件：

### 1. 自动筛选功能
为所有Sheet的第一行启用自动筛选，让用户可以按任意列筛选数据：
```python
from openpyxl.utils import get_column_letter

for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    if ws.max_row > 0 and ws.max_column > 0:
        last_col_letter = get_column_letter(ws.max_column)
        last_row = ws.max_row
        ws.auto_filter.ref = f"A1:{last_col_letter}{last_row}"
```

### 2. 数据格式优化（避免排序错误）
检查每一列的数据类型，确保数字列是数字格式，文本列是文本格式：
```python
def is_numeric_value(value):
    """检查值是否为数字类型"""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            int(value)
            return True
        except ValueError:
            try:
                float(value)
                return True
            except ValueError:
                return False
    return False

def is_numeric_column(values):
    """检查一列是否主要是数字（超过80%的非空值是数字）"""
    non_empty = [v for v in values if v is not None and str(v).strip() != '']
    if not non_empty:
        return False
    numeric_count = sum(1 for v in non_empty if is_numeric_value(v))
    return numeric_count / len(non_empty) > 0.8

# 对每一列应用格式
for col in range(1, ws.max_column + 1):
    column_values = [ws.cell(row=r, column=col).value for r in range(2, ws.max_row + 1)]
    
    if is_numeric_column(column_values):
        # 数字列：转换为数字，设置数字格式
        for row in range(2, ws.max_row + 1):
            cell = ws.cell(row=row, column=col)
            if cell.value and str(cell.value).strip():
                try:
                    cell.value = int(cell.value) if '.' not in str(cell.value) else float(cell.value)
                except ValueError:
                    pass
            cell.number_format = '0'
    else:
        # 文本列：确保为文本格式
        for row in range(2, ws.max_row + 1):
            cell = ws.cell(row=row, column=col)
            if cell.value is not None and not isinstance(cell.value, str):
                cell.value = str(cell.value)
            cell.number_format = '@'
```

**典型数字列**：连接数、端口号、命中次数、统计计数
**典型文本列**：IP地址、协议名称、服务名称、设备名称、动作状态

### 3. 后处理执行顺序
1. 生成Excel并保存（原始版本）
2. 重新加载文件进行后处理（避免openpyxl内存问题）
3. 应用自动筛选
4. 应用数据格式优化
5. 保存为新版本（避免覆盖原文件导致权限冲突）

## 文件权限问题处理（Pitfall补充）

当原文件被Excel打开或其他进程占用时，写入会失败（Permission denied）。

**解决方案**：创建带时间戳的新版本文件，不覆盖原文件：
```python
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = os.path.join(output_dir, f"Report_{timestamp}.xlsx")
```

**验证**：检查是否有 `~$` 开头的临时文件（表示Excel正在打开该文件）：
```bash
ls -la /path/to/directory/ | grep "~\$"
```

## 进度显示规范（强制）
- 必须按 [N/M] 格式显示进度，每步完成时给出进度更新
- 典型步骤划分：[1/5] 读取 → [2/5] 分析 → [3/5] 生成 → [4/5] 保存 → [5/5] 验证
- 验证步骤必须用 `ls -lh` 确认文件存在且大小合理
- 最终输出包含：文件路径、各 Sheet 名称和数据条数

## 回答风格（强制）
- 专业、严谨、简洁，无多余解释
- 不确定时必须询问用户，不推测
- 关键操作前必须获得用户确认

## 非微软项目分析工作流
当需要从采集数据中识别非微软项目（迁移重点关注项）时：
1. 读取所有 CSV，用关键词匹配判断是否为微软项目
2. 微软服务识别：检查服务名（已知列表）、Publisher、PathName、TaskPath
3. 非微软项目标记 `Is_Microsoft=No`，高亮浅红色背景
4. Risk_Level 列：HIGH（红色）/ MEDIUM（橙色）/ LOW（绿色）
5. 风险等级规则见 `references/non_ms_analysis_rules.md`
6. 输出包含所有项目的 Excel（含 Is_Microsoft + Risk_Level 列），可按列筛选

分析脚本必须兼容两种 CSV 格式：有 Is_Microsoft 列（v4脚本）和无 Is_Microsoft 列（旧版脚本），无列时用关键词回退判断。

## 参考文件
- `templates/openpyxl_styles.py` — 样式函数库（直接 import 复用）
- `templates/merge_excel.py` — Excel 合并脚本模板（含完整可运行代码）
- `references/bosch_firewall_csv_format.md` — Bosch 防火墙连接表字段格式参考
- `references/server_migration_inventory.md` — Windows Server 迁移资产清点采集要点
- `references/non_ms_analysis_rules.md` — 非微软项目识别规则和风险等级定义

