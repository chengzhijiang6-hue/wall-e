# 多 CSV → 多 Sheet Excel 合并模板

## 场景
目标服务器无法连接公网，无法安装 ImportExcel 模块。
脚本输出多个 CSV，由 Agent 或宿主机 Python 合并为单一 xlsx。

## Agent 直接合并（推荐）
当 CSV 文件已复制到本地时，用 execute_code 内的 openpyxl 直接合并。

关键代码模式：
```python
import csv, os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

base = "/mnt/c/Users/CZE8WX/Desktop/work/{project}/源文件"
output = "/mnt/c/Users/CZE8WX/Desktop/work/{project}/合并后/Report.xlsx"

CSV_SHEETS = [
    ("1_File.csv", "Sheet_Name_1"),
    ("2_File.csv", "Sheet_Name_2"),
    # ...
]

# 样式
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill("solid", fgColor="4472C4")
HEADER_ALIGN = Alignment(horizontal="center", vertical="center")
DATA_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
THIN_BORDER = Border(left=Side("thin"), right=Side("thin"), top=Side("thin"), bottom=Side("thin"))
ALT_FILL = PatternFill("solid", fgColor="D9E2F3")
HIGHLIGHT_FILL = PatternFill("solid", fgColor="FFC7CE")  # 用于高亮特定行

def auto_width(ws, max_width=40):
    for col_cells in ws.iter_cols(min_row=1, max_row=ws.max_row):
        max_len = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 4, max_width)

def write_sheet(ws, csv_path, highlight_col=None, highlight_val="No"):
    """写入 CSV 到 Sheet，可选高亮特定列值的行"""
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        ws.cell(1, 1, "No Data")
        return

    # 表头
    for c, val in enumerate(rows[0], 1):
        cell = ws.cell(1, c, value=val)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGN
        cell.border = THIN_BORDER

    # 数据
    headers = rows[0]
    highlight_idx = headers.index(highlight_col) + 1 if highlight_col and highlight_col in headers else None

    for r, row in enumerate(rows[1:], 2):
        should_highlight = False
        for c, val in enumerate(row, 1):
            cell = ws.cell(r, c, value=val)
            cell.alignment = DATA_ALIGN
            cell.border = THIN_BORDER
            if highlight_idx and c == highlight_idx and val == highlight_val:
                should_highlight = True
        # 整行高亮
        if should_highlight:
            for c in range(1, len(row) + 1):
                ws.cell(r, c).fill = HIGHLIGHT_FILL
        elif (r - 2) % 2 == 1:
            for c in range(1, len(row) + 1):
                ws.cell(r, c).fill = ALT_FILL

    ws.freeze_panes = "A2"
    auto_width(ws)

wb = Workbook()
wb.remove(wb.active)
for csv_name, sheet_name in CSV_SHEETS:
    ws = wb.create_sheet(title=sheet_name)
    write_sheet(ws, os.path.join(base, csv_name), highlight_col="Is_Microsoft", highlight_val="No")
wb.save(output)
```

## Windows 控制台编码修复（宿主机 Python 脚本必须）
```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

## 非微软项目高亮
在 CSV 中用 `Is_Microsoft` 列标记（Yes/No），合并时筛选 `Is_Microsoft=No` 的行高亮显示。
适用于服务器迁移场景：快速定位需要迁移的第三方服务/软件/任务。
