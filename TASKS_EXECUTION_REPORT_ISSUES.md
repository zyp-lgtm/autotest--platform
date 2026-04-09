# 执行报告页面失败信息显示问题

**日期**: 2026-04-08
**任务**: 修复前端执行报告页面的失败信息显示

## 问题描述

执行报告页面中，失败步骤没有显示详细的错误信息，缺少：
1. 详细的 error_message
2. debug_info（截图、控制台日志、网络请求等）
3. 执行详情不够丰富

## 当前状态

### ✅ 已完成
- [x] 任务可以成功执行
- [x] 有基本的步骤日志
- [x] 失败步骤有日志级别分类（info/error）
- [x] 前端 DebugPanel 组件已创建（5个标签页）
- [x] 后端 DebugInfoCollector 已实现
- [x] 数据库 debug_info 字段已添加

### ❌ 存在的问题
- [ ] debug_info 没有被正确收集和保存到数据库
- [ ] error_message 经常为 None
- [ ] 前端 ExecutionReport.tsx 显示的失败信息不够详细
- [ ] 浏览器自动化可能没有正确启动

### ⚠️ 部分完成
- [ ] 执行引擎有错误处理，但 debug_info 收集不完整
- [ ] JSON 字段序列化问题已修复，但 UUID 转换可能还有问题

## 根本原因分析

### 1. 执行路径问题
- UI 任务默认通过 Agent 执行
- Agent 执行路径没有实现 debug_info 收集
- **解决方案**: 在执行请求中添加 `"use_agent": false`

### 2. JSON 字段序列化
- SQLite JSON 类型处理有问题
- `case_ids` 和 `step_ids` 存储为 JSON 字符串，但代码期望列表
- **已修复**: 在 executor.py 中添加 JSON 解析逻辑

### 3. debug_info 保存问题
- debug_info 包含 UUID 对象，无法序列化到 JSON
- **已修复**: 将 debug_info 转换为 JSON 字符串再保存

### 4. 浏览器自动化未启动
- 可能 Playwright 浏览器管理器没有正确初始化
- debug_collector 依赖 page 对象来收集信息
- **待解决**: 检查浏览器启动流程

## 待解决事项

### 高优先级
1. **验证浏览器是否正确启动**
   - 检查 PlaywrightBrowser 是否成功启动浏览器
   - 验证 page 对象是否可用
   - 确认 debug_collector 监听器是否设置成功

2. **修复 debug_info 收集流程**
   - 确保步骤失败时触发异常处理
   - 验证 capture_failure_info 方法被调用
   - 检查截图、HTML 快照是否保存成功

3. **完善错误信息记录**
   - 确保 error_message 被正确设置
   - 记录完整的错误堆栈
   - 区分不同类型的错误（超时、元素未找到、断言失败等）

### 中优先级
4. **前端执行报告优化**
   - 在 ExecutionReport.tsx 中更好地显示 error_message
   - 即使没有 debug_info，也要显示可用的信息（日志、错误文本）
   - 添加重试执行的功能

5. **调试文件访问**
   - 确保 `/api/v1/files/debug` 端点工作正常
   - 验证截图文件可以被访问
   - 测试 HTML 快照下载功能

### 低优先级
6. **Agent 执行路径的 debug_info 收集**
   - 修改 Agent 代码，返回 debug_info
   - 或者在后端重新实现一遍收集逻辑

## 执行记录

**最近一次成功执行**:
- 执行ID: `315d7c10-a694-46cc-800c-25b71415ddf2`
- 时间: 2026-04-08 10:44:30 - 10:44:59
- 配置: `{"use_agent": false, "headless": false}`
- 结果: 9 步中 4 步通过，5 步失败

**失败步骤详情**:
1. 等待搜索框出现 - "等待超时: #kw (state=visible)"
2. 点击不存在的元素 - "未知错误"
3. 断言不存在的文本 - "Keyword not found"
4. 输入内容到不存在的元素 - "未知错误"
5. 等待搜索框（会执行） - "等待超时: #kw (state=visible)"

## 相关文件

### 后端
- `/backend/app/services/executor.py` - 执行引擎（已修复 JSON 处理）
- `/backend/app/services/debug_collector.py` - 调试信息收集器
- `/backend/app/services/keyword_engine.py` - 关键字执行引擎
- `/backend/app/services/playwright_browser.py` - 浏览器管理器
- `/backend/app/api/ui/tasks.py` - 任务 API

### 前端
- `/frontend/src/pages/ExecutionReport.tsx` - 执行报告页面
- `/frontend/src/components/debug/DebugPanel.tsx` - 调试面板组件
- `/frontend/src/components/debug/ScreenshotViewer.tsx` - 截图查看器
- `/frontend/src/components/debug/ConsoleLogs.tsx` - 控制台日志
- `/frontend/src/components/debug/NetworkRequests.tsx` - 网络请求
- `/frontend/src/components/debug/ExecutionSteps.tsx` - 执行步骤
- `/frontend/src/types/debug.ts` - 调试信息类型定义

## 测试步骤

### 验证修复
1. 执行任务（禁用 Agent）:
   ```bash
   curl 'http://localhost:3000/api/v1/ui/tasks/190d5cd7-55a4-4649-9248-9e26de4f33f8/execute' \
     -H 'Authorization: Bearer YOUR_TOKEN' \
     -H 'Content-Type: application/json' \
     --data-raw '{"browser_config": {"use_agent": false, "headless": false}}'
   ```

2. 检查 debug_info 是否保存:
   ```python
   # 从数据库查询
   import sqlite3, json
   conn = sqlite3.connect('backend/test_platform.db')
   cursor = conn.cursor()
   cursor.execute("SELECT step_name, debug_info FROM step_executions WHERE result='fail' LIMIT 1")
   row = cursor.fetchone()
   if row and row[1]:
       debug = json.loads(row[1])
       print(f"screenshot: {debug.get('screenshot')}")
       print(f"console_logs: {len(debug.get('console_logs', []))}")
   ```

3. 验证前端显示:
   - 访问执行报告页面
   - 查看失败步骤是否显示 DebugPanel
   - 检查截图、控制台、网络请求标签

## 下次继续

1. 首先检查浏览器启动日志
2. 验证 Playwright 浏览器驱动是否安装
3. 测试 debug_collector 的 capture_failure_info 方法
4. 检查失败步骤的异常处理流程
5. 确保截图和 HTML 文件保存到正确位置

## 代码修改记录

### 已修改文件
1. `backend/app/services/executor.py`:
   - 添加 `import json` 到文件顶部
   - 修复 case_ids 和 step_ids 的 JSON 解析
   - 将 debug_info 转换为 JSON 字符串再保存

2. `backend/app/api/ui/tasks.py`:
   - 在 get_execution 端点添加 debug_info 字段解析

3. `frontend/src/pages/ExecutionReport.tsx`:
   - 集成 DebugPanel 组件

4. 数据库迁移:
   - 添加 step_executions.debug_info 字段

### 待修改文件
1. `backend/app/services/executor.py` - 完善异常处理
2. `backend/app/services/keyword_engine.py` - 确保异常正确抛出
3. `frontend/src/pages/ExecutionReport.tsx` - 优化信息显示

---

**创建时间**: 2026-04-08 18:47
**状态**: 待解决
**优先级**: 高
