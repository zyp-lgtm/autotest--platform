# 测试自动化平台 - 项目宪法

本文档定义项目的技术原则、开发规范和不可协商的规则。

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
- **TDD 优先**: 优化和新功能必须遵循测试驱动开发

---

## 🧪 TDD 开发规范

### 核心原则

所有代码优化和新功能开发**必须**遵循 TDD 模式：`Red → Green → Refactor`

**何时使用 TDD**:
```markdown
✅ 必须使用 TDD:
   - 性能优化（缓存、查询优化）
   - 新功能开发
   - Bug 修复（先写失败用例）
   - API 端点开发
   - 数据模型变更

⚠️  可以灵活处理:
   - 配置文件修改
   - 文档更新
   - 代码格式调整
```

**禁止直接生产优化**:
```markdown
❌ 禁止行为:
   - 直接在生产环境测试优化
   - 优化后不编写测试
   - 忽略回归测试
   - 跳过性能基准测试

✅ 正确做法:
   - 先写测试，再优化
   - 使用测试环境验证
   - 对比优化前后性能
   - 记录优化效果
```

---

## ⚡ 缓存策略宪法

### 缓存使用原则

**必须缓存的场景**:
```markdown
✅ 高频读取、低频修改的数据:
   - 关键字列表
   - 场景列表
   - 用户信息
   - 配置数据
   - 类别/枚举数据
```

**不应缓存的场景**:
```markdown
❌ 频繁修改的数据:
   - 实时执行状态
   - 计数器
   - 临时数据
❌ 个性化数据:
   - 用户会话（使用 HttpOnly Cookie）
   - 临时令牌
```

### 缓存 TTL 标准

```python
# 静态数据：10-30 分钟
@cache_response(ttl=1800)  # 30 分钟

# 半静态数据：5-10 分钟
@cache_response(ttl=600)   # 10 分钟

# 动态数据：1-5 分钟
@cache_response(ttl=300)   # 5 分钟

# 实时数据：不缓存或 30 秒
@cache_response(ttl=30)    # 30 秒
```

### 缓存失效策略

**主动失效（修改操作后）**:
```python
@router.post("/")
async def create_task(task: TaskCreate):
    new_task = db.add(task)
    db.commit()
    invalidate_pattern("list_tasks*")  # 必须清除相关缓存
    return new_task
```

### 性能目标

- 缓存命中率 ≥ 60%
- 数据库查询减少 ≥ 70%
- 响应时间减少 ≥ 50%

### 禁止事项

```markdown
❌ 禁止缓存敏感数据: 密码、Token、个人隐私信息
❌ 禁止过度缓存: 不要为所有 API 都添加缓存
❌ 禁止忽略缓存失效: 修改数据后必须清除缓存
```

---

## 🗄️ 数据库架构宪法

### 核心规则

**数据库类型选择**:
```
开发环境: SQLite
测试环境: SQLite
生产环境: PostgreSQL 14+
```

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

### SQLite UUID 处理注意事项

SQLite 存储 UUID 时会**自动去除横线**，Raw SQL 查询时必须手动处理：

```python
# ✅ 使用 ORM (推荐) - 自动处理格式转换
task = db.query(UITask).filter(UITask.id == task_id_str).first()

# ⚠️ 使用 Raw SQL - 必须手动去除横线
task_id_str = str(uuid_obj).replace('-', '')  # 去除横线
result = db.execute(text("SELECT * FROM ui_tasks WHERE id = :task_id"), {"task_id": task_id_str})
```

**最佳实践**:
1. **优先使用 ORM**: 避免手动处理 UUID 格式
2. **Raw SQL 必须格式化**: 使用 `str(uuid).replace('-', '')`
3. **测试验证**: 使用 Raw SQL 的代码必须测试验证

---

## 🔧 环境配置宪法

### 配置管理规则

```python
class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "development")

    if ENV == "production":
        DATABASE_URL = os.getenv("DATABASE_URL")
    else:
        DATABASE_URL = "sqlite:///./test_platform.db"
```

### 禁止事项

```markdown
❌ 禁止硬编码配置
❌ 禁止在代码中检查 if os.getenv("ENV") == "production"
❌ 禁止提交敏感信息到仓库
❌ 禁止在代码中添加平台特定的逻辑
```

---

## 📝 开发规范

### 代码风格

**Python**: 遵循 PEP 8，使用 Type Hints，Google Style Docstring，最大行长度 100 字符

**API**: RESTful 设计，统一错误响应格式，版本化 API (/api/v1/)，OpenAPI 文档自动生成

**前端**: React 函数组件，TypeScript 严格模式，组件文件按功能组织，Hooks 规范使用

### Git 工作流

**分支策略**:
```
main          - 生产环境代码
develop       - 开发主分支
feature/*     - 功能分支
hotfix/*      - 紧急修复分支
```

**提交信息规范**: feat / fix / docs / refactor / test / chore

---

## 🚀 部署宪法

### 开发环境

- SQLite 数据库
- 本地文件存储
- DEBUG 模式开启

**启动命令**:
```bash
# 后端
cd backend && python3 init_db.py && python3 -m uvicorn app.main:app --reload

# 前端
cd frontend && npm run dev

# Agent
cd agent && python3 agent.py
```

### 生产环境

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

## 🎓 新成员上手指南

### 快速启动 (30 分钟内)

**1. 环境准备** (5 分钟):
```bash
python3 --version  # 需要 3.11+
node --version      # 需要 16+
git --version
```

**2. 项目设置** (5 分钟):
```bash
git clone <repository>
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

**3. 初始化数据库** (5 分钟):
```bash
cd backend && python3 init_db.py
```

**4. 启动服务** (5 分钟):
```bash
# 终端1: 后端
cd backend && python3 -m uvicorn app.main:app --reload

# 终端2: 前端
cd frontend && npm run dev

# 可选: 终端3: Agent
cd agent && python3 agent.py
```

**5. 测试验证** (10 分钟):
```bash
# 访问 http://localhost:3000
# 使用 demo/demo123 登录
```

---

## 🔍 问题诊断指南

### 常见问题

**登录失败**:
- 检查 DATABASE_URL 配置
- 开发环境确保 test_platform.db 存在
- 运行 python3 init_db.py 初始化数据

**前端空白页**:
- 按 F12 查看控制台错误
- 检查 /api/v1/health 端点
- 验证 token 是否有效

**Agent 不响应**:
- 检查 Agent 日志: tail -f agent.log
- 重启 Agent: python agent.py
- 验证后端 /agent 端点可用

---

## 📖 相关文档

- **TDD_GUIDE.md**: 测试驱动开发指南（必读）
- **README.md**: 项目概述和快速开始
- **docs/guides/**: 各类功能指南
- **docs/reports/**: 技术决策记录和审计报告

---

*最后更新: 2026-05-11*
*宪法版本: 1.2*
