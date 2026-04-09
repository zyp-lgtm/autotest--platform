# 测试自动化平台 API 使用指南

> **版本**: 1.0.0
> **基础路径**: `http://localhost:8000/api/v1`
> **认证方式**: Bearer Token (JWT)

---

## 📋 目录

- [认证](#认证)
- [关键字管理](#关键字管理)
- [任务管理](#任务管理)
- [场景管理](#场景管理)
- [用例管理](#用例管理)
- [执行管理](#执行管理)
- [错误处理](#错误处理)
- [状态码](#状态码)

---

## 🔐 认证

### 1. 用户注册

**请求**:
```http
POST /api/v1/auth/register HTTP/1.1
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

**响应** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**错误响应** (400 Bad Request):
```json
{
  "detail": "Username already registered"
}
```

### 2. 用户登录

**请求**:
```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=testuser&password=password123
```

**响应** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**错误响应** (401 Unauthorized):
```json
{
  "detail": "Incorrect username or password"
}
```

### 3. 使用令牌

在请求头中添加令牌：
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🎯 关键字管理

### 1. 获取关键字列表

**请求**:
```http
GET /api/v1/ui/keywords/?category=ui&enabled_only=true HTTP/1.1
Authorization: Bearer <token>
```

**查询参数**:
- `category` (可选): 过滤类别 (ui, assertion, api)
- `enabled_only` (可选): 仅显示有效关键字 (true/false)

**响应** (200 OK):
```json
[
  {
    "id": "kw-001",
    "name": "CLICK",
    "category": "ui",
    "description": "点击页面元素",
    "parameter_schema": {
      "type": "object",
      "properties": {
        "selector": {
          "type": "string",
          "description": "CSS选择器或XPath"
        },
        "force": {
          "type": "boolean",
          "description": "强制点击",
          "default": false
        }
      },
      "required": ["selector"]
    },
    "example": {
      "selector": "#submit-button",
      "force": true
    }
  },
  {
    "id": "kw-002",
    "name": "INPUT",
    "category": "ui",
    "description": "在输入框中输入文本",
    "parameter_schema": {
      "type": "object",
      "properties": {
        "selector": {
          "type": "string"
        },
        "text": {
          "type": "string"
        },
        "clear_first": {
          "type": "boolean",
          "default": true
        }
      },
      "required": ["selector", "text"]
    },
    "example": {
      "selector": "#username",
      "text": "testuser",
      "clear_first": true
    }
  }
]
```

### 2. 常用关键字

#### UI 关键字

| 关键字 | 描述 | 必需参数 |
|--------|------|---------|
| NAVIGATE | 导航到URL | url |
| CLICK | 点击元素 | selector |
| INPUT | 输入文本 | selector, text |
| WAIT_FOR_ELEMENT | 等待元素出现 | selector |
| SCREENSHOT | 截图 | path (可选) |
| CLOSE_BROWSER | 关闭浏览器 | 无 |
| SWITCH_TAB | 切换标签页 | index |
| GO_BACK | 后退 | 无 |
| REFRESH | 刷新页面 | 无 |
| DOUBLE_CLICK | 双击元素 | selector |

#### 断言关键字

| 关键字 | 描述 | 必需参数 |
|--------|------|---------|
| ASSERT_TEXT | 断言文本 | selector, text |
| ASSERT_VISIBLE | 断言元素可见 | selector |
| ASSERT_ELEMENT_COUNT | 断言元素数量 | selector, count |

---

## 📝 任务管理

### 1. 创建任务

**请求**:
```http
POST /api/v1/tasks?project_id=<project_id> HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "登录测试任务",
  "description": "测试用户登录功能",
  "task_type": "ui",
  "tags": ["login", "smoke"],
  "execution_config": {
    "browser": "chromium",
    "headless": true,
    "timeout": 30000
  }
}
```

**响应** (200 OK):
```json
{
  "id": "task-001",
  "project_id": "proj-001",
  "name": "登录测试任务",
  "description": "测试用户登录功能",
  "task_type": "ui",
  "scenario_ids": [],
  "tags": ["login", "smoke"],
  "execution_config": {
    "browser": "chromium",
    "headless": true,
    "timeout": 30000
  },
  "report_config": {},
  "created_by": "user-001",
  "created_at": "2026-04-09T10:00:00Z"
}
```

### 2. 列出任务

**请求**:
```http
GET /api/v1/tasks?project_id=<project_id> HTTP/1.1
Authorization: Bearer <token>
```

**响应** (200 OK):
```json
[
  {
    "id": "task-001",
    "name": "登录测试任务",
    "description": "测试用户登录功能",
    "task_type": "ui",
    "tags": ["login", "smoke"],
    "created_at": "2026-04-09T10:00:00Z"
  }
]
```

### 3. 获取任务详情

**请求**:
```http
GET /api/v1/tasks/<task_id> HTTP/1.1
Authorization: Bearer <token>
```

### 4. 更新任务

**请求**:
```http
PUT /api/v1/tasks/<task_id> HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "更新后的任务名称",
  "description": "更新后的描述"
}
```

### 5. 删除任务

**请求**:
```http
DELETE /api/v1/tasks/<task_id> HTTP/1.1
Authorization: Bearer <token>
```

---

## 🎬 场景管理

### 1. 创建场景

**请求**:
```http
POST /api/v1/ui/scenarios?task_id=<task_id> HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "登录场景",
  "description": "用户登录主流程",
  "scenario_type": "ui",
  "execution_order": 1,
  "tags": ["happy-path"]
}
```

**响应** (200 OK):
```json
{
  "id": "scenario-001",
  "task_id": "task-001",
  "project_id": "proj-001",
  "name": "登录场景",
  "description": "用户登录主流程",
  "scenario_type": "ui",
  "case_ids": [],
  "execution_order": 1,
  "tags": ["happy-path"],
  "created_at": "2026-04-09T10:00:00Z"
}
```

### 2. 列出场景

**请求**:
```http
GET /api/v1/ui/scenarios?task_id=<task_id> HTTP/1.1
Authorization: Bearer <token>
```

---

## 🧪 用例管理

### 1. 创建用例

**请求**:
```http
POST /api/v1/ui/scenarios/<scenario_id>/cases HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "正确账号登录",
  "description": "使用正确的用户名和密码登录",
  "case_type": "ui",
  "priority": "P1",
  "data_bindings": {
    "username": "testuser",
    "password": "password123"
  },
  "browser_config": {
    "viewport": {"width": 1920, "height": 1080}
  },
  "tags": ["positive"]
}
```

**响应** (200 OK):
```json
{
  "id": "case-001",
  "scenario_id": "scenario-001",
  "project_id": "proj-001",
  "name": "正确账号登录",
  "description": "使用正确的用户名和密码登录",
  "case_type": "ui",
  "priority": "P1",
  "step_ids": [],
  "data_bindings": {
    "username": "testuser",
    "password": "password123"
  },
  "browser_config": {
    "viewport": {"width": 1920, "height": 1080}
  },
  "tags": ["positive"],
  "created_at": "2026-04-09T10:00:00Z"
}
```

### 2. 添加步骤到用例

**请求**:
```http
POST /api/v1/ui/cases/<case_id>/steps HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "keyword_id": "kw-001",
  "step_name": "打开登录页面",
  "step_type": "ui",
  "step_order": 1,
  "parameters": {
    "selector": "#login-link",
    "force": true
  },
  "enabled": true,
  "continue_on_failure": false,
  "screenshot_config": {
    "on_error": true,
    "on_success": false
  }
}
```

---

## ▶️ 执行管理

### 1. 执行任务

**请求**:
```http
POST /api/v1/tasks/<task_id>/execute HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "mode": "sequential",
  "max_retries": 1
}
```

**响应** (200 OK):
```json
{
  "execution_id": "exec-001",
  "task_id": "task-001",
  "status": "running",
  "started_at": "2026-04-09T10:00:00Z"
}
```

### 2. 查询执行状态

**请求**:
```http
GET /api/v1/tasks/executions/<execution_id> HTTP/1.1
Authorization: Bearer <token>
```

**响应** (200 OK):
```json
{
  "id": "exec-001",
  "task_id": "task-001",
  "status": "completed",
  "result": "pass",
  "total_scenarios": 1,
  "total_steps": 5,
  "passed_steps": 5,
  "failed_steps": 0,
  "started_at": "2026-04-09T10:00:00Z",
  "completed_at": "2026-04-09T10:01:30Z",
  "duration": 90.5,
  "scenario_executions": [...]
}
```

### 3. 获取执行报告

**请求**:
```http
GET /api/v1/tasks/executions/<execution_id>/report HTTP/1.1
Authorization: Bearer <token>
```

---

## ⚠️ 错误处理

### 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误

#### 1. 认证错误 (401)

```json
{
  "detail": "Could not validate credentials"
}
```

**解决方案**:
- 检查令牌是否有效
- 重新登录获取新令牌

#### 2. 权限错误 (403)

```json
{
  "detail": "Not enough permissions"
}
```

**解决方案**:
- 确认你有该资源的访问权限
- 联系管理员授权

#### 3. 资源未找到 (404)

```json
{
  "detail": "Task not found"
}
```

**解决方案**:
- 检查资源 ID 是否正确
- 确认资源是否存在

#### 4. 验证错误 (422)

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**解决方案**:
- 检查请求参数是否完整
- 确认参数类型正确

#### 5. 服务器错误 (500)

```json
{
  "detail": "Internal server error"
}
```

**解决方案**:
- 检查服务器日志
- 联系技术支持

---

## 📊 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源未找到 |
| 422 | 验证失败 |
| 429 | 请求过于频繁（速率限制） |
| 500 | 服务器内部错误 |

---

## 🚀 快速开始

### 1. 准备工作

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端服务
cd backend
python3 -m uvicorn app.main:app --reload

# 服务运行在 http://localhost:8000
```

### 2. 获取令牌

```bash
# 注册用户
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# 登录获取令牌
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

### 3. 使用 API

```bash
# 获取关键字列表
curl http://localhost:8000/api/v1/ui/keywords/ \
  -H "Authorization: Bearer <token>"

# 创建任务
curl -X POST "http://localhost:8000/api/v1/tasks?project_id=<project_id>" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试任务",
    "task_type": "ui"
  }'

# 执行任务
curl -X POST http://localhost:8000/api/v1/tasks/<task_id>/execute \
  -H "Authorization: Bearer <token>"
```

---

## 📚 相关资源

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **项目 README**: README.md
- **快速开始**: QUICK_START.md

---

## 🔄 API 版本历史

### v1.0.0 (2026-04-09)
- ✅ 认证 API
- ✅ 关键字 API
- ✅ 任务 API
- ✅ 场景 API
- ✅ 用例 API
- ✅ 执行 API

---

*最后更新: 2026-04-09*
