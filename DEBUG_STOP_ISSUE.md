# 停止服务调试指南

## 如何测试停止功能

### 1. 打开浏览器开发者工具
- 按 `F12` 或右键点击 → "检查"
- 切换到 "Console"（控制台）标签

### 2. 执行停止操作
1. 点击右上角的系统健康状态指示器
2. 找到"后端 API"服务卡片
3. 点击"停止"按钮

### 3. 检查控制台输出
应该看到以下日志（按顺序）：
```
[ServiceAction] 开始操作: backend stop
[ServiceAction] 调用停止API
[ServiceAction] 停止响应: {success: true, message: "...", async: true}
[ServiceAction] 停止成功，准备更新状态
[ServiceAction] 显示后端提示
[ServiceAction] 已设置手动操作标记
[ServiceAction] 新的健康状态: {name: "后端 API", status: "down", ...}
[ServiceAction] 操作完成，清除操作状态
```

### 4. 预期界面变化
- 后端服务卡片背景变为红色
- 状态文字变为"服务已停止"
- 出现黄色提示框，显示启动命令
- "停止"/"重启"按钮变为"启动"按钮

### 5. 如果没有反应

#### 检查 1: 网络请求
- 切换到 "Network"（网络）标签
- 查找 `services/backend/stop` 请求
- 检查响应是否为 200 OK

#### 检查 2: 认证状态
- 在控制台输入: `localStorage.getItem('token')`
- 如果返回 null，需要重新登录

#### 检查 3: React DevTools
- 安装 React DevTools 扩展
- 切换到 "Components" 标签
- 找到 `HealthStatusIndicator` 组件
- 检查 state:
  - `showBackendTip`: 应该为 true
  - `manualOperation`: 应该有值
  - `health.services[0].status`: 应该为 "down"

### 6. 手动刷新状态
如果停止成功但界面未更新：
- 点击"刷新"按钮
- 或者重新打开健康状态面板

### 7. 重新启动后端
在终端执行：
```bash
bash /Users/apple/aicode/.worktrees/test-platform/backend/start_backend.sh
```

然后在界面点击"知道了"按钮，状态应该自动恢复。

## 常见问题

### Q: 点击停止按钮没反应
A: 检查控制台是否有 `[ServiceAction]` 日志，如果没有，说明点击事件未触发。

### Q: 显示"停止失败"
A: 检查后端是否正在运行，后端停止时无法再次停止。

### Q: 停止后没有提示框
A: 检查 `showBackendTip` 状态，可能被其他逻辑覆盖了。

### Q: 状态变为"已停止"后又变回"正常"
A: 这是因为自动刷新检测到后端还在运行（或者还没完全停止），60秒后会恢复。
