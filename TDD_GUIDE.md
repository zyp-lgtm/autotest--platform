# TDD 开发指南

> **测试驱动开发 (Test-Driven Development)** 是本项目强制要求的开发模式

---

## 🎯 TDD 核心原则

### 红绿重构循环 (Red-Green-Refactor)

```
┌─────────────────────────────────────────────────────┐
│  1. RED    - 编写失败的测试                           │
│  2. GREEN  - 编写最小化代码使测试通过                   │
│  3. REFACTOR - 重构优化代码，保持测试通过               │
└─────────────────────────────────────────────────────┘
```

### 关键规则

```markdown
✅ 必须先写测试，后写代码
✅ 测试失败后才编写实现
✅ 只编写使测试通过的最小代码
✅ 所有测试通过后才能重构
✅ 重构后必须保持测试通过
```

---

## 📋 TDD 实施流程

### 1. 性能优化 TDD 流程

#### 第一步：编写基准测试（Red）

```python
# test_cache_optimization.py
import pytest
from unittest.mock import patch
from app.api.auth import get_current_user

def test_cache_reduces_db_queries():
    """
    测试：缓存应该减少数据库查询次数

    Given: 用户信息在缓存中
    When: 多次调用 get_current_user
    Then: 只有第一次查询数据库，后续从缓存返回
    """
    token = "valid_token"
    user = User(id="123", username="demo")

    # 第一次调用 - 应该查询数据库
    with patch('app.models.User.query') as mock_query:
        mock_query.return_value.first.return_value = user

        result = get_current_user(token=token)

        assert mock_query.call_count == 1
        assert result.username == "demo"

    # 第二次调用 - 应该从缓存返回，不查询数据库
    with patch('app.models.User.query') as mock_query:
        mock_query.return_value.first.return_value = user

        result = get_current_user(token=token)

        # ✅ 测试失败：当前没有缓存，会再次查询数据库
        assert mock_query.call_count == 0
```

**运行测试**:
```bash
pytest test_cache_optimization.py -v
# 预期：FAILED - 因为还没有实现缓存
```

#### 第二步：实现缓存功能（Green）

```python
# app/api/auth.py
from ...utils.cache import get_cache

@router.get("/me")
async def get_current_user(token: str = Depends(get_token_from_cookie_or_header)):
    """获取当前用户信息（带缓存）"""
    cache = get_cache()
    payload = verify_token(token)
    username = payload.get("sub")

    # 尝试从缓存获取
    cache_key = f"user_info:{username}"
    cached_user = cache.get(cache_key)
    if cached_user:
        return UserResponse(**cached_user)

    # 缓存未命中，查询数据库
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user_response = UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=user.role,
        created_at=user.created_at
    )

    # 存入缓存
    cache.set(cache_key, user_response.dict(), ttl=600)

    return user_response
```

**运行测试**:
```bash
pytest test_cache_optimization.py -v
# 预期：PASSED - 缓存功能正常工作
```

#### 第三步：重构优化（Refactor）

```python
# 优化：提取缓存逻辑到单独的函数
def get_user_with_cache(db: Session, username: str) -> Optional[UserResponse]:
    """获取用户信息（带缓存）"""
    cache = get_cache()
    cache_key = f"user_info:{username}"

    # 尝试从缓存获取
    cached_user = cache.get(cache_key)
    if cached_user:
        return UserResponse(**cached_user)

    # 查询数据库
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None

    user_response = UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=user.role,
        created_at=user.created_at
    )

    # 存入缓存
    cache.set(cache_key, user_response.dict(), ttl=600)

    return user_response

@router.get("/me")
async def get_current_user(token: str = Depends(get_token_from_cookie_or_header)):
    """获取当前用户信息"""
    payload = verify_token(token)
    username = payload.get("sub")

    user_response = get_user_with_cache(db, username)
    if not user_response:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user_response
```

**运行测试**:
```bash
pytest test_cache_optimization.py -v
# 预期：PASSED - 重构后测试仍然通过
```

---

### 2. API 开发 TDD 流程

#### 第一步：编写失败的测试

```python
# test_task_api.py
def test_create_task_returns_201():
    """
    测试：创建任务应该返回 201 状态码

    Given: 有效的任务数据
    When: POST /api/v1/tasks
    Then: 返回 201 Created 和任务 ID
    """
    task_data = {
        "name": "测试任务",
        "description": "TDD 测试",
        "project_id": "project-123"
    }

    response = client.post("/api/v1/tasks", json=task_data)

    # ✅ 测试失败：API 还未实现
    assert response.status_code == 201
    assert "id" in response.json()
```

#### 第二步：实现最小化功能

```python
@router.post("/tasks", status_code=201)
async def create_task(task: TaskCreate):
    # 最小化实现：只返回必需字段
    new_task = {"id": str(uuid.uuid4())}
    return new_task
```

#### 第三步：完善功能并重构

```python
@router.post("/tasks", status_code=201)
async def create_task(
    task: TaskCreate,
    project_id: str,
    db: Session = Depends(get_db)
):
    # 完整实现
    new_task = UITask(**task.dict(), project_id=project_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "id": str(new_task.id),
        "name": new_task.name,
        "created_at": new_task.created_at.isoformat()
    }
```

---

## 🧪 测试类型和要求

### 1. 单元测试

**要求**: 所有业务逻辑必须有单元测试

```python
# test_user_service.py
def test_hash_password():
    """测试密码哈希"""
    password = "MyPassword123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)

def test_verify_token_success():
    """测试 Token 验证成功"""
    token = create_access_token({"sub": "demo"})
    payload = verify_token(token)

    assert payload["sub"] == "demo"
```

### 2. 集成测试

**要求**: API 端点必须有集成测试

```python
# test_task_integration.py
def test_create_and_get_task():
    """测试创建和获取任务"""
    # 创建任务
    response = client.post("/api/v1/tasks", json={...})
    task_id = response.json()["id"]

    # 获取任务
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
```

### 3. 性能测试

**要求**: 优化必须有性能基准测试

```python
# test_performance.py
import time

def test_cache_improves_performance():
    """测试缓存提升性能"""
    # 第一次调用（无缓存）
    start = time.time()
    get_current_user(token="test_token")
    first_call_time = time.time() - start

    # 第二次调用（有缓存）
    start = time.time()
    get_current_user(token="test_token")
    second_call_time = time.time() - start

    # 缓存应该快 10 倍以上
    assert second_call_time < first_call_time / 10
```

### 4. 回归测试

**要求**: 修复 Bug 后必须有回归测试

```python
# test_regression.py
def test_login_does_not_leak_password_in_logs(caplog):
    """
    回归测试：登录不应该在日志中泄露密码

    背景：之前版本在创建用户时记录了哈希密码
    修复：移除了密码日志
    """
    response = client.post("/api/v1/auth/login", json={
        "username": "demo",
        "password": "SecretPassword123"
    })

    # 检查日志中不包含密码
    assert "SecretPassword123" not in caplog.text
    assert "hash" not in caplog.text.lower()
```

---

## ✅ TDD 检查清单

### 开发前

- [ ] 编写失败测试（Red）
- [ ] 确认测试失败原因明确
- [ ] 记录当前性能基准（优化场景）

### 开发中

- [ ] 编写最小化代码（Green）
- [ ] 运行测试确认通过
- [ ] 不添加额外功能

### 开发后

- [ ] 重构代码（Refactor）
- [ ] 确认所有测试通过
- [ ] 运行完整测试套件
- [ ] 更新相关文档

### 性能优化特别要求

- [ ] 对比优化前后性能
- [ ] 记录性能提升数据
- [ ] 确认无回归问题
- [ ] 更新缓存策略文档

---

## 🚫 常见错误

### 错误 1：先写代码后写测试

```python
# ❌ 错误做法
def get_user(user_id):
    return db.query(User).get(user_id)

# 然后写测试 - 这不是 TDD
def test_get_user():
    assert get_user(1) is not None
```

```python
# ✅ 正确做法
def test_get_user():
    # 先写测试
    assert get_user(1) is not None

# 然后实现
def get_user(user_id):
    return db.query(User).get(user_id)
```

### 错误 2：一次性写太多代码

```python
# ❌ 错误做法
def get_user(user_id):
    # 一次性实现所有功能
    user = db.query(User).get(user_id)
    if user:
        cache.set(user_id, user)
        invalidate_pattern(f"user:*")
        send_notification(user)
        log_access(user)
    return user
```

```python
# ✅ 正确做法 - 循序渐进
# 第 1 版：只返回用户
def get_user(user_id):
    return db.query(User).get(user_id)

# 第 2 版：添加缓存
def get_user(user_id):
    cached = cache.get(user_id)
    if cached:
        return cached
    user = db.query(User).get(user_id)
    cache.set(user_id, user)
    return user

# 第 3 版：添加通知（测试通过后）
def get_user(user_id):
    # ... 前面的代码
    send_notification(user)
    return user
```

### 错误 3：跳过重构

```python
# ❌ 测试通过后不重构
def get_user(user_id):
    user = db.query(User).filter(User.id == user_id).first()
    if user is not None:
        return user
    else:
        return None

# ✅ 测试通过后重构
def get_user(user_id):
    return db.query(User).filter(User.id == user_id).first()
```

---

## 📚 相关资源

### 测试工具
- `pytest` - 测试框架
- `pytest-cov` - 覆盖率测试
- `pytest-asyncio` - 异步测试
- `unittest.mock` - Mock 对象

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest test_cache.py

# 查看覆盖率
pytest --cov=app --cov-report=html

# 运行性能测试
pytest -m performance
```

---

**记住**: TDD 不是可选的，而是本项目的基本要求。所有优化和新功能必须遵循 TDD 模式！

*最后更新: 2026-04-16*
