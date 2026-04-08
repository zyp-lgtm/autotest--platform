# 测试自动化平台 - 项目宪法

本文档定义了项目的技术原则、开发规范和不可协商的规则，确保项目长期健康发展。

> **宪法原则**: 这些规则除非团队共识和充分讨论，否则不得变更。

---

## 🎯 核心原则

### 1. 开发者体验优先
- **30分钟启动原则**: 新成员必须在 30 分钟内从零启动项目
- **零配置开箱即用**: 开发环境不需要复杂的服务配置
- **快速反馈**: 减少开发-测试-部署的循环时间

### 2. 跨环境兼容性
- **一次编写，到处运行**: 代码必须在所有环境工作
- **抽象差异**: 通过 ORM 和配置抽象处理环境差异
- **避免供应商锁定**: 不依赖特定平台或专有功能

### 3. 代码质量标准
- **类型安全**: 所有 API 必须有完整的类型注解
- **测试覆盖**: 关键路径必须有测试
- **代码审查**: 重大变更必须经过 Code Review

---

## 🗄️ 数据库架构宪法

### 核心规则

#### **1. 数据库类型选择**

```
开发环境: SQLite
测试环境: SQLite
生产环境: PostgreSQL 14+
```

**理由**:
- **SQLite**: 零配置，内置 Python 支持，快速启动
- **PostgreSQL**: 生产级特性，高并发，ACID 事务

#### **2. 数据类型兼容性强制要求**

**禁止使用的类型** (PostgreSQL 特有):
```python
❌ ARRAY(String)        # 仅 PostgreSQL
❌ JSONB               # 仅 PostgreSQL
❌ UUID (直接类型)     # 依赖数据库实现
```

**必须使用的类型** (跨数据库兼容):
```python
✅ JSON(default=list)    # 存储为 JSON，ORM 层处理
✅ String                # UUID 存储为 TEXT
✅ DateTime(timezone=True) # 时区感知
✅ Boolean               # 布尔值
✅ Integer/Float/Decimal # 数值类型
```

#### **3. 模型定义规范**

```python
from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID  # 仅用于 UUID 生成
import uuid

class BaseModel(Base):
    __tablename__ = "base_models"

    # ✅ 正确: 使用 UUID 类型但允许 ORM 处理差异
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ✅ 正确: 使用 JSON 替代 ARRAY
    tags = Column(JSON, default=list)

    # ✅ 正确: 时区感知时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### **4. 为什么这样设计？**

**问题案例**: 2026-04-08 登录 API 500 错误
```
原始错误:
  psycopg2.OperationalError: connection to server at "localhost" port 5432 failed

根本原因:
  - 开发环境配置要求 PostgreSQL
  - PostgreSQL 需要单独安装和启动
  - 增加新成员开发环境设置成本

解决方案:
  - 开发环境改用 SQLite
  - 统一使用跨数据库兼容类型
  - ORM 层抽象处理差异
```

**收益**:
- ✅ 开发环境零配置
- ✅ 新成员 30 分钟内可上手
- ✅ CI/CD 简化（无需数据库服务）
- ✅ 生产环境保持高性能

**代价**:
- ⚠️  需要维护数据库迁移脚本
- ⚠️ 丢失 PostgreSQL 特有功能（ARRAY, JSONB）
- ⚠️ JSON 类型查询语法略有不同

---

## 🔧 环境配置宪法

### 配置管理规则

#### **1. 配置文件层次**

```python
# app/core/config.py
class Settings(BaseSettings):
    # 环境自动检测
    ENV: str = os.getenv("ENV", "development")

    # 根据环境选择数据库
    if ENV == "production":
        DATABASE_URL = os.getenv("DATABASE_URL")  # 生产环境从环境变量读取
    else:
        # 开发/测试环境默认使用 SQLite
        DATABASE_URL = "sqlite:///./test_platform.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_ignore_empty=True,
        extra="ignore"
    )
```

#### **2. 环境变量定义**

**开发环境** (.env.development):
```bash
ENV=development
# DATABASE_URL 自动使用 SQLite
```

**生产环境** (.env.production):
```bash
ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0
JWT_SECRET=your-secret-key
```

#### **3. 禁止事项**

```markdown
❌ 禁止硬编码配置
❌ 禁止在代码中检查 if os.getenv("ENV") == "production"
❌ 禁止提交敏感信息到仓库
❌ 禁止在代码中添加平台特定的逻辑
```

---

## 📝 开发规范

### 代码风格

#### **1. Python 代码规范**
- 遵循 PEP 8
- 使用 Type Hints
- Docstring 遵循 Google Style
- 最大行长度: 100 字符

#### **2. API 设计规范**
- RESTful 设计原则
- 统一的错误响应格式
- 版本化 API (/api/v1/)
- OpenAPI 文档自动生成

#### **3. 前端代码规范**
- React 函数组件
- TypeScript 严格模式
- 组件文件按功能组织
- Hooks 规范使用

### Git 工作流

#### **1. 分支策略**
```
main          - 生产环境代码
develop       - 开发主分支
feature/*     - 功能分支
hotfix/*      - 紧急修复分支
```

#### **2. 提交信息规范**
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
refactor: 重构
test: 测试相关
chore: 构建/工具配置
```

#### **3. 代码审查规范**
- 所有 PR 必须经过至少 1 人审查
- 重大变更需要团队讨论
- 自动化测试必须通过
- 代码风格检查必须通过

---

## 🚀 部署宪法

### 开发环境

**要求**:
- SQLite 数据库
- 本地文件存储
- DEBUG 模式开启

**启动命令**:
```bash
# 后端
cd backend
python3 init_db.py  # 初始化数据库（首次）
python3 -m uvicorn app.main:app --reload

# 前端
cd frontend
npm run dev

# Agent
cd agent
python3 agent.py
```

### 生产环境

**要求**:
- PostgreSQL 14+ 数据库
- Redis 缓存
- Gunicorn/Nginx 部署
- 环境变量配置

**禁止事项**:
```markdown
❌ 禁止使用 SQLite in production
❌ 禁止 DEBUG=True in production
❌ 禁止硬编码密钥
❌ 禁止直接暴露后端端口
```

---

## 📚 技术决策记录

### 重大技术决策

#### **决策 #1: 数据库架构 (2026-04-08)**

**问题**: 登录 API 返回 500 错误，开发环境无法使用

**分析**:
- PostgreSQL 需要单独安装和配置
- 新成员设置开发环境困难
- 开发环境启动时间长
- 增加认知负担

**决策**:
- 开发/测试环境使用 SQLite
- 生产环境使用 PostgreSQL
- 统一使用 JSON 类型替代 ARRAY
- ORM 层抽象数据库差异

**收益**:
- ✅ 开发环境零配置
- ✅ 新成员快速上手
- ✅ CI/CD 简化
- ✅ 生产环境保持高性能

**风险缓解**:
- 📋 编写数据库迁移脚本
- 📋 完善测试覆盖
- 📋 CI 环境使用 SQLite
- 📋 PR 环境检查 PostgreSQL 兼容性

**验证**:
- ✅ 登录 API 正常工作
- ✅ 用户创建/查询正常
- ✅ JSON 类型数据处理正常

---

## 🎓 新成员上手指南

### 快速启动 (30 分钟内)

#### **1. 环境准备** (5 分钟)
```bash
# 检查 Python 版本
python3 --version  # 需要 3.11+

# 检查 Node.js 版本
node --version      # 需要 16+

# 检查 git
git --version
```

#### **2. 项目设置** (5 分钟)
```bash
# 克隆项目
git clone <repository>

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

#### **3. 初始化数据库** (5 分钟)
```bash
cd backend
python3 init_db.py  # 创建数据库和测试用户
```

#### **4. 启动服务** (5 分钟)
```bash
# 终端1: 启动后端
cd backend
python3 -m uvicorn app.main:app --reload

# 终端2: 启动前端
cd frontend
npm run dev

# 可选: 终端3: 启动 Agent
cd agent
python3 agent.py
```

#### **5. 测试验证** (10 分钟)
```bash
# 访问 http://localhost:3000
# 使用 demo/demo123 登录
# 验证基本功能
```

---

## 🔍 问题诊断指南

### 常见问题

#### **1. 登录失败**
```
症状: API 返回 500 Internal Server Error
原因: 数据库连接失败
解决:
  - 检查 DATABASE_URL 配置
  - 开发环境确保 test_platform.db 存在
  - 运行 python3 init_db.py 初始化数据
```

#### **2. 前端空白页**
```
症状: 页面完全空白，无错误信息
原因: 组件渲染错误或路由配置问题
解决:
  - 按 F12 查看控制台错误
  - 检查 /api/v1/health 端点
  - 验证 token 是否有效
```

#### **3. Agent 不响应**
```
症状: Agent 显示已连接但不执行任务
原因: WebSocket 连接断开或进程崩溃
解决:
  - 检查 Agent 日志: tail -f agent.log
  - 重启 Agent: python agent.py
  - 验证后端 /agent 端点可用
```

---

## 📖 相关文档

- **DEVELOPMENT.md**: 开发环境设置
- **DEPLOYMENT.md**: 生产环境部署
- **CONTRIBUTING.md**: 贡献指南
- **README.md**: 项目概述和快速开始

---

## 🔄 宪法修订流程

### 重大变更流程

1. **提案**: 在团队频道讨论变更建议
2. **讨论**: 至少 2 天讨论期，允许反对意见
3. **决策**: 团队成员投票，超过 2/3 多数通过
4. **文档**: 更新相关文档和此宪法
5. **实施**: 更新代码，合并 PR
6. **验证**: 在所有环境测试验证

### 小型优化流程

1. **文档**: 直接在文档中记录
2. **PR**: 创建 Pull Request
3. **审查**: 至少 1 人审查通过
4. **合并**: 合并到主分支

---

## ⚖️ 违宪处理

### 违宪后果

- **轻微违宪**: 提交被拒绝，要求修复
- **中度违宪**: 团队警告，需要回滚
- **严重违宪**: 移除写访问权限

### 豁免流程

如果特殊情况需要违反宪法:
1. 在团队频道提出豁免请求
2. 说明理由和替代方案
3. 团队投票决定
4. 记录豁免决策和期限

---

## 📞 联系方式

**宪法维护者**: 项目负责人
**更新频率**: 每季度审查一次
**反馈渠道**: Issues, Pull Requests, 团队会议

---

*最后更新: 2026-04-08*
*宪法版本: 1.0*
