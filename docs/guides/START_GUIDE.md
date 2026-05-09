# 测试自动化平台 - 启动指南

**最后更新**: 2026-04-09
**项目路径**: `/Users/apple/aicode/.worktrees/test-platform`

## 📋 项目概述

测试自动化平台是一个基于 AI 的智能测试平台，支持：
- UI 自动化测试（Playwright）
- API 自动化测试
- 实时执行监控
- 调试信息收集
- 可视化测试报告

### 技术栈

| 组件 | 技术 | 端口 |
|------|------|------|
| 后端 | FastAPI + Python 3.12 | 8000 |
| 前端 | React 19 + Vite + TypeScript | 3000 |
| 数据库 | SQLite | - |
| Agent | Python WebSocket | - |

## 🚀 快速启动（从任意路径）

### 一键启动所有服务

```bash
# 方式 1: 使用启动脚本（推荐）
/Users/apple/aicode/.worktrees/test-platform/start_all.sh

# 方式 2: 使用 tmux 分屏启动
/Users/apple/aicode/.worktrees/test-platform/start_tmux.sh

# 方式 3: 逐个启动（见下方详细命令）
```

### 启动后端服务

```bash
cd /Users/apple/aicode/.worktrees/test-platform/backend && \
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**后台启动**:
```bash
cd /Users/apple/aicode/.worktrees/test-platform/backend && \
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
> /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid
```

### 启动前端服务

```bash
cd /Users/apple/aicode/.worktrees/test-platform/frontend && \
npm run dev
```

**后台启动**:
```bash
cd /Users/apple/aicode/.worktrees/test-platform/frontend && \
nohup npm run dev > /tmp/frontend.log 2>&1 &
echo $! > /tmp/frontend.pid
```

### 启动 Agent 服务

```bash
cd /Users/apple/aicode/.worktrees/test-platform/agent && \
./start_agent.sh
```

## 📝 完整启动脚本

### 1. 创建启动脚本

将以下脚本保存为 `~/start-test-platform.sh`：

```bash
#!/bin/bash

# 测试自动化平台启动脚本
# 使用方式: bash ~/start-test-platform.sh

PROJECT_DIR="/Users/apple/aicode/.worktrees/test-platform"

echo "🚀 启动测试自动化平台..."

# 1. 启动后端
echo "📡 启动后端服务 (http://localhost:8000)..."
cd "$PROJECT_DIR/backend"
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
    > /tmp/test-platform-backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > /tmp/test-platform-backend.pid
echo "   后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 2. 启动前端
echo "🎨 启动前端服务 (http://localhost:3000)..."
cd "$PROJECT_DIR/frontend"
nohup npm run dev > /tmp/test-platform-frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/test-platform-frontend.pid
echo "   前端 PID: $FRONTEND_PID"

# 等待前端启动
sleep 3

# 3. 启动 Agent
echo "🤖 启动 Agent 服务..."
cd "$PROJECT_DIR/agent"
./start_agent.sh

# 4. 显示服务状态
echo ""
echo "✅ 所有服务已启动！"
echo ""
echo "📍 访问地址："
echo "   前端:     http://localhost:3000"
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/docs"
echo "   健康检查: http://localhost:8000/api/v1/health"
echo ""
echo "📊 服务进程："
echo "   后端 PID: $BACKEND_PID"
echo "   前端 PID: $FRONTEND_PID"
echo ""
echo "📝 查看日志："
echo "   后端: tail -f /tmp/test-platform-backend.log"
echo "   前端: tail -f /tmp/test-platform-frontend.log"
echo ""
echo "🛑 停止服务："
echo "   kill $BACKEND_PID  # 停止后端"
echo "   kill $FRONTEND_PID # 停止前端"
echo ""
```

### 2. 创建停止脚本

将以下脚本保存为 `~/stop-test-platform.sh`：

```bash
#!/bin/bash

echo "🛑 停止测试自动化平台..."

# 读取 PID 并杀掉进程
if [ -f /tmp/test-platform-backend.pid ]; then
    BACKEND_PID=$(cat /tmp/test-platform-backend.pid)
    kill $BACKEND_PID 2>/dev/null && echo "✓ 后端已停止 (PID: $BACKEND_PID)"
    rm /tmp/test-platform-backend.pid
fi

if [ -f /tmp/test-platform-frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/test-platform-frontend.pid)
    kill $FRONTEND_PID 2>/dev/null && echo "✓ 前端已停止 (PID: $FRONTEND_PID)"
    rm /tmp/test-platform-frontend.pid
fi

# 杀掉 Agent
pkill -f "python.*agent.py" && echo "✓ Agent 已停止"

echo "✅ 所有服务已停止"
```

### 3. 使脚本可执行

```bash
chmod +x ~/start-test-platform.sh
chmod +x ~/stop-test-platform.sh
```

## 🎯 使用方式

### 从任意位置启动

```bash
# 启动所有服务
bash ~/start-test-platform.sh

# 停止所有服务
bash ~/stop-test-platform.sh
```

### 检查服务状态

```bash
# 检查健康状态
curl http://localhost:8000/api/v1/health | python3 -m json.tool

# 检查端口占用
lsof -i :8000  # 后端
lsof -i :3000  # 前端
```

### 查看日志

```bash
# 实时查看后端日志
tail -f /tmp/test-platform-backend.log

# 实时查看前端日志
tail -f /tmp/test-platform-frontend.log

# 查看最近 50 行后端日志
tail -50 /tmp/test-platform-backend.log
```

## 🔧 环境要求

### Python 环境

- Python 3.11+
- 依赖包在 `backend/requirements.txt`

### Node.js 环境

- Node.js 18+
- npm 9+

### 系统要求

- macOS / Linux
- 至少 4GB RAM
- 至少 2GB 可用磁盘空间

## 📊 验证服务启动

### 1. 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

预期输出：
```json
{
  "overall": "healthy",
  "services": [
    {"id": "backend", "status": "healthy"},
    {"id": "frontend", "status": "healthy"},
    {"id": "agent", "status": "healthy"}
  ]
}
```

### 2. 访问前端

浏览器打开：http://localhost:3000

### 3. 测试 API

```bash
# 获取所有任务
curl http://localhost:8000/api/v1/ui/tasks?project_id=550e8400-e29b-41d4-a716-446655440000

# 执行任务（需要替换 token）
curl -X POST http://localhost:8000/api/v1/ui/tasks/YOUR_TASK_ID/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  --data-raw '{}'
```

## 🐛 常见问题

### 问题 1: 端口被占用

```bash
# 查找占用进程
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口

# 杀掉进程
kill -9 <PID>

# 或使用不同的端口
# 后端：修改启动命令中的 --port 8000
# 前端：在 frontend/vite.config.ts 中修改 server.port
```

### 问题 2: 后端启动失败

```bash
# 检查 Python 版本
python3 --version  # 应该是 3.11+

# 安装依赖
cd /Users/apple/aicode/.worktrees/test-platform/backend
pip3 install -r requirements.txt

# 检查数据库
ls -la test_platform.db
```

### 问题 3: 前端启动失败

```bash
# 检查 Node 版本
node --version  # 应该是 18+
npm --version

# 安装依赖
cd /Users/apple/aicode/.worktrees/test-platform/frontend
npm install

# 清除缓存
rm -rf node_modules/.vite
```

### 问题 4: Agent 无法连接

```bash
# 检查 Agent 进程
ps aux | grep agent

# 重启 Agent
cd /Users/apple/aicode/.worktrees/test-platform/agent
./start_agent.sh

# 检查 WebSocket 连接
# 后端日志应该显示：WebSocket connection established
```

### 问题 5: 浏览器自动化失败

```bash
# 安装 Playwright 浏览器
cd /Users/apple/aicode/.worktrees/test-platform/backend
python3 -m playwright install chromium

# 验证安装
python3 -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

## 📁 项目结构

```
test-platform/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── main.py         # 应用入口
│   ├── test_platform.db    # SQLite 数据库
│   └── requirements.txt
├── frontend/               # 前端服务
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── pages/          # 页面
│   │   └── main.tsx        # 应用入口
│   ├── package.json
│   └── vite.config.ts
├── agent/                  # Agent 服务
│   ├── agent.py
│   ├── start_agent.sh
│   └── venv/
└── debug/                  # 调试文件
    ├── console/            # 控制台日志
    ├── html/               # HTML 快照
    └── screenshots/        # 失败截图
```

## 🔐 默认账户

```
用户名: demo
密码: demo123
```

## 📖 相关文档

- [API 文档](http://localhost:8000/docs) - Swagger UI
- [开发文档](./README.md) - 项目开发说明
- [任务跟踪](./TASKS_EXECUTION_REPORT_ISSUES.md) - 待解决问题

## 📞 支持

如遇问题，请检查：
1. 服务日志文件
2. 健康检查端点
3. 浏览器控制台
4. 后端 API 文档

---

**祝使用愉快！** 🎉
