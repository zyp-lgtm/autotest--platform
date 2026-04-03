# 使用本地浏览器执行UI测试

## 概述

测试平台支持使用本地安装的Chrome/Edge浏览器来执行UI测试，无需在Docker容器中安装浏览器。

## 🚀 快速开始（推荐）

### 一键启动本地浏览器服务

在项目根目录执行：

```bash
./scripts/start-local-browser.sh
```

只需要运行一次！浏览器将在后台运行，测试平台可以直接使用。

**输出示例：**
```
==========================================
  测试平台 - 本地浏览器服务
==========================================

正在启动本地浏览器服务...

启动 Chrome 浏览器 (远程调试端口: 9222)...
等待 Chrome 启动 ✓
Chrome 已启动 (PID: 12345)

✓ 本地浏览器服务已启动

==========================================
  现在您可以直接执行测试任务了！
==========================================

使用说明：

1. 在任务的"打开浏览器"关键字中设置:
   {
     "keyword": "打开浏览器",
     "parameters": {
       "use_local": true,
       "headless": false
     }
   }

2. 执行任务，浏览器会自动在您的 Mac 上打开
```

### 在任务中配置

在任务的第一个步骤中，配置"打开浏览器"关键字：

```json
{
  "keyword": "打开浏览器",
  "parameters": {
    "use_local": true,
    "headless": false
  }
}
```

执行任务时，浏览器会自动在您的 Mac 上打开并执行测试！

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

安装后，Chrome 浏览器服务会在系统启动时自动运行，无需手动启动。

## 优势

- ✅ **一键启动** - 运行一次脚本即可
- ✅ **无需在Docker中安装浏览器** - 节省磁盘空间和时间
- ✅ **可视化执行过程** - 可以看到浏览器实际操作
- ✅ **更快的执行速度** - 本地浏览器性能更好
- ✅ **方便调试** - 可以使用Chrome DevTools
- ✅ **自动重启** - 守护进程会监控浏览器状态

## 工作原理

```
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
│  │ Chrome      │  │
│  │ 端口: 9222 │  │  ← 由浏览器守护进程管理
│  └─────────────┘  │
└─────────────────┘
```

Docker容器通过 `host.docker.internal` 访问宿主机服务。

## 浏览器配置选项

"打开浏览器"关键字支持的参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `use_local` | boolean | false | 连接到本地浏览器 |
| `remote_url` | string | null | 远程浏览器WebSocket URL（如 ws://192.168.1.100:9222） |
| `headless` | boolean | true | 是否无头模式（false=显示浏览器窗口） |
| `viewport` | object | {"width": 1920, "height": 1080} | 浏览器视口大小 |
| `timeout` | integer | 30000 | 超时时间（毫秒） |

## 故障排查

### 问题1: 连接被拒绝

```
Error: Connection refused
```

**解决方案**: 运行一键启动脚本
```bash
./scripts/start-local-browser.sh
```

### 问题2: 端口被占用

```
错误: 端口 9222 被其他程序占用
```

**解决方案**: 检查并停止占用端口的程序
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

### 问题4: Docker无法访问宿主机

**解决方案**:
- Docker Desktop for Mac: 自动支持 `host.docker.internal`
- Linux: 需要使用 `--network=host` 模式
- Windows: 使用 `host.docker.internal`

## 高级配置

### 连接到远程浏览器（其他机器）

```json
{
  "keyword": "打开浏览器",
  "parameters": {
    "remote_url": "ws://192.168.1.100:9222",
    "headless": false
  }
}
```

### 自定义视口大小

```json
{
  "keyword": "打开浏览器",
  "parameters": {
    "use_local": true,
    "headless": false,
    "viewport": {
      "width": 1920,
      "height": 1080
    }
  }
}
```

### 设置超时时间

```json
{
  "keyword": "打开浏览器",
  "parameters": {
    "use_local": true,
    "timeout": 60000,
    "headless": false
  }
}
```

## 手动启动（高级用户）

如果您想手动启动 Chrome 而不使用守护进程：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug
```

或使用快捷方式：

```bash
open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

**注意**: 手动启动的 Chrome 不会自动重启，如果浏览器意外关闭需要重新启动。

## 卸载

如果不再需要本地浏览器服务：

```bash
# 停止服务
./scripts/browser-daemon.sh stop

# 如果安装了开机自启动，卸载它
./scripts/browser-daemon.sh uninstall
```

## 注意事项

1. **仅支持 Chromium** - 本地/远程连接仅支持 Chromium 浏览器（Chrome、Edge）
2. **独立的用户配置** - Chrome 使用独立的用户数据目录，不会影响您的日常使用
3. **服务会自动重启** - 如果浏览器意外关闭，守护进程会自动重启它
4. **测试完成后浏览器保持打开** - 可以重复使用，无需每次重启
