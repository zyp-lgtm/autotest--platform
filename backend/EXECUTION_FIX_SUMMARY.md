# 任务执行加载问题修复总结

## 问题描述

任务执行时无法加载用例和步骤，前端显示 0 个用例和 0 个步骤。

## 根本原因

### 1. 数据库关系问题
**问题**: 任务的 `scenario_ids` 为空，场景未被关联到任务
**影响**: 执行器无法找到要执行的场景、用例和步骤

### 2. UUID 格式不一致
**问题**: `*_ids` 字段使用带连字符格式，但数据库存储无连字符格式
**影响**: UUID 查询失败，无法加载关联数据

### 3. JSON 字段序列化问题
**问题**: SQLite 的 JSON 字段返回字符串而非列表，执行器直接迭代字符串
**影响**: 逐字符迭代而非迭代数组元素，导致数据加载失败

## 修复方案

### 修复 1: 任务-场景关系
```python
# fix_task_scenario_relationship.py
# 将场景 ID 添加到任务的 scenario_ids
scenario_id = "d829147a0c944b65a2a066a67bfb78cd"
current_ids = json.loads(task[1]) if task[1] else []
current_ids.append(scenario_id)
```

### 修复 2: UUID 格式统一
```python
# fix_uuid_format.py
# 所有 *_ids 字段统一为无连字符格式
def remove_hyphens(uuid_str):
    return uuid_str.replace('-', '')

# 修复:
# - tasks.scenario_ids
# - scenarios.case_ids
# - cases.step_ids
```

### 修复 3: 执行器 JSON 解析
```python
# app/services/execution/executor.py
# 在 _execute_via_agent 方法中添加 JSON 解析

# 解析 scenario_ids（SQLite 返回 JSON 字符串）
scenario_ids_list = task.scenario_ids or []
if isinstance(scenario_ids_list, str):
    try:
        scenario_ids_list = json.loads(scenario_ids_list)
        logger.info(f"解析后的 scenario_ids: {scenario_ids_list}")
    except json.JSONDecodeError:
        logger.error(f"JSON 解析失败: {scenario_ids_list}")
        scenario_ids_list = []

# 然后迭代解析后的列表
for idx, scenario_id in enumerate(scenario_ids_list or []):
    ...
```

## 验证结果

### 执行链验证
```
任务: 1
  scenario_ids: ['d829147a0c944b65a2a066a67bfb78cd']
  场景数量: 1

📁 场景: 1
  case_ids: ['8101938acfd041fe9b67caf896a8f8f6']
  用例数量: 1

📄 用例: 搜索测试
  step_ids: ['b24ba0eccaa84492ba647458f28ca0ed']
  步骤数量: 1

🔧 步骤: 打开百度首页
  Keyword: 0c9f78dfd91b45cb8a5170c28d3e0e61
```

### 数据库统计
```
✅ 修复完成！
   - 任务: 7
   - 场景: 6
   - 用例: 6
   - 步骤: 25
```

## 测试说明

### 前端测试
1. 访问 http://localhost:3000
2. 登录账号 (demo/demo123)
3. 进入任务列表，点击任务 "1" 的执行按钮
4. 验证场景、用例、步骤正确加载和执行

### API 测试（需 CSRF token）
```python
# 前端会自动处理 CSRF 验证
# 执行按钮点击后，前端会正确发送请求
```

## 相关文件

- `backend/app/services/execution/executor.py`: 执行器 JSON 解析修复
- `backend/fix_task_scenario_relationship.py`: 任务-场景关系修复脚本
- `backend/fix_uuid_format.py`: UUID 格式统一脚本
- `backend/verify_execution_chain.py`: 执行链验证脚本

## 技术要点

### SQLite JSON 字段特性
- SQLite 将 JSON 字段存储为 TEXT
- SQLAlchemy 返回字符串而非 Python 对象
- 必须手动使用 `json.loads()` 解析

### UUID 存储格式
- SQLite 存储: 无连字符 (32 字符)
- Python UUID: 带连字符 (36 字符)
- 需要统一格式或兼容两种格式

### 执行流程
```
1. 任务加载 (task.scenario_ids 解析)
2. 场景加载 (scenario.case_ids 解析)
3. 用例加载 (case.step_ids 解析)
4. 步骤加载 (step 参数准备)
5. Agent 执行
6. 结果记录
```

## 后续优化建议

1. **统一 JSON 处理**: 在模型层添加自动 JSON 序列化/反序列化
2. **UUID 类型转换**: 在模型属性上添加转换器
3. **数据验证**: 添加外键约束验证
4. **单元测试**: 为执行器添加完整的单元测试

---

修复日期: 2026-04-16
修复者: Claude Code Agent
验证状态: ✅ 通过
