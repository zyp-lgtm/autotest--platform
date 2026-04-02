# 测试自动化平台 MVP

关键字驱动测试自动化平台，支持 API 和 UI 测试，采用四层结构设计（任务 → 场景 → 用例 → 步骤），完全分离 UI 和 API 测试类型。

## 📋 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [API 端点](#api-端点)
- [系统关键字](#系统关键字)
- [MVP 进度](#mvp-进度)

## 功能特性

### 核心功能

- 🎯 **关键字驱动测试**
  - 系统关键字：内置的常用测试操作（API 请求、UI 操作、断言等）
  - 业务关键字：用户可编程的自定义测试逻辑

- 📊 **四层结构设计**
  - Task（任务）：执行单元和报告单位
  - Scenario（场景）：流程组合
  - Case（用例）：调试单位和基本单位
  - Step（步骤）：执行单位和最小粒度

- 🔀 **UI/API 完全分离**
  - UI Task/UI Scenario/UI Case/UI Step
  - API Task/API Scenario/API Case/API Step
  - 数据互操作性：API 创建数据，UI 使用数据

- 💾 **可视化测试数据管理**
  - 界面管理测试数据
  - 数据名即变量名
  - 支持多种数据类型：string、number、boolean、json

- 📝 **强大的变量系统**
  - 统一语法：`{变量名}`
  - 支持嵌套访问：`{user.id}`
  - 参数自动解析和替换

- 🔍 **详细的执行日志**
  - 步骤级日志记录
  - 参数解析追踪（原始表达式 → 解析值）
  - 执行结果详细记录

- 🖼️ **可配置 UI 截图**
  - 调试模式：开启截图，方便排查错误
  - 执行模式：关闭截图，提升速度
  - 性能模式：最小截图

### 测试能力

- ✅ API 自动化测试（GET、POST、断言、变量提取）
- ✅ UI 自动化测试（导航、点击、输入、等待）
- ✅ 数据驱动测试
- ✅ 关键字复用和组合
- ✅ 分布式执行支持

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端 (React 19)                      │
│  ┌──────────────┬──────────────┬──────────────────────┐    │
│  │ 仪表盘        │ 任务管理      │ 测试数据管理          │    │
│  └──────────────┴──────────────┴──────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       后端 (FastAPI)                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  API 路由层                                           │  │
│  │  /api/v1/auth   /api/v1/data   /api/v1/ui/tasks     │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  服务层                                              │  │
│  │  TestExecutor │ KeywordEngine │ VariableResolver   │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  数据层 (SQLAlchemy)                                 │  │
│  │  User │ Project │ UITask │ APITask │ Keyword      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据层                                   │
│  PostgreSQL (业务数据)  │  Redis (缓存/队列)              │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 启动步骤

```bash
# 1. 进入项目目录
cd /Users/apple/aicode/.worktrees/test-platform

# 2. 复制环境配置文件
cp .env.example .env

# 3. 启动所有服务（后台运行）
docker-compose -f docker/docker-compose.yml up -d

# 4. 等待服务启动（约 30 秒）
docker-compose -f docker/docker-compose.yml ps

# 5. 查看后端日志
docker-compose -f docker/docker-compose.yml logs -f backend

# 6. 种植系统关键字
docker-compose -f docker/docker-compose.yml exec backend python scripts/seed_keywords.py
```

### 访问应用

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 停止服务

```bash
docker-compose -f docker/docker-compose.yml down
```

## 技术栈

### 后端

- **框架**: FastAPI 0.104.1
- **语言**: Python 3.11+
- **数据库**: SQLAlchemy 2.0.23 + PostgreSQL 16
- **缓存**: Redis 7
- **任务队列**: Celery 5.3.4
- **认证**: JWT (python-jose)
- **测试**: pytest 7.4.3, httpx 0.25.1

### 前端

- **框架**: React 19
- **语言**: TypeScript 5.3+
- **构建工具**: Vite 5.0+
- **UI 框架**: Tailwind CSS 3.3+
- **路由**: React Router DOM 6.20+
- **状态管理**: Zustand 4.4+
- **HTTP 客户端**: Axios 1.6+

### 测试工具

- **API 测试**: requests 2.31.0
- **UI 测试**: Playwright 1.40.0
- **性能测试**: Locust (待集成)

### 基础设施

- **容器化**: Docker, Docker Compose
- **反向代理**: Nginx (Alpine)
- **数据库**: PostgreSQL 16 (Alpine)
- **缓存**: Redis 7 (Alpine)

## 项目结构

```
test-platform/
├── docker/
│   └── docker-compose.yml          # 容器编排配置
├── backend/
│   ├── app/
│   │   ├── api/                    # API 路由
│   │   │   ├── auth/               # 认证端点
│   │   │   ├── data/               # 测试数据管理
│   │   │   └── ui/                 # UI 任务管理
│   │   ├── core/                   # 核心模块
│   │   │   ├── config.py           # 配置管理
│   │   │   ├── database.py         # 数据库配置
│   │   │   └── security.py         # JWT 认证
│   │   ├── models/                 # SQLAlchemy 模型
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── keyword.py
│   │   │   ├── test_data.py
│   │   │   ├── ui_task.py          # UI 四层模型
│   │   │   └── api_task.py         # API 四层模型
│   │   ├── schemas/                # Pydantic 模式
│   │   ├── services/               # 业务服务
│   │   │   ├── executor.py         # 测试执行器
│   │   │   ├── variable_resolver.py # 变量解析
│   │   │   └── keyword_engine.py   # 关键字引擎
│   │   ├── tests/                  # 测试文件
│   │   └── main.py                 # FastAPI 应用入口
│   ├── scripts/
│   │   └── seed_keywords.py        # 系统关键字种子脚本
│   ├── requirements.txt             # Python 依赖
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/             # React 组件
│   │   ├── pages/                  # 页面组件
│   │   │   └── Dashboard.tsx       # 仪表盘
│   │   ├── services/               # API 服务
│   │   ├── types/                  # TypeScript 类型
│   │   ├── App.tsx                 # 根组件
│   │   └── main.tsx                # 应用入口
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── .env.example                    # 环境变量模板
└── README.md
```

## 开发指南

### 后端开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest

# 种植系统关键字
python scripts/seed_keywords.py
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### 代码规范

- **Python**: 遵循 PEP 8，使用 black 格式化
- **TypeScript**: 使用 ESLint 进行代码检查
- **Git**: 使用 Conventional Commits 规范

## API 端点

### 认证 API (`/api/v1/auth`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录 |
| GET | `/me` | 获取当前用户信息 |

### 测试数据 API (`/api/v1/projects/{project_id}/data`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 创建测试数据 |
| GET | `/` | 获取项目所有测试数据 |
| GET | `/{data_id}` | 获取单个测试数据 |
| PUT | `/{data_id}` | 更新测试数据 |
| DELETE | `/{data_id}` | 删除测试数据 |

### UI 任务 API (`/api/v1/ui/tasks`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 创建 UI 任务 |
| GET | `/` | 获取项目所有 UI 任务 |
| GET | `/{task_id}` | 获取单个 UI 任务 |
| POST | `/{task_id}/execute` | 执行 UI 任务 |

### UI 场景 API (`/api/v1/ui/scenarios`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 创建 UI 场景 |
| GET | `/{scenario_id}` | 获取单个 UI 场景 |

## 系统关键字

### API 关键字

| 关键字名 | 类别 | 描述 | 参数 |
|---------|------|------|------|
| `API_GET` | api | 发送 HTTP GET 请求 | url, headers, params |
| `API_POST` | api | 发送 HTTP POST 请求 | url, headers, body |
| `ASSERT_STATUS` | assertion | 断言 HTTP 状态码 | expected_status |
| `EXTRACT_VARIABLE` | extract | 从响应中提取变量 | variable_name, extract_from, expression |

### UI 关键字

| 关键字名 | 类别 | 描述 | 参数 |
|---------|------|------|------|
| `NAVIGATE` | ui | 导航到指定 URL | url |
| `CLICK` | ui | 点击页面元素 | selector, timeout |
| `INPUT` | ui | 在输入框中输入文本 | selector, text, clear_first |
| `WAIT_FOR_ELEMENT` | ui | 等待元素出现 | selector, state, timeout |

## MVP 进度

### 已完成 ✅

- [x] 项目基础设施搭建
- [x] Docker 容器化配置
- [x] 后端核心模块（配置、数据库、安全）
- [x] 数据模型（User, Project, Keyword, TestData）
- [x] UI 四层模型（UITask, UIScenario, UICase, UIStep）
- [x] API 四层模型（APITask, APIScenario, APICase, APIStep）
- [x] Pydantic 模式
- [x] 变量解析器（支持 `{变量名}` 语法）
- [x] 关键字执行引擎
- [x] 测试执行器
- [x] 认证 API（注册、登录、用户信息）
- [x] 测试数据管理 API（CRUD）
- [x] UI 任务管理 API
- [x] 前端配置（React 19 + TypeScript + Vite + TailwindCSS）
- [x] 仪表盘页面
- [x] 系统关键字种子脚本（9 个关键字）
- [x] README 和文档

### 技术债务

- [ ] 密码哈希（当前存储明文，需要使用 bcrypt）
- [ ] Playwright UI 关键字实现
- [ ] 完整的错误处理和验证
- [ ] 单元测试覆盖
- [ ] E2E 测试
- [ ] API 性能测试集成
- [ ] 分布式执行实现
- [ ] 报告生成和展示

### 后续计划

1. **Phase 1**: 完善认证系统（密码哈希、权限控制）
2. **Phase 2**: 实现 Playwright UI 关键字
3. **Phase 3**: 完整的测试执行和报告
4. **Phase 4**: 分布式执行支持
5. **Phase 5**: 性能测试集成

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
