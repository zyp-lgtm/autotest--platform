# 使用本地浏览器执行UI测试

## 概述

测试平台**自动支持**使用本地浏览器，无需手动配置！系统会自动检测并使用本地浏览器（如果可用）。

## 🚀 快速开始

### 第一步：启动本地浏览器服务（只需一次）

在项目根目录执行：

```bash
./scripts/start-local-browser.sh
```

**输出示例：**
```
==========================================
  测试平台 - 本地浏览器服务
==========================================

启动 Chrome 浏览器...
等待 Chrome 启动 ✓
Chrome 已启动 (PID: 12345)

✓ 本地浏览器服务已启动

==========================================
  现在您可以直接执行测试任务了！
==========================================
```

### 第二步：重启 Docker 容器（应用代码更改）

```bash
./scripts/restart-backend.sh
```

### 第三步：直接执行任务！

**无需任何配置**，直接执行您的测试任务。系统会自动：
1. 检测本地浏览器是否可用
2. 如果可用，使用本地浏览器（可视化执行）
3. 如果不可用，使用容器内浏览器（后台执行）

```bash
# 直接执行任务，无需任何额外参数
curl 'http://localhost:8000/api/v1/ui/tasks/{task_id}/execute' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

就这样！浏览器会自动在您的 Mac 上打开并执行测试。

## 服务管理

### 查看状态
```bash
./scripts/browser-daemon.sh status
```

### 停止服务
```bash
./scripts/browser-daemon.sh stop
```

### 重启服务
```bash
./scripts/browser-daemon.sh restart
```

### 安装为开机自启动（可选）
```bash
./scripts/browser-daemon.sh install
```

安装后，Chrome 浏览器服务会在系统启动时自动运行。

## 工作原理

```
┌─────────────────────────────────────────┐
│         用户执行测试任务                 │
│    (无需任何额外配置或参数)               │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      测试平台自动检测本地浏览器            │
└─────────────────────────────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  本地浏览器可用   │     │  本地浏览器不可用  │
│  ✅ 使用本地浏览器 │     │  ✅ 使用容器内浏览器 │
│  (可视化执行)     │     │  (后台执行)       │
└─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Docker 容器      │
│  ┌─────────────┐  │
│  │ 后端 API     │  │
│  │  ┌─────────┐ │  │
│  │  │Playwright│─┼──┼──> ws://host.docker.internal:9222
│  │  └─────────┘ │  │
│  └─────────────┘  │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  宿主机 (macOS)   │
│  ┌─────────────┐  │
│  │ Chrome      │  │  ← 由浏览器守护进程管理
│  │ 端口: 9222 │  │
│  └─────────────┘  │
└─────────────────┘
```

## 优势

- ✅ **零配置** - 无需修改任务，自动检测并使用本地浏览器
- ✅ **一键启动** - 运行一次脚本即可
- ✅ **智能回退** - 本地浏览器不可用时自动使用容器内浏览器
- ✅ **可视化执行** - 可以看到浏览器实际操作
- ✅ **更快的执行速度** - 本地浏览器性能更好
- ✅ **方便调试** - 可以使用Chrome DevTools
- ✅ **自动重启** - 守护进程会监控浏览器状态

## 手动控制（高级）

虽然系统会自动检测，但您也可以手动控制：

### 强制使用本地浏览器

在执行请求中指定：

```bash
curl 'http://localhost:8000/api/v1/ui/tasks/{task_id}/execute' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "browser_config": {
      "use_local": true,
      "headless": false
    }
  }'
```

### 强制使用容器内浏览器

```bash
curl 'http://localhost:8000/api/v1/ui/tasks/{task_id}/execute' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "browser_config": {
      "use_local": false,
      "headless": true
    }
  }'
```

### 浏览器配置选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `use_local` | boolean | auto | 连接到本地浏览器（默认自动检测） |
| `remote_url` | string | null | 远程浏览器WebSocket URL |
| `headless` | boolean | true | 是否无头模式（false=显示浏览器窗口） |
| `viewport` | object | {"width": 1920, "height": 1080} | 浏览器视口大小 |
| `timeout` | integer | 30000 | 超时时间（毫秒） |

## 故障排查

### 问题1: 未使用本地浏览器

**症状**: 执行任务时浏览器没有在本地打开

**解决方案**:
```bash
# 检查服务状态
./scripts/browser-daemon.sh status

# 如果未运行，启动它
./scripts/start-local-browser.sh
```

### 问题2: 端口被占用

**症状**: 启动服务时提示端口被占用

**解决方案**:
```bash
# 查看占用端口的进程
lsof -i :9222

# 停止守护进程
./scripts/browser-daemon.sh stop
```

### 问题3: Chrome 未安装

**解决方案**: 安装 Google Chrome
```bash
# 使用 Homebrew 安装
brew install --cask google-chrome

# 或从官网下载
# https://www.google.com/chrome/
```

## 高级配置

### 连接到远程浏览器（其他机器）

```bash
curl 'http://localhost:8000/api/v1/ui/tasks/{task_id}/execute' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "browser_config": {
      "remote_url": "ws://192.168.1.100:9222",
      "headless": false
    }
  }'
```

### 自定义视口大小

```bash
curl 'http://localhost:8000/api/v1/ui/tasks/{task_id}/execute' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "browser_config": {
      "use_local": true,
      "headless": false,
      "viewport": {
        "width": 1920,
        "height": 1080
      }
    }
  }'
```

## 卸载

如果不再需要本地浏览器服务：

```bash
# 停止服务
./scripts/browser-daemon.sh stop

# 如果安装了开机自启动，卸载它
./scripts/browser-daemon.sh uninstall
```

## 注意事项

1. **仅支持 Chromium** - 本地连接仅支持 Chromium 浏览器（Chrome、Edge）
2. **独立的用户配置** - Chrome 使用独立的用户数据目录，不会影响您的日常使用
3. **服务会自动重启** - 如果浏览器意外关闭，守护进程会自动重启它
4. **智能回退** - 如果本地浏览器不可用，系统会自动使用容器内浏览器
