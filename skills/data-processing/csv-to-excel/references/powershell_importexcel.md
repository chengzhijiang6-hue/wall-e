# PowerShell ImportExcel 模块参考

## 模块简介
ImportExcel 是 PowerShell 的第三方模块，无需安装 Microsoft Excel 即可操作 Excel 文件。
支持创建多 Sheet、格式化、图表、数据透视表等。

## 安装
```powershell
Install-Module -Name ImportExcel -Force -Scope CurrentUser -SkipPublisherCheck
Import-Module ImportExcel
```

## 核心命令

### Export-Excel（最常用）
```powershell
# 基本用法：追加 Sheet 到已有文件
$data | Export-Excel -Path "C:\report.xlsx" -WorksheetName "Sheet1" -AutoSize -BoldTopRow -FreezeTopRow

# 首次创建（自动创建文件）
$data | Export-Excel -Path "C:\report.xlsx" -WorksheetName "First" -AutoSize

# 追加到已有文件（自动创建新 Sheet）
$data2 | Export-Excel -Path "C:\report.xlsx" -WorksheetName "Second" -Append
```

### 常用参数
| 参数 | 作用 |
|------|------|
| -Path | 输出文件路径 |
| -WorksheetName | Sheet 名称 |
| -AutoSize | 自动列宽 |
| -BoldTopRow | 首行加粗 |
| -FreezeTopRow | 冻结首行 |
| -Append | 追加到已有文件 |
| -TableName | 创建 Excel 表格（带筛选） |
| -PassThru | 返回 ExcelPackage 对象（高级操作） |

## CSV → Excel 改造模式

### 原始（多 CSV 输出）
```powershell
$results1 | Export-Csv -Path "$path\1_Data.csv" -NoTypeInformation -Encoding UTF8
$results2 | Export-Csv -Path "$path\2_Services.csv" -NoTypeInformation -Encoding UTF8
```

### 改造后（单 Excel 多 Sheet）
```powershell
$excelFile = "$path\Report.xlsx"
if (Test-Path $excelFile) { Remove-Item $excelFile -Force }

$results1 | Export-Excel -Path $excelFile -WorksheetName "1_Data" -AutoSize -BoldTopRow -FreezeTopRow
$results2 | Export-Excel -Path $excelFile -WorksheetName "2_Services" -AutoSize -BoldTopRow -FreezeTopRow
```

## 注意事项
- 模块从 PowerShell Gallery 安装，需要外网或代理访问
- 企业环境可能被 Group Policy 限制 Install-Module，需管理员权限
- -Append 参数在首次写入时不需要，第二次写入才需要
- -NoTypeInformation 是 CSV 专用参数，Export-Excel 不需要
