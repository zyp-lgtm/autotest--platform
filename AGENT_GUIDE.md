# 本地 Agent 执行模式

## 架构说明

测试平台支持将测试任务下发到用户本地机器上执行，而不是在服务器上执行。

```
┌─────────────────────────────────────┐
│      服务器（部署在远程）              │
│  ┌───────────────────────────────┐  │
│  │  测试平台后端 API              │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ Agent 管理器             │  │  │
│  │  │  - 管理已连接的 Agent    │  │  │
│  │  │  - 分发测试任务          │  │  │
│  │  │  - 接收执行结果          │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
              │
              │ WebSocket
              │
              ▼
┌─────────────────────────────────────┐
│      用户本地机器                      │
│  ┌───────────────────────────────┐  │
│  │  本地 Agent                    │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ Playwright               │  │  │
│  │  │  - 本地浏览器执行         │  │  │
│  │  │  - 实时反馈结果           │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## 使用场景

- **需要可视化执行** - 在本地看到浏览器操作过程
- **特定环境测试** - 需要特定的本地环境（如特定浏览器插件）
- **性能优化** - 分担服务器压力
- **调试方便** - 可以直接在本地调试

## 快速开始

### 1. 启动本地 Agent

在用户本地机器上运行：

```bash
./scripts/start-agent.sh
```

或者指定服务器地址：

```bash
./scripts/start-agent.sh ws://your-server.com:8000/agent
```

输出示例：

```
==========================================
  测试平台 - 本地执行 Agent
==========================================

检查依赖...
创建虚拟环境...
激活虚拟环境...
安装依赖...
✓ 依赖检查完成

==========================================
  配置
==========================================

服务器: ws://localhost:8000/agent

==========================================

启动 Agent...
按 Ctrl+C 停止

初始化 Agent: abc-123-def
正在连接到服务器: ws://localhost:8000/agent
✓ 已连接到服务器
已注册 Agent: abc-123-def
```

### 2. 查看已连接的 Agent

```bash
# 获取 token
TOKEN=$(curl -s 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-raw 'username=demo&password=demo123' | jq -r '.access_token')

# 查看所有 Agent
curl 'http://localhost:8000/api/v1/agents' \
  -H "Authorization: Bearer $TOKEN"
```

返回示例：

```json
{
  "agents": {
    "abc-123-def": {
      "browser_types": ["chromium", "firefox", "webkit"],
      "platform": "darwin",
      "headless": false,
      "connected_at": "2026-04-03T10:30:00"
    }
  },
  "count": 1
}
```

### 3. 下发测试任务

```bash
curl 'http://localhost:8000/api/v1/agents/dispatch' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "agent_id": "abc-123-def",
    "task_id": "test-task-001",
    "browser_type": "chromium",
    "headless": false,
    "steps": [
      {"action": "navigate", "parameters": {"url": "https://www.baidu.com"}},
      {"action": "input", "parameters": {"selector": "#kw", "text": "测试"}},
      {"action": "click", "parameters": {"selector": "#su"}},
      {"action": "screenshot", "parameters": {"path": "test.png"}}
    ]
  }'
```

## Agent 支持的操作

| 操作 | 参数 | 说明 |
|------|------|------|
| `navigate` | url | 导航到指定 URL |
| `click` | selector | 点击元素 |
| `input` | selector, text | 输入文本 |
| `wait` | selector, timeout | 等待元素出现 |
| `screenshot` | path | 截图 |

## API 端点

### 获取所有 Agent

```
GET /api/v1/agents
```

### 获取指定 Agent

```
GET /api/v1/agents/{agent_id}
```

### 下发任务

```
POST /api/v1/agents/dispatch

{
  "agent_id": "string",
  "task_id": "string",
  "browser_type": "chromium",
  "headless": false,
  "url": "string",
  "steps": [...]
}
```

### 关闭浏览器

```
POST /api/v1/agents/{agent_id}/close
```

## 服务器部署配置

如果服务器在远程，需要确保：

1. **WebSocket 端口开放** - 确保 8000 端口可访问
2. **CORS 配置** - 允许跨域 WebSocket 连接
3. **防火墙规则** - 允许入站连接

### 后端配置

在 `backend/app/core/config.py` 中添加：

```python
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://your-frontend.com",
    # 添加 Agent 可能连接的来源
    "ws://localhost:*",
]
```

## 高级配置

### 自定义 Agent ID

```bash
python3 agent.py --agent-id "my-custom-agent-id"
```

### 连接到远程服务器

```bash
python3 agent.py --server "ws://192.168.1.100:8000/agent"
```

### 持久化连接

Agent 会自动重连。如果连接断开，会尝试重新连接。

## 故障排查

### 问题1: Agent 无法连接

```
WebSocket 连接错误: [Errno 61] Connection refused
```

**解决方案**:
1. 确认服务器正在运行
2. 检查防火墙设置
3. 确认 WebSocket 端口正确

### 问题2: 任务下发失败

```
发送任务失败
```

**解决方案**:
1. 确认 Agent 已连接: `GET /api/v1/agents`
2. 检查 agent_id 是否正确
3. 查看 Agent 日志

### 问题3: 浏览器启动失败

**解决方案**:
```bash
# 安装 Playwright 浏览器
playwright install chromium
```

## 安全建议

1. **使用 HTTPS/WSS** - 生产环境使用加密连接
2. **身份验证** - 添加 Token 验证
3. **IP 白名单** - 限制允许连接的 IP 地址
4. **任务验证** - 验证下发的任务内容

## 下一步

- [ ] 添加 Agent 认证机制
- [ ] 支持任务优先级队列
- [ ] 实时执行日志推送
- [ ] 支持批量任务下发
- [ ] Agent 性能监控
