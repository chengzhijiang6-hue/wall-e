# WSL 环境下监控 Windows 宿主机资源

## 方法
通过 `powershell.exe` 从 WSL 内部调用 Windows CIM (WMI) 接口。

## CPU 信息
```bash
powershell.exe -Command "Get-CimInstance Win32_Processor | Select-Object LoadPercentage, NumberOfCores, NumberOfLogicalProcessors | ConvertTo-Json"
```

## 内存信息
```bash
powershell.exe -Command "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory, TotalVirtualMemorySize, FreeVirtualMemory | ConvertTo-Json"
```
- `TotalVisibleMemorySize` 和 `FreePhysicalMemory` 单位为 KB，需除以 1024^2 转为 GB

## 磁盘信息（仅系统盘）
```bash
powershell.exe -Command "Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" | Select-Object DeviceID, Size, FreeSpace | ConvertTo-Json"
```
- `DriveType=3` 表示本地固定磁盘
- 多磁盘时返回数组，单磁盘返回对象
- `Size` 和 `FreeSpace` 单位为字节

## 已映射网络驱动器
```bash
powershell.exe -Command "net use"
```
输出示例：
```
Status       Local     Remote                    Network
---------    ----      ------                    -------
             N:        \\bosch.com\dfsrb\DfsCN\LOC\Wx\Project
             U:        \\SGP0FS70.APAC.BOSCH.COM\CZE8WX$
```

## 注意事项
- 输出为 JSON 格式，可直接用 Python `json.loads()` 解析
- `powershell.exe` 自动继承 Windows 用户权限和网络上下文
- UNC 路径（\\\\server\\share）无法直接在 WSL 中用 `ls` 访问，需通过 powershell.exe 操作
- 如果 `powershell.exe` 超时，可能是 Windows Defender 或网络策略阻断

## 关键原则：通过宿主机访问公司网络资源

### 背景
WSL 运行在 Linux 环境中，使用的是 Linux 用户上下文，不具备 Windows 域认证能力。
企业 UNC 路径（如 `\\bosch.com\dfsrb\`）依赖 Windows 域凭据访问。

### 规则
**必须通过宿主机 Windows 访问 UNC 路径，不得在 WSL 本地直接使用自己的凭证尝试访问。**

### 正确做法
```bash
# ✅ 通过 powershell.exe 使用宿主机认证访问
powershell.exe -Command "Get-Content '\\bosch.com\dfsrb\DfsCN\loc\Wx\path\to\file.txt'"

# ✅ 通过 cmd.exe 使用宿主机认证访问
cmd.exe /c "type \\bosch.com\dfsrb\DfsCN\loc\Wx\path\to\file.txt"

# ✅ 通过 explorer.exe 在宿主机文件资源管理器中打开
explorer.exe "\\bosch.com\dfsrb\DfsCN\loc\Wx\path\to\folder"

# ✅ 检查已映射的网络驱动器
powershell.exe -Command "net use"
```

### 错误做法
```bash
# ❌ 在 WSL 直接访问 UNC 路径（无域上下文，会失败）
ls //bosch.com/dfsrb/...
cat //bosch.com/dfsrb/...
```

### 文件读取失败排查
| 症状 | 原因 | 解决 |
|------|------|------|
| `PowerShell 解析为 C:\...` | WSL 自动将 UNC 路径前缀转为 C:\ | 确保路径引号正确，使用单引号 |
| `System error 67` | 网络名找不到 | 路径不存在或权限不足 |
| `System error 1702` | 绑定句柄无效 | DFS 名称解析失败，尝试直连服务器 |
| `Test-NetConnection port 445 OK` 但无法列出目录 | 有网络连接但无目录权限 | 需要域认证，检查是否有权限 |
