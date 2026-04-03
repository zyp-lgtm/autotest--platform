# 使用本地浏览器执行UI测试

## 概述

测试平台支持使用本地安装的Chrome/Edge浏览器来执行UI测试，无需在Docker容器中安装浏览器。

## 优势

- ✅ **无需在Docker中安装浏览器** - 节省磁盘空间和时间
- ✅ **可视化执行过程** - 可以看到浏览器实际操作
- ✅ **更快的执行速度** - 本地浏览器性能更好
- ✅ **方便调试** - 可以使用Chrome DevTools

## 步骤

### 1. 启动本地Chrome浏览器（支持远程调试）

在macOS上执行：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug
```

或者使用Chrome快捷方式：

```bash
open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

**注意**：
- 端口 `9222` 是Chrome DevTools Protocol默认端口
- `--user-data-dir` 创建独立的用户配置目录，避免影响现有Chrome配置

### 2. 在任务中配置"打开浏览器"关键字

**重要**: `use_local` 和 `remote_url` 参数需要通过 **"打开浏览器"** 关键字的参数来配置。

#### 方式1: 使用 `use_local` 参数（推荐）

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

#### 方式2: 使用 `remote_url` 参数

连接到指定的远程浏览器：

```json
{
  "keyword": "打开浏览器",
  "parameters": {
    "remote_url": "ws://host.docker.internal:9222",
    "headless": false
  }
}
```

### 3. 查看执行过程

浏览器会自动打开并执行测试步骤，你可以看到：
- 页面导航
- 元素点击
- 文本输入
- 等待操作

## 浏览器配置选项

"打开浏览器"关键字支持的参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `use_local` | boolean | false | 连接到本地浏览器（host.docker.internal:9222） |
| `remote_url` | string | null | 远程浏览器WebSocket URL（如 ws://192.168.1.100:9222） |
| `headless` | boolean | true | 是否无头模式（false=显示浏览器窗口） |
| `viewport` | object | {"width": 1920, "height": 1080} | 浏览器视口大小 |
| `timeout` | integer | 30000 | 超时时间（毫秒） |

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
│  │ 端口: 9222 │  │
│  └─────────────┘  │
└─────────────────┘
```

Docker容器通过 `host.docker.internal` 访问宿主机服务。

## 故障排查

### 问题1: 连接被拒绝

```
Error: Connection refused
```

**解决方案**: 确保Chrome浏览器已经启动并监听9222端口

```bash
# 检查端口是否监听
lsof -i :9222
```

### 问题2: 无法连接到本地浏览器

```
Error: Unable to connect to browser
```

**解决方案**:
1. 确保Chrome使用了 `--remote-debugging-port=9222` 参数
2. 检查防火墙设置
3. 尝试使用 `0.0.0.0:9222` 而不是 `127.0.0.1:9222`

### 问题3: Docker无法访问宿主机

**解决方案**:
- Docker Desktop for Mac: 自动支持 `host.docker.internal`
- Linux: 需要使用 `--network=host` 模式
- Windows: 使用 `host.docker.internal`

## 示例：完整测试流程

```bash
# 1. 启动本地Chrome
open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug

# 2. 创建包含本地浏览器配置的任务（通过API或UI）
# 任务的第一个步骤应该是 "打开浏览器" 关键字，并设置 use_local: true

# 3. 执行任务
curl 'http://localhost:8000/api/v1/ui/tasks/{task_id}/execute' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'

# 4. 查看执行记录
curl 'http://localhost:8000/api/v1/ui/tasks/{task_id}/executions?limit=1' \
  -H "Authorization: Bearer $TOKEN"
```

## 注意事项

1. **不要使用日常使用的Chrome** - 使用 `--user-data-dir` 创建独立配置
2. **执行前关闭其他Chrome实例** - 避免端口冲突
3. **非headless模式会显示浏览器窗口** - 可以看到实际操作
4. **测试完成后Chrome会保持打开** - 需要手动关闭或复用
5. **本地/远程连接仅支持 Chromium** - Firefox 和 Webkit 不支持 CDP 连接

## 高级配置

### 指定远程浏览器（其他机器）

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
