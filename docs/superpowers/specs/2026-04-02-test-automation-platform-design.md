# 测试自动化平台技术设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 测试自动化平台技术设计 |
| 创建日期 | 2026-04-02 |
| 版本 | v1.0 |
| 作者 | Claude |
| 状态 | 待审核 |

---

## 1. 项目概述

### 1.1 项目目标

建设一个支持接口自动化、UI自动化和性能测试的测试自动化平台，面向10人企业测试团队使用。

### 1.2 核心特性

- **关键字驱动测试** - 封装通用和业务关键字，灵活组合
- **四层结构体系** - 任务/场景/用例/步骤，清晰的层次结构
- **类型分离** - UI测试和接口测试独立管理
- **可视化维护** - 界面化管理测试数据和用例
- **变量系统** - 统一的变量引用机制 `{变量名}`
- **详细日志** - 步骤级别日志，记录参数解析过程
- **分布式执行** - 支持多执行机，任务自动分发
- **完整报告** - 任务层级的结构化测试报告

### 1.3 技术栈

| 层次 | 技术选型 |
|------|----------|
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS |
| 后端 | Python + FastAPI |
| 数据库 | PostgreSQL 16 (主库) + Redis (缓存/队列) |
| 任务队列 | Celery + Redis |
| 容器化 | Docker + Docker Compose |
| 测试工具 | pytest + requests + Playwright + Locust |

---

## 2. 整体架构设计

### 2.1 架构选择

采用**模块化单体架构**，适合10人团队开发和维护：

```
┌─────────────────────────────────────────────────────────────────┐
│                      简化架构 (小团队友好)                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Frontend       │     │   Backend        │     │   Infrastructure │
│   (React)        │◄────┤   (FastAPI)      │◄────┤   PostgreSQL     │
│   Port: 3000     │     │   Port: 8000     │     │   Port: 5432    │
└──────────────────┘     └────────┬─────────┘     └──────────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
        ┌───────────────┐               ┌───────────────┐
        │    Redis      │               │   Workers     │
        │  Port: 6379   │               │  (后台任务)    │
        └───────────────┘               └───────────────┘
```

### 2.2 模块划分

```
backend/
├── app/
│   ├── api/                    # API 路由
│   │   ├── ui/                 # UI任务/场景/用例/步骤
│   │   ├── api/                # 接口任务/场景/用例/步骤
│   │   ├── data/               # 测试数据管理
│   │   ├── keywords/           # 关键字管理
│   │   ├── workers/            # 执行机管理
│   │   ├── executions/         # 执行和报告
│   │   └── auth/               # 认证授权
│   ├── core/                   # 核心配置
│   ├── models/                 # 数据模型
│   ├── services/               # 业务逻辑
│   │   ├── executor.py         # 测试执行引擎
│   │   ├── scheduler.py        # 任务调度器
│   │   ├── variable_resolver.py # 变量解析器
│   │   └── keyword_engine.py   # 关键字执行引擎
│   └── workers/                # 后台任务
```

---

## 3. 四层结构体系

### 3.1 层次定义

```
┌─────────────────────────────────────────────────────────────────┐
│                    四层结构体系                                  │
└─────────────────────────────────────────────────────────────────┘

任务            │ 执行单位 | 报告单位 │ 最高层级
├─────────────────────────────────────────────────────────────────┤
场景            │ 流程组合 │ 报告章节 │ 业务流程
├─────────────────────────────────────────────────────────────────┤
用例            │ 调试单位 │ 基本单元 │ 功能验证
├─────────────────────────────────────────────────────────────────┤
步骤            │ 执行单元 │ 最小粒度 │ 具体操作
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 类型分离

```
UI测试分支:
  UI任务 → UI场景 → UI用例 → UI步骤

接口测试分支:
  接口任务 → 接口场景 → 接口用例 → 接口步骤

混合测试分支:
  混合任务 → UI场景 + 接口场景 → UI用例 + 接口用例 → UI步骤 + 接口步骤
```

---

## 4. 数据模型设计

### 4.1 核心数据表

#### UI任务表 (ui_tasks)
```sql
CREATE TABLE ui_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    name TEXT NOT NULL,
    description TEXT,
    task_type TEXT DEFAULT 'ui',
    scenario_ids TEXT[] DEFAULT '{}',
    execution_config JSONB DEFAULT '{}',
    report_config JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### UI场景表 (ui_scenarios)
```sql
CREATE TABLE ui_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    task_id UUID REFERENCES ui_tasks(id),
    name TEXT NOT NULL,
    description TEXT,
    scenario_type TEXT DEFAULT 'ui',
    case_ids TEXT[] DEFAULT '{}',
    execution_order INTEGER,
    tags TEXT[] DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### UI用例表 (ui_test_cases)
```sql
CREATE TABLE ui_test_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    scenario_id UUID REFERENCES ui_scenarios(id),
    name TEXT NOT NULL,
    description TEXT,
    case_type TEXT DEFAULT 'ui',
    step_ids TEXT[] DEFAULT '{}',
    data_bindings JSONB DEFAULT '{}',
    browser_config JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    priority TEXT DEFAULT 'P2',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### UI步骤表 (ui_test_steps)
```sql
CREATE TABLE ui_test_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES ui_test_cases(id),
    scenario_id UUID REFERENCES ui_scenarios(id),
    task_id UUID REFERENCES ui_tasks(id),
    step_order INTEGER NOT NULL,
    keyword_id UUID REFERENCES keywords(id),
    step_name TEXT NOT NULL,
    step_type TEXT DEFAULT 'ui',
    parameters JSONB DEFAULT '{}',
    enabled BOOLEAN DEFAULT TRUE,
    continue_on_failure BOOLEAN DEFAULT FALSE,
    screenshot_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 测试数据表 (test_data)
```sql
CREATE TABLE test_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    data_name TEXT NOT NULL,
    data_value TEXT NOT NULL,
    data_type TEXT DEFAULT 'string',
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, data_name)
);
```

#### 关键字表 (keywords)
```sql
CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    keyword_type TEXT NOT NULL, -- 'system' or 'business'
    category TEXT NOT NULL, -- 'api', 'ui', 'assertion', 'extract', 'data'
    description TEXT,
    icon TEXT,
    implementation JSONB DEFAULT '{}',
    parameter_schema JSONB DEFAULT '{}',
    return_schema JSONB DEFAULT '{}',
    code_content TEXT, -- 业务关键字的Python代码
    is_valid BOOLEAN DEFAULT TRUE,
    project_id UUID REFERENCES projects(id), -- NULL表示系统关键字
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 执行机表 (workers)
```sql
CREATE TABLE workers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_name TEXT NOT NULL UNIQUE,
    worker_type TEXT NOT NULL, -- 'ui', 'api', 'perf', 'mixed'
    hostname TEXT,
    ip_address TEXT,
    port INTEGER,
    capabilities JSONB DEFAULT '{}',
    max_concurrent_tasks INTEGER DEFAULT 10,
    current_tasks INTEGER DEFAULT 0,
    browser_configs JSONB DEFAULT '{}',
    status TEXT DEFAULT 'offline', -- 'online', 'offline', 'busy', 'maintenance'
    last_heartbeat TIMESTAMP,
    tags TEXT[] DEFAULT '{}',
    project_id UUID REFERENCES projects(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 4.2 执行记录表

#### 任务执行记录表 (task_executions)
```sql
CREATE TABLE task_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    task_type TEXT NOT NULL,
    execution_mode TEXT DEFAULT 'task', -- 'task', 'case', 'debug'
    status TEXT DEFAULT 'pending',
    triggered_by UUID REFERENCES users(id),
    worker_id UUID REFERENCES workers(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_scenarios INTEGER DEFAULT 0,
    total_cases INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    passed_scenarios INTEGER DEFAULT 0,
    passed_cases INTEGER DEFAULT 0,
    passed_steps INTEGER DEFAULT 0,
    failed_scenarios INTEGER DEFAULT 0,
    failed_cases INTEGER DEFAULT 0,
    failed_steps INTEGER DEFAULT 0,
    execution_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 场景执行记录表 (scenario_executions)
```sql
CREATE TABLE scenario_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_execution_id UUID REFERENCES task_executions(id),
    scenario_id UUID NOT NULL,
    scenario_order INTEGER,
    scenario_name TEXT,
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_cases INTEGER DEFAULT 0,
    passed_cases INTEGER DEFAULT 0,
    failed_cases INTEGER DEFAULT 0
);
```

#### 用例执行记录表 (case_executions)
```sql
CREATE TABLE case_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_execution_id UUID REFERENCES task_executions(id),
    scenario_execution_id UUID REFERENCES scenario_executions(id),
    case_id UUID NOT NULL,
    case_order INTEGER,
    case_name TEXT,
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_steps INTEGER DEFAULT 0,
    passed_steps INTEGER DEFAULT 0,
    failed_steps INTEGER DEFAULT 0
);
```

#### 步骤执行日志表 (step_executions)
```sql
CREATE TABLE step_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_execution_id UUID REFERENCES task_executions(id),
    scenario_execution_id UUID REFERENCES scenario_executions(id),
    case_execution_id UUID REFERENCES case_executions(id),
    step_id UUID NOT NULL,
    step_order INTEGER,
    step_name TEXT,
    keyword_id UUID REFERENCES keywords(id),
    keyword_name TEXT,
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    parameters_definition JSONB DEFAULT '{}',
    parameters_resolved JSONB DEFAULT '{}',
    parameters_mapping JSONB DEFAULT '{}',
    return_value JSONB DEFAULT '{}',
    error_message TEXT,
    error_stack TEXT,
    screenshots JSONB DEFAULT '{}',
    logs TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. 关键字系统设计

### 5.1 关键字分类

#### 通用关键字 (系统内置)

**API测试关键字**
- `API_GET` - 发送GET请求
- `API_POST` - 发送POST请求
- `API_PUT` - 发送PUT请求
- `API_DELETE` - 发送DELETE请求

**UI测试关键字**
- `NAVIGATE` - 打开页面
- `CLICK` - 点击元素
- `INPUT` - 输入文本
- `WAIT_FOR_ELEMENT` - 等待元素

**断言关键字**
- `ASSERT_STATUS` - 断言HTTP状态码
- `ASSERT_JSON_FIELD` - 断言JSON字段
- `ASSERT_VISIBLE` - 断言元素可见
- `ASSERT_TEXT` - 断言元素文本

**提取关键字**
- `EXTRACT_VARIABLE` - 提取变量

#### 业务关键字 (用户自定义)

用户可以编写Python代码创建业务关键字，封装复杂的业务逻辑：

```python
def user_login(
    username: str,
    password: str,
    base_url: str = None,
    context: dict = None,
    variables: dict = None,
    logger: Any = None,
    http_client: Any = None,
    driver: Any = None,
) -> dict:
    """用户登录业务关键字"""
    # 实现登录逻辑
    return {
        'success': True,
        'token': '...',
        'user_id': '...'
    }
```

### 5.2 关键字参数定义

关键字参数支持变量引用，通过 `{变量名}` 方式引用测试数据：

```yaml
keyword: API_POST
parameters:
  url: "{login_url}"
  body:
    username: "{username}"
    password: "{password}"
```

### 5.3 关键字返回值

关键字的返回值可以保存为变量，供后续步骤使用：

```yaml
keyword: EXTRACT_VARIABLE
parameters:
  variable_name: auth_token
  extract_from: response_body
  extract_type: json_path
  expression: $.data.token

# 后续步骤可通过 {auth_token} 引用
```

---

## 6. 测试数据管理

### 6.1 数据与变量关联

测试数据在界面中管理，遵循以下原则：

- **数据名 = 变量名**
- **数据值 = 变量值**
- **引用方式**: `{变量名}`

### 6.2 数据管理界面

```
┌───────────────────────────────────────────────────────────────┐
│ 测试数据管理                                                    │
├───────────────────────────────────────────────────────────────┤
│ 项目: [电商项目 ▼]                                             │
│                                                               │
│ ┌─ 全局变量 ──────────────────────────────────────────────┐  │
│ │ 变量名           │ 变量值                  │ 类型   │ 操作 │  │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ base_url        │ https://api.test.com     │ text   │ ✏️   │ │
│ │ admin_token     │ sk_12345...             │ text   │ ✏️   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─ 项目变量 ──────────────────────────────────────────────┐  │
│ │ [+ 新增数据]                                               │  │
│ │ 变量名           │ 变量值                  │ 类型   │ 操作 │  │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ login_url       │ {base_url}/api/login    │ text   │ ✏️   │ │
│ │ login_username  │ test_user               │ text   │ ✏️   │ │
│ │ login_password  │ Test@123                │ text   │ 🔒   │ │
│ └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### 6.3 数据绑定到用例

用例可以绑定测试数据，绑定后可通过 `{数据名}` 或 `{别名}` 引用：

```
┌─ 用例数据绑定 ──────────────────────────────────────────────┐
│ 用例: API登录用例                                              │
│                                                               │
│ 已绑定数据:                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 数据名称         │ 别名       │ 用途           │ 操作    │ │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ login_url       │ url        │ 请求地址      │ [×]     │ │ │
│ │ login_username  │ username   │ 登录用户名    │ [×]     │ │ │
│ │ login_password  │ password   │ 登录密码      │ [×]     │ │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                               │
│ 绑定后引用方式: {url}, {username}, {password}                 │
└───────────────────────────────────────────────────────────────┘
```

---

## 7. 执行与日志系统

### 7.1 执行模式

#### 任务执行模式
- 从任务层级执行
- 生成完整的测试报告
- 支持场景并行执行
- 适合回归测试和冒烟测试

#### 调试执行模式
- 从用例层级执行
- 详细的日志和截图
- 单步执行支持
- 适合用例开发和问题排查

### 7.2 日志记录

#### 步骤级别日志

详细记录每个步骤的执行过程：

```json
{
  "step_execution_log": {
    "step_name": "发送登录请求",
    "keyword_name": "API_POST",
    "execution_info": {
      "status": "passed",
      "started_at": "2026-04-02T10:00:00.000Z",
      "completed_at": "2026-04-02T10:00:01.234Z",
      "duration_ms": 1234
    },
    "parameters_definition": {
      "url": "{login_url}",
      "body": {
        "username": "{username}",
        "password": "{password}"
      }
    },
    "parameters_resolved": {
      "url": "https://api.test.com/api/login",
      "body": {
        "username": "test_user",
        "password": "Test@123"
      }
    },
    "parameters_mapping": [
      {
        "参数路径": "url",
        "原始表达式": "{login_url}",
        "解析值": "https://api.test.com/api/login",
        "变量来源": "data_binding",
        "变量名": "login_url"
      }
    ],
    "execution_result": {
      "response": {
        "status_code": 200,
        "body": {...}
      }
    },
    "logs": [
      {
        "timestamp": "2026-04-02T10:00:00.000Z",
        "level": "INFO",
        "message": "开始执行步骤: 发送登录请求"
      }
    ]
  }
}
```

### 7.3 截图配置

#### 截图模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 调试模式 | 每个步骤都截图 | 用例开发、问题排查 |
| 正常模式 | 关键步骤和失败步骤截图 | 日常执行 |
| 性能模式 | 不截图 | 性能测试、大量执行 |

#### UI步骤截图

UI步骤执行时可配置截图时机：
- 开始前截图
- 结束后截图
- 失败时自动截图

---

## 8. 分布式执行系统

### 8.1 执行机架构

```
┌───────────────────────────────────────────────────────────────┐
│                        调度层                                │
│  Scheduler Service ──→ Task Queue (Redis)                     │
└───────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Worker Node 1  │   │ Worker Node 2  │   │ Worker Node 3  │
│ 类型: UI       │   │ 类型: API     │   │ 类型: UI       │
│ 状态: 在线     │   │ 状态: 在线     │   │ 状态: 在线     │
│ 负载: 2/10     │   │ 负载: 5/20     │   │ 负载: 1/10     │
└───────────────┘   └───────────────┘   └───────────────┘
```

### 8.2 执行机能力配置

UI执行机需要配置浏览器支持：
```json
{
  "worker_type": "ui",
  "browsers": [
    {
      "name": "chrome",
      "version": "120.0",
      "headless_supported": true,
      "max_instances": 5
    },
    {
      "name": "firefox",
      "version": "115.0",
      "headless_supported": true,
      "max_instances": 3
    }
  ],
  "max_concurrent_tasks": 10
}
```

### 8.3 任务分发策略

1. **基础条件检查**
   - 执行机状态为在线
   - 未达到最大并发数
   - 执行机类型匹配

2. **优先匹配**
   - 浏览器类型匹配 (UI任务)
   - 标签匹配 (环境、操作系统等)

3. **负载优化**
   - 优先选择负载较低的执行机
   - 考虑网络延迟

---

## 9. 测试报告设计

### 9.1 报告结构

```
测试报告
│
├─ 报告概要
│   ├─ 任务信息
│   ├─ 执行统计
│   └─ 趋势分析
│
├─ 场景详情
│   ├─ 场景 1
│   │   ├─ 用例 1
│   │   │   ├─ 步骤 1
│   │   │   ├─ 步骤 2
│   │   │   └─ ...
│   │   ├─ 用例 2
│   │   └─ ...
│   ├─ 场景 2
│   └─ ...
│
├─ 失败分析
│   ├─ 失败场景列表
│   ├─ 失败用例列表
│   └─ 失败步骤详情
│
└─ 附录
    ├─ 执行日志
    ├─ 性能指标
    └─ 截图附件
```

### 9.2 报告内容

任务级报告包含完整的四层结构信息：
- 任务概览
- 场景执行情况
- 用例执行详情
- 步骤执行日志
- 失败分析
- 趋势对比

---

## 10. 部署架构

### 10.1 容器化部署

使用 Docker Compose 进行容器化部署：

```yaml
version: '3.8'

services:
  # 前端
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  # 后端API
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://admin:${DB_PASSWORD}@postgres:5432/test_platform
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis

  # 数据库
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: test_platform
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

  # Worker (UI测试)
  ui-worker:
    build: ./backend
    command: celery -A app.workers worker --loglevel=info -Q ui_tasks
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
    depends_on:
      - redis

  # Worker (API测试)
  api-worker:
    build: ./backend
    command: celery -A app.workers worker --loglevel=info -Q api_tasks
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
```

### 10.2 部署准备

1. **环境要求**
   - Docker 24.0+
   - Docker Compose 2.20+
   - CPU: 4核+
   - 内存: 8GB+

2. **配置文件**
   - `.env` - 环境变量配置
   - `docker-compose.yml` - 服务编排

3. **初始化脚本**
   - 数据库初始化
   - 默认数据导入

---

## 11. API接口设计

### 11.1 UI任务管理

```
GET    /v1/ui/tasks                    # 获取UI任务列表
POST   /v1/ui/tasks                    # 创建UI任务
GET    /v1/ui/tasks/:task_id           # 获取UI任务详情
PUT    /v1/ui/tasks/:task_id           # 更新UI任务
DELETE /v1/ui/tasks/:task_id           # 删除UI任务
POST   /v1/ui/tasks/:task_id/execute    # 执行UI任务
```

### 11.2 场景管理

```
GET    /v1/ui/scenarios                 # 获取UI场景列表
POST   /v1/ui/scenarios                 # 创建UI场景
GET    /v1/ui/scenarios/:id            # 获取场景详情
PUT    /v1/ui/scenarios/:id            # 更新场景
```

### 11.3 用例管理

```
GET    /v1/ui/cases                    # 获取UI用例列表
POST   /v1/ui/cases                    # 创建UI用例
GET    /v1/ui/cases/:id                # 获取用例详情
PUT    /v1/ui/cases/:id                # 更新用例
POST   /v1/ui/cases/:id/execute        # 调试用例
POST   /v1/ui/cases/:id/debug          # 调试用例
```

### 11.4 数据管理

```
GET    /v1/projects/:id/data            # 获取测试数据
POST   /v1/projects/:id/data            # 创建测试数据
PUT    /v1/data/:id                     # 更新测试数据
DELETE /v1/data/:id                     # 删除测试数据
```

### 11.5 执行和报告

```
GET    /v1/executions/:id               # 获取执行详情
GET    /v1/executions/:id/report        # 获取测试报告
GET    /v1/step-executions/:id          # 获取步骤执行日志
```

---

## 12. 分阶段实施计划

### Phase 1: MVP (4-6周)

**目标**: 基础功能可用

- 用户认证和授权
- 四层结构数据模型
- 通用关键字 (API: 10个, UI: 10个)
- 测试数据管理
- 用例编辑器
- 任务执行 (单执行机)
- 基础报告

### Phase 2: 核心功能 (6-8周)

**目标**: 功能完善

- 业务关键字开发框架
- 变量提取和传递
- 步骤级别详细日志
- UI截图功能
- 用例调试模式
- 场景管理
- 完整测试报告

### Phase 3: 高级功能 (4-6周)

**目标**: 企业级能力

- 分布式执行
- 执行机管理
- 任务调度
- 性能测试支持
- 趋势分析
- 告警通知

### Phase 4: 优化增强 (4-6周)

**目标**: 体验优化

- 界面优化
- 性能优化
- 监控告警
- 数据备份
- 文档完善

---

## 13. 附录

### 13.1 关键字清单

#### API测试关键字
| 关键字 | 说明 | 参数 |
|--------|------|------|
| API_GET | 发送GET请求 | url, headers, params |
| API_POST | 发送POST请求 | url, headers, body |
| API_PUT | 发送PUT请求 | url, headers, body |
| API_DELETE | 发送DELETE请求 | url, headers |
| ASSERT_STATUS | 断言状态码 | expected_status |
| ASSERT_JSON_FIELD | 断言JSON字段 | json_path, expected_value |
| EXTRACT_VARIABLE | 提取变量 | variable_name, extract_from, expression |

#### UI测试关键字
| 关键字 | 说明 | 参数 |
|--------|------|------|
| NAVIGATE | 打开页面 | url |
| CLICK | 点击元素 | selector, timeout |
| INPUT | 输入文本 | selector, text, clear_first |
| WAIT_FOR_ELEMENT | 等待元素 | selector, state, timeout |
| ASSERT_VISIBLE | 断言可见 | selector |
| ASSERT_TEXT | 断言文本 | selector, expected_text |
| ASSERT_URL | 断言URL | expected_url |
| GET_TEXT | 获取文本 | selector, save_as |

### 13.2 配置示例

#### 执行配置示例
```json
{
  "execution_mode": "task",
  "screenshot_mode": "normal",
  "parallel_execution": true,
  "max_concurrent_scenarios": 3,
  "timeout": 600,
  "on_failure": "stop"
}
```

#### 浏览器配置示例
```json
{
  "browser": "chrome",
  "version": "120",
  "headless": true,
  "resolution": "1920x1080",
  "args": [
    "--no-sandbox",
    "--disable-dev-shm-usage"
  ]
}
```

### 13.3 参考资料

- FastAPI官方文档: https://fastapi.tiangolo.com/
- React官方文档: https://react.dev/
- Playwright官方文档: https://playwright.dev/
- Pytest官方文档: https://docs.pytest.org/
- Celery官方文档: https://docs.celeryq.io/
