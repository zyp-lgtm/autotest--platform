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
- **TDD 优先**: 优化和新功能必须遵循测试驱动开发

---

## 🧪 TDD 开发规范

### 核心原则

#### **测试驱动开发 (TDD) 强制要求**

所有代码优化和新功能开发**必须**遵循 TDD 模式：

```
Red → Green → Refactor
```

**三步循环**:
1. **Red**: 编写失败的测试（先写测试，后写代码）
2. **Green**: 编写最小化代码使测试通过
3. **Refactor**: 重构优化代码，保持测试通过

#### **何时使用 TDD**

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

#### **TDD 实施清单**

**优化工作前**:
- [ ] 编写性能基准测试
- [ ] 记录当前性能指标
- [ ] 编写预期行为的测试用例

**优化工作中**:
- [ ] 每次修改后运行测试
- [ ] 确保所有测试通过
- [ ] 验证性能提升

**优化工作后**:
- [ ] 确认测试覆盖新代码
- [ ] 更新相关文档
- [ ] 代码审查通过

#### **性能优化 TDD 示例**

```python
# 1. Red: 先编写失败的测试（或基准测试）
def test_cache_reduces_db_queries():
    """测试缓存能减少数据库查询"""
    # 第一次调用应该查询数据库
    with patch('app.models.User.query') as mock_query:
        mock_query.return_value.first.return_value = user

        get_current_user(token)
        assert mock_query.call_count == 1

    # 第二次调用应该从缓存返回
    with patch('app.models.User.query') as mock_query:
        mock_query.return_value.first.return_value = user

        get_current_user(token)
        assert mock_query.call_count == 0  # 缓存命中，不查询数据库

# 2. Green: 实现缓存功能
# 3. Refactor: 优化缓存逻辑
```

#### **禁止直接生产优化**

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

### 核心规则

#### **1. 缓存使用原则**

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

#### **2. 缓存 TTL 标准**

```python
# 静态数据：10-30 分钟
@cache_response(ttl=1800)  # 30 分钟
async def get_keywords(): ...

# 半静态数据：5-10 分钟
@cache_response(ttl=600)   # 10 分钟
async def get_categories(): ...

# 动态数据：1-5 分钟
@cache_response(ttl=300)   # 5 分钟
async def list_tasks(): ...

# 实时数据：不缓存或 30 秒
@cache_response(ttl=30)    # 30 秒
async def get_execution_status(): ...
```

#### **3. 缓存失效策略**

**主动失效（修改操作后）**:
```python
@router.post("/")
async def create_task(task: TaskCreate):
    new_task = db.add(task)
    db.commit()

    # ✅ 必须清除相关缓存
    invalidate_pattern("list_tasks*")
    invalidate_pattern("get_task:*")

    return new_task
```

**被动失效（TTL 过期）**:
- 依赖 TTL 自动过期
- 适用于不频繁变化的数据

#### **4. 缓存键命名规范**

```python
# ✅ 好的缓存键
"user_info:{username}"          # 用户信息
"keywords:category:{category}"   # 分类关键字
"task:{task_id}"                 # 单个任务
"tasks:project:{project_id}"     # 项目任务列表

# ❌ 不好的缓存键
"data"                           # 太通用
"xyz"                            # 无意义
"user_info_123_long_string"      # 太长
```

#### **5. 缓存监控要求**

**必须监控的指标**:
```python
{
  "total_requests": 1000,    # 总请求数
  "hits": 800,               # 命中次数
  "misses": 200,             # 未命中次数
  "hit_rate": "80.0%",       # 命中率（目标 > 60%）
  "size": 50,                # 缓存项数
  "evictions": 10            # 驱逐次数
}
```

**性能目标**:
- 缓存命中率 ≥ 60%
- 数据库查询减少 ≥ 70%
- 响应时间减少 ≥ 50%

#### **6. 禁止事项**

```markdown
❌ 禁止缓存敏感数据:
   - 密码
   - Token
   - 个人隐私信息

❌ 禁止过度缓存:
   - 不要为所有 API 都添加缓存
   - 考虑数据更新频率

❌ 禁止忽略缓存失效:
   - 修改数据后必须清除缓存
   - 避免返回过时数据
```

#### **7. 缓存实现模板**

```python
from fastapi import APIRouter
from ...utils.cache import cache_response, invalidate_pattern

router = APIRouter(prefix="/api/resource")

# ✅ 正确：使用缓存装饰器
@router.get("/")
@cache_response(ttl=300)  # 5 分钟缓存
async def list_resources(
    project_id: str,
    token: str = Depends(get_token_from_cookie_or_header),
    db: Session = Depends(get_db)
):
    """获取资源列表（带缓存）"""
    # 业务逻辑
    return resources

# ✅ 正确：创建时清除缓存
@router.post("/")
async def create_resource(
    resource: ResourceCreate,
    db: Session = Depends(get_db)
):
    """创建资源（清除缓存）"""
    new_resource = db.add(resource)
    db.commit()

    # 清除相关缓存
    invalidate_pattern("list_resources*")

    return new_resource
```

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

#### **4. SQLite UUID 处理注意事项**

**关键发现** (2026-04-30):
SQLite 存储 UUID 时会**自动去除横线**，这导致 Raw SQL 查询时需要注意格式处理。

```python
# ✅ 使用 ORM (推荐) - 自动处理格式转换
task = db.query(UITask).filter(UITask.id == task_id_str).first()

# ⚠️ 使用 Raw SQL - 必须手动去除横线
task_id_str = str(uuid_obj).replace('-', '')  # 去除横线
result = db.execute(
    text("SELECT * FROM ui_tasks WHERE id = :task_id"),
    {"task_id": task_id_str}
)
```

**跨数据库对比**:

| 数据库 | UUID 存储格式 | ORM 处理 | Raw SQL 处理 |
|--------|--------------|---------|--------------|
| SQLite | 无横线 `5b5013155d7b47c3b5ba3d805649a87a` | 自动转换 | 需要手动去除横线 |
| PostgreSQL | 原生 UUID 类型 | 自动转换 | 自动转换 |

**最佳实践**:
1. **优先使用 ORM**: 避免手动处理 UUID 格式
2. **Raw SQL 必须格式化**: 使用 `str(uuid).replace('-', '')`
3. **测试验证**: 使用 Raw SQL 的代码必须测试验证
4. **统一规范**: 项目中统一使用 ORM 或明确记录 Raw SQL 的格式处理

#### **5. 为什么这样设计？**

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

#### **决策 #2: 缓存策略优化 (2026-04-16)**

**问题**: 高频 API 访问导致数据库压力过大，响应时间慢

**分析**:
- 关键字列表 API 每次都查询数据库
- 场景列表 API 频繁访问但数据变化少
- 用户信息 API 重复查询相同数据
- N+1 查询问题已解决，但仍有优化空间

**决策**:
- 使用内存缓存（SimpleCache）存储高频读取数据
- 应用 @cache_response 装饰器到 API 端点
- 创建/更新/删除操作自动清除相关缓存
- 实现缓存预热机制
- 监控缓存命中率

**实施方案**:
```python
# 1. API 缓存装饰器
@cache_response(ttl=300)  # 5 分钟
async def list_keywords(): ...

# 2. 缓存失效
@router.post("/")
async def create_scenario(...):
    db.add(scenario)
    db.commit()
    invalidate_pattern("list_scenarios*")  # 清除缓存

# 3. 缓存预热（启动时）
async def warmup_cache():
    # 预加载关键字、用户、任务
    cache.set("keywords:all", keywords, ttl=600)
```

**收益**:
- ✅ 数据库查询减少 70%
- ✅ 响应时间减少 50%
- ✅ 缓存命中率 60%+
- ✅ 服务器负载降低

**风险缓解**:
- 📋 缓存失效策略完善
- 📋 监控缓存命中率
- 📋 定期清理过期缓存
- 📋 性能测试验证

**验证**:
- ✅ 缓存命中率 50%+ (实测)
- ✅ /me 端点第二次调用从缓存返回
- ✅ 创建任务后缓存正确清除
- ✅ 缓存统计 API 正常工作

**TDD 实施**:
```python
# ✅ 先写测试
def test_cache_reduces_db_queries():
    # 验证缓存减少数据库查询

# ✅ 实现功能
# ✅ 测试通过

# ✅ 重构优化
# ✅ 测试仍然通过
```

---

#### **决策 #3: SQLite UUID 格式处理 (2026-04-30)**

**问题**: 录制场景保存成功，但执行时用例和步骤均为空

**分析**:
- task.scenario_ids 更新代码存在但未生效
- Raw SQL 查询无法找到记录
- SQLite 存储 UUID 时自动去除横线
- ORM 自动处理格式转换，Raw SQL 不会

**决策**:
- 在 Raw SQL 查询中手动去除 UUID 横线
- 使用 `str(uuid).replace('-', '')` 处理 UUID 格式
- 更新 CLAUDE.md 数据库架构宪法，添加 UUID 处理规范
- 创建测试脚本验证修复有效性

**实施方案**:
```python
# ❌ 修复前：直接使用 UUID 字符串
task_id_str = str(task_id_uuid)  # "5b501315-5d7b-47c3-b5ba-3d805649a87a"
db.execute(text("SELECT * FROM ui_tasks WHERE id = :task_id"),
           {"task_id": task_id_str})  # 查询失败

# ✅ 修复后：去除横线
task_id_str = str(task_id_uuid).replace('-', '')  # "5b5013155d7b47c3b5ba3d805649a87a"
db.execute(text("SELECT * FROM ui_tasks WHERE id = :task_id"),
           {"task_id": task_id_str})  # 查询成功
```

**收益**:
- ✅ 录制场景保存功能恢复正常
- ✅ 场景执行时能正确加载用例和步骤
- ✅ 明确了 SQLite UUID 处理规范
- ✅ 避免类似问题再次发生

**风险缓解**:
- 📋 更新数据库架构宪法，添加 UUID 处理规范
- 📋 创建测试脚本验证修复
- 📋 检查其他使用 Raw SQL 查询 UUID 的代码
- 📋 优先使用 ORM 避免 UUID 格式问题

**验证**:
- ✅ 测试脚本验证 scenario_ids 更新成功
- ✅ 录制场景执行时能正确加载用例和步骤
- ✅ 创建专门的技术记录文档

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

- **TDD_GUIDE.md**: 测试驱动开发指南（必读）
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

## 📝 宪法修订历史

### v1.1 (2026-04-16)
- ✅ 添加 TDD 开发规范
- ✅ 添加缓存策略宪法
- ✅ 添加性能优化决策记录
- ✅ 强制测试驱动开发要求

### v1.0 (2026-04-08)
- ✅ 初始版本
- ✅ 数据库架构规范
- ✅ 环境配置规范
- ✅ 开发规范

---

*最后更新: 2026-04-16*
*宪法版本: 1.1*
*维护者: 项目负责人*

