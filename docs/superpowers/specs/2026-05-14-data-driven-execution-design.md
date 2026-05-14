# 数据驱动执行 — 设计文档

日期: 2026-05-14
状态: approved

## 概述

当前系统录制时会自动提取测试数据并创建 DataBinding，但执行引擎 `data_row_index` 硬编码为 0，导致即使有多行测试数据，场景只执行一次。同时录制时自动生成的变体数据（边界值、特殊字符）用户并不需要。本次改动实现"录制提取原始数据 + 按数据行迭代执行"，满足"几组数据就执行几次"的预期。

## 1. 数据模型变更

### 1.1 TestData 新增字段

```python
# app/models/test_data.py
class TestData(Base):
    ...
    scenario_id = Column(String(36), ForeignKey("ui_scenarios.id"), nullable=True, index=True)
    # nullable=True 保持向后兼容，旧数据不受影响
```

一个场景通过 `scenario_id` 直接关联一个 TestData（主要绑定路径）。DataBinding 表保留不变，作为用例级 override（可选）。

### 1.2 关联规则

- **默认**：场景下所有用例使用场景的 TestData（通过 `scenario_id`）
- **Override**：如果某个用例在 DataBinding 表中有绑定，优先使用自己的 TestData
- **无数据**：如果场景没有 TestData 且用例也没有 DataBinding，N=1，等同于当前行为

## 2. 录制行为变更

### 2.1 去掉自动变体生成

`DataExtractor.generate_test_data()` 不再生成变体数据行：

```
当前: data_sets = [base_row, variant1, variant2, ...]
改为: data_sets = [base_row]  # 只保留录制时的实际值
```

### 2.2 提取规则不变

- Input 操作：识别输入值 → 变量名从元素属性/文本/选择器推断
- Navigate 操作：提取 URL 参数
- Select 操作：捕获选中值
- `_is_variable_data()` / `_guess_field_name()` 逻辑保持不变

### 2.3 保存时关联场景

`save-scenario` API 保存 TestData 时同时写入 `scenario_id`，在场景前后端之间建立直接关联。

## 3. 执行引擎改动

### 3.1 数据行迭代

`TaskOrchestrator._orchestrate_scenario_execution()` 新增迭代循环：

```python
# 1. 查询 TestData
test_data = db.query(TestData).filter(
    TestData.scenario_id == scenario.id
).first()

data_rows = test_data.data if test_data else []
max_iterations = max(len(data_rows), 1)

# 2. 按行迭代
for data_row_index in range(max_iterations):
    scenario_execution = create_scenario_execution(
        iteration=data_row_index,
        data_row=data_rows[data_row_index] if data_row_index < len(data_rows) else {}
    )
    
    for case in cases:
        # 3. 解析用例的 TestData（优先 DataBinding）
        case_data = resolve_case_data(case, scenario, data_row_index)
        execute_case(case, case_data)
    
    # 4. 某行失败则停止（fail-fast）
    if scenario_execution.status == "failed":
        break
```

### 3.2 变量解析

`VariableResolver` 已支持 `data_row_index`，只需传入正确的 index（不再硬编码 0）：

```python
# step_executor.py: 移除 data_row_index=0
resolved_params = variable_resolver.resolve_step_parameters(
    step, case, data_row_index=current_data_row_index
)
```

### 3.3 ScenarioExecution 新增字段

```python
iteration: int = 0       # 第几轮迭代
data_row_index: int = 0  # 使用的数据行索引
data_row: JSON = {}      # 当前行数据快照（用于报告展示）
```

## 4. 前端改动

### 4.1 测试数据管理 — 表格编辑

废弃 JSON 编辑器，改为表格视图。API 返回的数据 (`data: [{...}, {...}]`) 按二维表渲染：

```
┌────────┬──────────┬──────────┬──────────┬──────────┐
│        │ username │ password │ item     │ qty      │
├────────┼──────────┼──────────┼──────────┼──────────┤
│ 第1行  │ admin    │ 123456   │ 笔记本   │ 5        │
│ 第2行  │ testuser │ abc123   │ 鼠标     │ 10       │
└────────┴──────────┴──────────┴──────────┴──────────┘

[+ 添加行] [编辑列头] [删除选中行]
```

- 每列 = 一个变量名（列头只读，从步骤中的 `${变量名}` 引用自动提取）
- 每行 = 一组测试数据
- 支持添加/删除行、编辑单元格值
- 支持添加/删除列（添加列 = 新增变量名；删除列 = 移除 TestData 中该字段）
- 添加行时默认复制上一行的值，降低填写成本

### 4.2 场景详情页

新增"测试数据"标签页，展示该场景关联的 TestData，提供入口直接编辑。

### 4.3 执行报告

- 按迭代轮次分组展示：迭代 1 → 迭代 2 → 迭代 3
- 每轮显示使用的数据行（表格快照）
- 每轮显示该轮各用例的执行结果

## 5. 向后兼容

- 没有 TestData 的场景：N=1，行为不变
- 旧的 DataBinding 记录：继续生效，作为用例级 override
- 旧的 TestData 记录（无 scenario_id）：用户编辑保存后自动关联
- API 返回格式不变：`TestData.data` 仍然是 JSON 数组，前端表格只是渲染方式的变化

## 6. 不做的

- 不自动生成断言数据
- 不支持跨场景共享 TestData（每场景独立）
- 不自动生成变体数据
- 不在取消/失败时保存中间结果

## 7. 修改文件清单

| 文件 | 改动 |
|------|------|
| `backend/app/models/test_data.py` | TestData 新增 `scenario_id` 字段 |
| `backend/app/services/recording/data_extractor.py` | `generate_test_data()` 去掉变体生成 |
| `backend/app/api/recording.py` | save-scenario 写入 scenario_id |
| `backend/app/services/execution/task_orchestrator.py` | 新增数据行迭代循环 |
| `backend/app/services/execution/step_executor.py` | 传入正确的 data_row_index |
| `backend/app/models/execution.py` | ScenarioExecution 新增 iteration/data_row_index/data_row |
| `frontend/src/pages/TestData.tsx` | 表格编辑视图替代 JSON 编辑器 |
| `frontend/src/pages/Scenarios.tsx` | 场景详情新增测试数据入口 |
| `frontend/src/pages/ExecutionReport.tsx` | 按迭代轮次展示 |
