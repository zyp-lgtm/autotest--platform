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

### 🎉 MVP 完成（2026-04-02）

**状态**: ✅ 核心功能已完成并验证

### 已完成功能

#### 后端 API
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
- [x] 系统关键字种子脚本（9 个关键字）

#### 前端应用
- [x] 前端配置（React 19 + TypeScript + Vite + TailwindCSS）
- [x] 前后端完整集成
- [x] 用户认证流程（注册、登录、退出）
- [x] 路由和认证保护
- [x] 仪表盘页面（实时统计数据）
- [x] 项目选择功能
- [x] UI 组件库（Button, Input, Card, Header, Layout）
- [x] 错误处理和表单验证

#### 文档
- [x] README 和项目文档
- [x] API 文档（Swagger/OpenAPI）
- [x] 部署指南
- [x] 手动测试报告

#### Playwright UI 自动化（2026-04-03 新增）
- [x] Playwright 浏览器管理器（异步 API）
- [x] NAVIGATE 关键字（导航到 URL）
- [x] CLICK 关键字（点击元素）
- [x] INPUT 关键字（输入文本）
- [x] WAIT_FOR_ELEMENT 关键字（等待元素）
- [x] SCREENSHOT 功能（截图保存）
- [x] 完整错误处理和日志
- [x] 测试脚本（test_ui_keywords.py）

### 🎯 验证通过的功能

#### 用户认证
- [x] 用户注册（表单验证、密码确认、长度检查）
- [x] 用户登录（正确密码、错误密码处理）
- [x] 自动登录（Token 存储、自动认证）
- [x] 退出登录（清除 Token、重定向）
- [x] 路由保护（未登录自动跳转登录页）
- [x] 受保护页面（仪表盘需要认证）

#### API 集成
- [x] API 调用正确携带认证头
- [x] OAuth2 登录（application/x-www-form-urlencoded 格式）
- [x] 错误处理（401、400 等状态码）
- [x] 表单数据验证
- [x] Network 请求日志可见

#### 用户体验
- [x] 加载状态指示
- [x] 错误消息友好提示
- [x] 页面重定向正确
- [x] 表单验证实时反馈
- [x] 响应式布局

### 🔧 已修复的关键问题

1. **React 懒加载问题** → 添加 `Suspense` 包裹，支持路由懒加载
2. **组件导出方式** → 统一使用默认导出（export default）
3. **API 请求格式** → 使用 `URLSearchParams` 发送 OAuth2 表单数据
4. **401 错误闪退** → 智能重定向逻辑，避免在登录/注册页面刷新
5. **错误处理** → 改进错误消息提取和显示

### 📊 技术债务

#### 优先级 P0（MVP 后必须）
- [ ] 密码哈希（当前存储明文，需要使用 bcrypt）
- [ ] 完整的单元测试覆盖

#### 优先级 P1（重要功能）
- [ ] Playwright UI 关键字实现
- [ ] 任务/场景/用例管理 UI
- [ ] 测试执行和报告展示
- [ ] E2E 测试自动化

#### 优先级 P2（增强功能）
- [ ] API 性能测试集成
- [ ] 分布式执行实现
- [ ] 高级报告生成
- [ ] CI/CD 集成

---

## 🚀 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Git
- Node.js 18+（用于本地开发）

### 5 分钟快速启动

```bash
# 1. 克隆仓库
git clone https://github.com/zyp-lgtm/autotest--platform.git
cd autotest--platform
git checkout test-platform-mvp

# 2. 启动后端服务
docker-compose -f docker/docker-compose.yml up -d

# 3. 启动前端开发服务器
cd frontend
npm install
npm run dev

# 4. 访问应用
open http://localhost:3001
```

### 测试账号

您可以在注册页面创建新账号，或使用以下测试账号：

- **用户名**: `demouser`
- **密码**: `demo123`

### 功能验证清单

✅ **核心功能**:
- [x] 用户注册和登录
- [x] 查看仪表盘统计
- [x] 退出登录
- [x] 受保护路由自动重定向
- [x] API 文档访问

⏳ **后续功能**:
- [ ] 创建和管理测试任务
- [ ] 配置测试数据
- [ ] 执行测试
- [ ] 查看测试报告

---

## 📁 项目结构

```
test-platform/
├── docker/
│   └── docker-compose.yml          # 容器编排配置
├── backend/
│   ├── app/
│   │   ├── api/                    # API 路由
│   │   ├── core/                   # 核心模块
│   │   ├── models/                 # SQLAlchemy 模型
│   │   ├── schemas/                # Pydantic 模式
│   │   ├── services/               # 业务服务
│   │   └── main.py                 # FastAPI 应用入口
│   └── scripts/
│       └── seed_keywords.py        # 系统关键字种子脚本
├── frontend/
│   ├── src/
│   │   ├── api/                    # API 客户端层
│   │   ├── components/             # React 组件
│   │   ├── contexts/               # React Context
│   │   ├── hooks/                  # 自定义 Hooks
│   │   ├── pages/                  # 页面组件
│   │   ├── types/                  # TypeScript 类型
│   │   └── App.tsx                 # 根组件
│   └── package.json
└── README.md
```

---

## 📚 开发指南

### 后端开发

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

### 代码规范

- **Python**: PEP 8 + black 格式化
- **TypeScript**: ESLint 代码检查
- **Git**: Conventional Commits 规范

---

## 📖 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

主要端点：

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/auth/me` | 获取当前用户 |
| GET | `/api/v1/projects/{project_id}/data/` | 获取测试数据 |
| GET | `/api/v1/ui/tasks/` | 获取 UI 任务 |

---

## 🎯 MVP 总结

### 交付成果

✅ **完整的测试自动化平台 MVP**，包含：
- 用户认证系统
- 前后端完整集成
- RESTful API 设计
- Docker 容器化部署
- 完善的项目文档

### 技术亮点

- 🏗️ **四层架构设计**：Task → Scenario → Case → Step
- 🔀 **UI/API 完全分离**：支持不同测试类型
- 💾 **可视化测试数据管理**：界面管理测试数据
- 📝 **强大的变量系统**：统一语法 `{变量名}`
- 🔍 **详细的执行日志**：完整的请求追踪

### 下一步

根据 **roadmap.md**，项目将进入 **阶段 2：基础功能完善**：

1. **Playwright UI 关键字实现**
2. **任务/场景/用例管理 UI**
3. **测试执行报告**

**阶段 4** 将实现最高优先级功能：**AI 驱动测试** 🤖

---

## 🏆 许可证

MIT License

---

**MVP 完成日期**: 2026-04-02
**当前版本**: v1.0.0
**GitHub**: https://github.com/zyp-lgtm/autotest--platform
- 🎯 **自然语言测试** - 用自然语言描述测试需求，AI 自动生成测试步骤
- 🤖 **智能元素定位** - AI 分析页面结构，自动选择最佳元素定位策略
- 🧠 **学习与自修复** - AI 从历史执行中学习，自动适应页面变化
- 💡 **智能修复建议** - 测试失败时，AI 分析原因并提供修复方案
- 💰 **成本可控** - 三层架构（大模型规划 + 小模型执行 + Playwright），成本优化

**技术方案**：
- **规划层**：GPT-4 / Claude 3.5 Sonnet（理解测试目标，生成抽象计划）
- **适配层**：GPT-4o-mini / Claude 3.5 Haiku（智能元素定位，动态调整）
- **执行层**：Playwright（执行 UI 操作，零 AI 成本）
- **学习系统**：页面学习历史，持续优化

**预计开发周期**：2-6 个月

**交互原型**：[`docs/ai-test-prototype.html`](./docs/ai-test-prototype.html)（在浏览器中打开查看）

**状态**：📋 设计完成，等待 MVP 验证后启动实施

## 部署验证

### 本地开发环境

1. 启动后端服务：
```bash
cd /Users/apple/aicode/.worktrees/test-platform
docker-compose -f docker/docker-compose.yml up -d
```

2. 启动前端开发服务器：
```bash
cd frontend
npm install
npm run dev
```

3. 访问应用：
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 功能验证清单

- [x] 用户注册
- [x] 用户登录
- [x] 查看仪表盘统计
- [x] 创建测试数据
- [x] 查看 API 文档

## 📖 Demo 使用指南

### 创建完整的测试流程

本平台支持完整的 UI 测试自动化流程。以下是创建一个"百度搜索测试"的完整步骤：

#### 1. 登录系统
访问 http://localhost:5173，使用注册的用户登录

#### 2. 创建测试任务
1. 进入"任务管理"页面
2. 点击"创建任务"按钮
3. 填写任务信息：
   - 任务名称：百度搜索测试
   - 描述：演示百度搜索功能的UI自动化测试
   - 标签：demo, ui, 百度
4. 点击"创建"

#### 3. 创建测试场景
1. 在任务列表中，点击"管理场景"按钮
2. 点击"创建场景"按钮
3. 填写场景信息：
   - 场景名称：百度搜索场景
   - 描述：在百度首页搜索关键词并验证结果
   - 场景类型：UI测试
   - 标签：搜索, 冒烟测试
4. 点击"创建"

#### 4. 创建测试用例
1. 在场景列表中，展开场景并点击"添加用例"按钮
2. 填写用例信息：
   - 用例名称：搜索关键词测试用例
   - 描述：打开百度首页，输入关键词并搜索
   - 优先级：P1
   - 标签：搜索, 核心功能
3. 点击"创建"

#### 5. 添加测试步骤
1. 在用例列表中，展开用例并点击"添加步骤"按钮
2. 创建以下4个步骤：

**步骤1 - 打开百度首页：**
- 步骤名称：打开百度首页
- 选择关键字：NAVIGATE (导航到指定 URL)
- 参数（JSON格式）：
  ```json
  {"url": "https://www.baidu.com"}
  ```

**步骤2 - 输入搜索关键词：**
- 步骤名称：输入搜索关键词
- 选择关键字：INPUT (在输入框中输入文本)
- 参数：
  ```json
  {
    "selector": "#kw",
    "text": "测试自动化平台",
    "clear_first": true
  }
  ```

**步骤3 - 点击搜索按钮：**
- 步骤名称：点击搜索按钮
- 选择关键字：CLICK (点击页面元素)
- 参数：
  ```json
  {
    "selector": "#su",
    "timeout": 5000
  }
  ```

**步骤4 - 等待搜索结果：**
- 步骤名称：等待搜索结果
- 选择关键字：WAIT_FOR_ELEMENT (等待元素出现)
- 参数：
  ```json
  {
    "selector": ".result",
    "state": "visible",
    "timeout": 10000
  }
  ```

#### 6. 执行测试
1. 返回"任务管理"页面
2. 找到刚创建的任务
3. 点击"执行"按钮
4. 等待执行完成，点击执行记录查看详细报告

### 可用系统关键字

#### UI 关键字
- **NAVIGATE** - 导航到指定 URL
- **CLICK** - 点击页面元素
- **INPUT** - 在输入框中输入文本
- **WAIT_FOR_ELEMENT** - 等待元素出现

#### API 关键字
- **API_GET** - 发送 HTTP GET 请求
- **API_POST** - 发送 HTTP POST 请求

#### 断言关键字
- **ASSERT_STATUS** - 断言 HTTP 状态码

#### 数据提取关键字
- **EXTRACT_VARIABLE** - 从响应中提取变量

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
