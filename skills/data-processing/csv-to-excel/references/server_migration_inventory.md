# Windows Server 迁移资产清点参考

## 场景
服务器迁移前，清点运行中的服务、计划任务、软件、端口占用、网络共享。
关键需求：区分微软/非微软项目，非微软项目高亮。

## 采集脚本要点（PowerShell）

### 端口映射
- Get-NetTCPConnection -State Listen + Get-NetUDPEndpoint
- 关联进程、服务、安装路径、发布者
- 增加 Is_System_Port、Is_Microsoft 标记列
- 不要过滤系统端口，迁移时也需要确认

### 服务
- Get-WmiObject Win32_Service 获取所有服务（运行+停止）
- Get-AuthenticodeSignature 检查签名判断发布者
- 增加 Is_Microsoft、LogOnAccount、Publisher 列

### 计划任务
- Get-ScheduledTask 获取所有非 Disabled 任务
- TaskPath 以 \Microsoft\ 开头标记为微软任务
- 增加 Is_Microsoft、Author 列

### 已安装软件
- 同时读取 64 位和 32 位注册表 Uninstall 路径
- 按 DisplayName+DisplayVersion 去重

### 网络共享
- 不过滤默认共享，增加 Is_Default 标记列

### IIS / ODBC / 环境变量 / Hosts
- appcmd.exe list site 采集 IIS
- 注册表读取 ODBC DSN（64+32位）
- Get-ChildItem Env: 采集环境变量
- 读取 hosts 文件非注释行

## 宿主机环境
Python 3.14.4 + openpyxl 3.1.5，路径 C:\Programs\Python\python-3.14-amd64\
内网 PyPI 镜像: rb-artifactory.bosch.com

## Is_Microsoft 标记逻辑
所有输出 CSV 增加 Is_Microsoft 列，便于迁移时筛选第三方项目：
- 端口映射：Publisher 包含 "Microsoft" 或系统端口 → Yes
- 服务：Publisher 包含 "Microsoft" 或 StartName 为内置账户 → Yes
- 计划任务：TaskPath 以 `\Microsoft\` 开头 → Yes
- 软件：Publisher 包含 "Microsoft Corporation" → Yes
- Excel 中筛选 Is_Microsoft=No 即可定位需要迁移的第三方项目

## 交付物
- 采集脚本（.ps1）+ 合并脚本（.py）+ 使用说明（.txt）
- 使用说明必须包含：前置条件、操作步骤、输出说明、重点关注项
- 脚本放在 work/scripts/，数据按设备IP目录存放
