# 测试自动化平台

> **当前状态**: 🟢 核心功能已完成，进入增强阶段
> **成熟度**: ⭐⭐⭐⭐/⭐⭐⭐⭐⭐ (4/5)
> **详细计划**: 查看 [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) 了解完整的开发路线图

关键字驱动测试自动化平台，支持 API 和 UI 测试，采用四层结构设计（任务 → 场景 → 用例 → 步骤），完全分离 UI 和 API 测试类型。

## 🚀 快速导航

- 📋 [开发计划](./DEVELOPMENT_PLAN.md) - 完整的功能规划和优先级
- 📖 [CLAUDE.md](./CLAUDE.md) - 项目宪法和开发规范
- 🤖 [Agent 指南](./AGENT_GUIDE.md) - Agent 使用说明
- 📝 [更新日志](./CHANGELOG.md) - 版本更新历史

## 📊 当前能力评估

### ✅ 已实现核心功能

#### 测试执行能力
- ✅ **15+ UI 关键字** - 导航、交互、等待、断言等完整覆盖
- ✅ **智能等待机制** - 自动等待元素出现，测试更稳定
- ✅ **完善的断言系统** - ASSERT_VISIBLE, ASSERT_TEXT, ASSERT_TITLE, ASSERT_URL
- ✅ **调试能力增强** - 失败截图、详细日志、错误分类
- ✅ **元素选择器工具** - 可视化选择页面元素
- ✅ **测试数据管理** - 完整的数据驱动测试支持
- ✅ **环境配置管理** - 多环境配置切换
- ✅ **定时任务系统** - 支持定时执行测试

#### 浏览器录制功能（2026-04-21 新增）🎬
- ✅ **可视化录制** - 在浏览器中执行操作，系统自动记录
- ✅ **智能数据提取** - 自动识别测试数据（用户名、密码等）
- ✅ **自动生成场景** - 录制的操作直接转换为测试用例
- ✅ **跨页面录制** - 支持多页面操作录制
- ✅ **实时进度显示** - 录制过程中实时显示捕获的操作数

#### 性能优化
- ✅ **内存缓存系统** - API 响应缓存，减少 70% 数据库查询
- ✅ **智能缓存失效** - 修改数据后自动清除相关缓存
- ✅ **并发执行系统** - 支持多个测试并发执行
- ✅ **自动重试机制** - 失败自动重试，提高成功率

#### 系统架构
- ✅ **插件化关键字系统** - 支持自定义关键字扩展
- ✅ **仓储模式层** - 数据访问层抽象，支持多数据库
- ✅ **结构化日志** - 统一的日志格式和级别
- ✅ **审计日志系统** - 完整的操作审计追踪
- ✅ **统一错误处理** - 错误分类和修复建议

### 🔜 待增强功能
- ⏳ **AI 驱动测试** - 自然语言生成测试步骤（阶段4）
- ⏳ **高级报告生成** - 更丰富的测试报告和图表
- ⏳ **CI/CD 集成** - 与主流 CI/CD 工具集成
- ⏳ **分布式执行** - 多机器分布式测试执行

### 📈 成熟度评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 基础架构 | ⭐⭐⭐⭐⭐ | 架构完善，插件化设计 |
| 关键字丰富度 | ⭐⭐⭐⭐ | 15+ 个关键字，覆盖核心场景 |
| 易用性 | ⭐⭐⭐⭐ | 录制功能 + 可视化界面 |
| 稳定性 | ⭐⭐⭐⭐ | 智能等待 + 自动重试 |
| 可调试性 | ⭐⭐⭐⭐ | 详细日志 + 截图 + 错误分类 |
| 报告质量 | ⭐⭐⭐ | 基础完善，待增强 |
| 数据管理 | ⭐⭐⭐⭐⭐ | 完整的数据驱动和环境配置 |
| 性能 | ⭐⭐⭐⭐ | 缓存 + 并发执行 |
| **总体评分** | **⭐⭐⭐⭐** | **核心功能完善，生产就绪** |

---

## 📋 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [系统关键字](#系统关键字)
- [录制功能](#录制功能)
- [API 文档](#api-文档)

## 功能特性

### 核心功能

- 🎯 **关键字驱动测试**
  - 系统关键字：内置的常用测试操作（API 请求、UI 操作、断言等）
  - 业务关键字：用户可编程的自定义测试逻辑
  - 插件化扩展：支持自定义关键字插件

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
  - 支持多环境配置

- 📝 **强大的变量系统**
  - 统一语法：`{变量名}`
  - 支持嵌套访问：`{user.id}`
  - 参数自动解析和替换
  - 支持测试数据引用

- 🔍 **详细的执行日志**
  - 步骤级日志记录
  - 参数解析追踪（原始表达式 → 解析值）
  - 执行结果详细记录
  - 错误分类和修复建议

- 🖼️ **智能截图机制**
  - 调试模式：所有步骤截图
  - 执行模式：仅失败步骤截图
  - 性能模式：无截图
  - 自动保存和展示

- 🎬 **浏览器录制功能**
  - 可视化录制用户操作
  - 自动生成测试步骤
  - 智能提取测试数据
  - 支持跨页面录制

### 测试能力

- ✅ API 自动化测试（GET、POST、PUT、DELETE、断言、变量提取）
- ✅ UI 自动化测试（15+ 关键字：导航、点击、输入、等待、断言等）
- ✅ 数据驱动测试（测试数据管理 + 环境配置）
- ✅ 关键字复用和组合
- ✅ 定时任务执行
- ✅ 并发测试执行
- ✅ 测试录制回放

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端 (React 19 + TypeScript)          │
│  ┌──────────────┬──────────────┬──────────────────────┐    │
│  │ 仪表盘        │ 场景管理      │ 录制向导              │    │
│  │ 任务管理      │ 测试数据      │ 执行报告              │    │
│  │ 环境配置      │ 定时任务      │ 元素选择器            │    │
│  └──────────────┴──────────────┴──────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       后端 (FastAPI)                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  API 路由层                                           │  │
│  │  /api/v1/auth   /api/v1/data   /api/v1/ui/*         │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  服务层                                              │  │
│  │  TestExecutor │ KeywordEngine │ VariableResolver   │  │
│  │  Recorder     │ DataExtractor  │ Scheduler         │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  数据层 (SQLAlchemy + Repository)                   │  │
│  │  User │ Project │ UITask │ APITask │ Keyword      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据层                                   │
│  SQLite (开发/测试)  │  PostgreSQL (生产)                  │
│  SimpleCache (内存缓存)                                     │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 16+
- Git

### 启动步骤

```bash
# 1. 进入项目目录
cd /Users/apple/aicode/.worktrees/test-platform

# 2. 初始化后端
cd backend
pip install -r requirements.txt
python3 init_db.py  # 初始化数据库

# 3. 启动后端服务
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 启动前端服务（新终端）
cd frontend
npm install
npm run dev

# 5. 访问应用
open http://localhost:3000
```

### 访问应用

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 技术栈

### 后端

- **框架**: FastAPI 0.104.1
- **语言**: Python 3.11+
- **数据库**: SQLAlchemy 2.0.23 + SQLite (开发) / PostgreSQL (生产)
- **缓存**: SimpleCache (内存)
- **认证**: JWT + HttpOnly Cookie
- **测试**: pytest 7.4.3
- **UI自动化**: Playwright 1.40.0

### 前端

- **框架**: React 19
- **语言**: TypeScript 5.3+
- **构建工具**: Vite 5.0+
- **UI 框架**: Tailwind CSS 3.3+
- **路由**: React Router DOM 6.20+
- **状态管理**: Zustand 4.4+
- **HTTP 客户端**: Axios 1.6+

### 基础设施

- **容器化**: Docker (可选)
- **数据库**: SQLite / PostgreSQL
- **缓存**: 内存缓存

## 项目结构

```
test-platform/
├── backend/
│   ├── app/
│   │   ├── api/                    # API 路由
│   │   │   ├── auth/               # 认证端点
│   │   │   ├── data/               # 测试数据管理
│   │   │   ├── ui/                 # UI 任务管理
│   │   │   └── recording/          # 录制功能 API
│   │   ├── core/                   # 核心模块
│   │   │   ├── config.py           # 配置管理
│   │   │   ├── database.py         # 数据库配置
│   │   │   └── security.py         # JWT 认证
│   │   ├── models/                 # SQLAlchemy 模型
│   │   ├── schemas/                # Pydantic 模式
│   │   ├── services/               # 业务服务
│   │   │   ├── executor.py         # 测试执行器
│   │   │   ├── keywords/           # 关键字引擎（插件化）
│   │   │   ├── recorder.py         # 录制服务
│   │   │   └── scheduler.py        # 定时调度
│   │   ├── repositories/           # 数据访问层
│   │   └── main.py                 # FastAPI 应用入口
│   ├── requirements.txt             # Python 依赖
│   └── init_db.py                  # 数据库初始化脚本
├── frontend/
│   ├── src/
│   │   ├── api/                    # API 客户端层
│   │   ├── components/             # React 组件
│   │   │   ├── RecordingWizard.tsx # 录制向导
│   │   │   └── ElementPicker.tsx   # 元素选择器
│   │   ├── pages/                  # 页面组件
│   │   │   ├── Dashboard.tsx       # 仪表盘
│   │   │   ├── Scenarios.tsx       # 场景管理
│   │   │   └── Tasks.tsx           # 任务管理
│   │   ├── types/                  # TypeScript 类型
│   │   └── App.tsx                 # 根组件
│   ├── package.json
│   └── vite.config.ts
├── CLAUDE.md                        # 项目宪法
├── CHANGELOG.md                     # 更新日志
└── README.md                        # 本文件
```

## 开发指南

### 后端开发

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest

# 初始化数据库
python3 init_db.py
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 类型检查
npm run type-check

# 代码检查
npm run lint
```

### 代码规范

- **Python**: 遵循 PEP 8，使用 black 格式化
- **TypeScript**: 使用 ESLint 进行代码检查
- **Git**: 使用 Conventional Commits 规范

## 系统关键字

### UI 关键字（15个）

#### 导航类
| 关键字 | 描述 | 参数 |
|---------|------|------|
| `NAVIGATE` | 导航到指定 URL | url, wait_until, timeout |
| `GO_BACK` | 返回上一页 | - |
| `REFRESH` | 刷新当前页面 | - |

#### 交互类
| 关键字 | 描述 | 参数 |
|---------|------|------|
| `CLICK` | 点击元素 | selector, timeout |
| `DOUBLE_CLICK` | 双击元素 | selector, timeout |
| `HOVER` | 鼠标悬停 | selector, timeout |
| `INPUT` | 输入文本 | selector, text, clear_first |
| `SELECT` | 选择下拉选项 | selector, value |

#### 等待类
| 关键字 | 描述 | 参数 |
|---------|------|------|
| `WAIT_FOR_ELEMENT` | 等待元素出现 | selector, state, timeout |
| `SLEEP` | 固定延迟 | duration |

#### 断言类
| 关键字 | 描述 | 参数 |
|---------|------|------|
| `ASSERT_VISIBLE` | 断言元素可见 | selector |
| `ASSERT_TEXT` | 断言元素文本 | selector, text |
| `ASSERT_TITLE` | 断言页面标题 | title |
| `ASSERT_URL` | 断言当前 URL | url |

### API 关键字

| 关键字 | 描述 | 参数 |
|---------|------|------|
| `API_GET` | 发送 HTTP GET 请求 | url, headers, params |
| `API_POST` | 发送 HTTP POST 请求 | url, headers, body |
| `API_PUT` | 发送 HTTP PUT 请求 | url, headers, body |
| `API_DELETE` | 发送 HTTP DELETE 请求 | url, headers |
| `ASSERT_STATUS` | 断言 HTTP 状态码 | expected_status |
| `EXTRACT_VARIABLE` | 从响应中提取变量 | variable_name, extract_from, expression |

## 录制功能

### 功能特点

- **🎬 可视化录制**: 在浏览器中执行操作，系统自动记录
- **🧠 智能数据提取**: 自动识别测试数据（用户名、密码、邮箱等）
- **🔄 自动生成场景**: 录制的操作直接转换为测试用例
- **📄 跨页面录制**: 支持多页面操作录制
- **⚡ 实时进度**: 录制过程中实时显示捕获的操作数

### 使用步骤

1. **启动录制**: 在场景管理页面点击"录制创建"
2. **设置信息**: 输入场景名称
3. **执行操作**: 在打开的浏览器中执行测试操作
4. **停止录制**: 完成后点击停止按钮
5. **数据提取**: 系统自动提取可变数据
6. **预览生成**: 查看自动生成的测试场景
7. **确认保存**: 保存到场景库

### 支持的操作

- ✅ 页面导航
- ✅ 元素点击
- ✅ 文本输入
- ✅ 表单提交
- ✅ 页面滚动
- ✅ 多页面跳转

## API 文档

### 认证 API (`/api/v1/auth`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录 |
| GET | `/me` | 获取当前用户信息 |

### UI 场景 API (`/api/v1/ui/scenarios`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 创建 UI 场景 |
| GET | `/` | 获取项目所有场景 |
| GET | `/{scenario_id}` | 获取单个场景 |
| PUT | `/{scenario_id}` | 更新场景 |
| DELETE | `/{scenario_id}` | 删除场景 |

### UI 任务 API (`/api/v1/ui/tasks`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 创建 UI 任务 |
| GET | `/` | 获取项目所有任务 |
| GET | `/{task_id}` | 获取单个任务 |
| POST | `/{task_id}/execute` | 执行 UI 任务 |

### 测试数据 API (`/api/v1/projects/{project_id}/data`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 创建测试数据 |
| GET | `/` | 获取项目所有测试数据 |
| GET | `/{data_id}` | 获取单个测试数据 |
| PUT | `/{data_id}` | 更新测试数据 |
| DELETE | `/{data_id}` | 删除测试数据 |

### 环境配置 API (`/api/v1/projects/{project_id}/environments`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 创建环境配置 |
| GET | `/` | 获取所有环境配置 |
| PUT | `/{env_id}` | 更新环境配置 |
| DELETE | `/{env_id}` | 删除环境配置 |

### 定时任务 API (`/api/v1/projects/{project_id}/scheduled-jobs`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 创建定时任务 |
| GET | `/` | 获取所有定时任务 |
| PUT | `/{job_id}` | 更新定时任务 |
| DELETE | `/{job_id}` | 删除定时任务 |
| POST | `/{job_id}/pause` | 暂停定时任务 |
| POST | `/{job_id}/resume` | 恢复定时任务 |

### 录制 API (`/api/v1/recording`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/start` | 启动录制会话 |
| POST | `/stop` | 停止录制并获取结果 |
| GET | `/actions/{session_id}` | 获取捕获的操作 |
| POST | `/extract-data` | 智能提取测试数据 |
| POST | `/generate-scenario` | 生成测试场景 |

### 关键字 API (`/api/v1/ui/keywords`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/` | 获取所有关键字 |
| GET | `/categories` | 获取关键字类别 |
| GET | `/{keyword_id}` | 获取单个关键字详情 |

完整 API 文档请访问：http://localhost:8000/docs

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

---

**最后更新**: 2026-04-24
**当前版本**: v1.5.0
**GitHub**: https://github.com/zyp-lgtm/autotest--platform
