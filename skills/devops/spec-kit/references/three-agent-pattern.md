# Three-Agent Collaboration Pattern

用户偏好的大型项目执行方式。

## 角色定义

### 汇总 Agent (Coordinator)
- 整合工作成果，生成进度报告
- 维护项目文档，协调沟通
- 工具：file, session_search, memory

### 监督 Agent (Supervisor)
- 监控进度和质量，检测异常
- 审查代码，纠正偏差
- 工具：terminal, file

### 实施 Agent (Implementer)
- 编码、部署、测试
- 工具：terminal, file, execute_code

## 流程
汇总分配 → 实施执行 → 监督审查 → 汇总记录 → 循环

## 异常处理
监督发现异常 → 分析原因 → 通知汇总 → 实施纠正 → 验证结果

## Pitfalls
- 监督审查大量文件易超时(>600s)，拆为单文件审查
- 子代理中断后已创建文件不丢失，可直接检查
- 2次中断后汇总直接接管审查
