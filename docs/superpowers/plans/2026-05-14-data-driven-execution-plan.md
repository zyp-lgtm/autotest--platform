# 数据驱动执行 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现"录制提取原始测试数据 + 按数据行迭代执行场景"，支持 N 行数据 = N 次场景执行。

**Architecture:** TestData 新增 scenario_id 实现场景级关联，DataBinding 保留作用例级 override；TaskOrchestrator 在场景执行层加迭代循环，StepExecutor 传入正确的 data_row_index；VariableResolver 优先查 DataBinding 再 fallback 到场景级 TestData。

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Pytest, React + TypeScript

**Spec:** `docs/superpowers/specs/2026-05-14-data-driven-execution-design.md`

---

### Task 1: TestData 模型 — 新增 scenario_id

**Files:**
- Modify: `backend/app/models/test_data.py`

- [ ] **Step 1: 添加 scenario_id 字段**

```python
# app/models/test_data.py — TestData 类中新增
scenario_id = Column(
    String(36), ForeignKey("ui_scenarios.id"),
    nullable=True, index=True
)
```

在 import 区域无其他改动。字段 nullable=True 保证向后兼容。

- [ ] **Step 2: 验证模型加载**

```bash
cd backend && python3 -c "from app.models.test_data import TestData; print('scenario_id' in TestData.__table__.columns)"
```
Expected: `True`

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/test_data.py
git commit -m "feat: TestData 新增 scenario_id 字段"
```

---

### Task 2: ScenarioExecution 模型 — 新增迭代字段

**Files:**
- Modify: `backend/app/models/execution.py`

- [ ] **Step 1: 添加三个新字段**

```python
# app/models/execution.py — ScenarioExecution 类中新增
iteration = Column(Integer, default=0)         # 第几轮迭代
data_row_index = Column(Integer, default=0)    # 使用的数据行索引
data_row = Column(JSON, default={})            # 当前行数据快照
```

加在 `execution_order` 字段之后。

- [ ] **Step 2: 验证**

```bash
cd backend && python3 -c "from app.models.execution import ScenarioExecution; cols = ScenarioExecution.__table__.columns; print(all(k in cols for k in ['iteration','data_row_index','data_row']))"
```
Expected: `True`

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/execution.py
git commit -m "feat: ScenarioExecution 新增迭代字段"
```

---

### Task 3: DataExtractor — 去掉变体生成

**Files:**
- Modify: `backend/app/services/recording/data_extractor.py`
- Test: `tests/integration/test_data_extractor.py` (新建)

- [ ] **Step 1: 写失败的测试**

```python
# tests/integration/test_data_extractor.py
import uuid
from app.services.recording.data_extractor import DataExtractor
from app.services.recorder import CapturedAction


class TestGenerateTestData:
    def test_generates_single_base_row_only(self):
        """generate_test_data 只应生成 1 行基准数据，不生成变体"""
        extractor = DataExtractor()
        from app.services.recording.data_extractor import DataPattern
        patterns = [
            DataPattern(
                id=str(uuid.uuid4()),
                field_name="username",
                pattern_type="input",
                values=["admin"],
                confidence=0.9,
                selected=True,
                suggested_variations=["admin_test", "", "a" * 20]
            ),
            DataPattern(
                id=str(uuid.uuid4()),
                field_name="password",
                pattern_type="input",
                values=["123456"],
                confidence=0.9,
                selected=True,
                suggested_variations=["123456_test", ""]
            ),
        ]

        result = extractor.generate_test_data(patterns, "测试场景", str(uuid.uuid4()))

        assert result["name"] == "测试场景_测试数据"
        assert result["data_type"] == "json"
        assert len(result["data"]) == 1, f"应只有 1 行基准数据，实际 {len(result['data'])} 行"
        assert result["data"][0] == {"username": "admin", "password": "123456"}
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python3 -m pytest tests/integration/test_data_extractor.py::TestGenerateTestData -x -p no:cacheprovider -o "addopts=" -v
```
Expected: FAIL, 实际行数 > 1

- [ ] **Step 3: 修改 generate_test_data 去掉变体生成**

```python
# app/services/recording/data_extractor.py — generate_test_data() 方法
def generate_test_data(self, patterns, scenario_name, project_id):
    selected_patterns = [p for p in patterns if p.selected]
    if not selected_patterns:
        return {}

    # 只生成基准行，不生成变体
    base_row = {}
    for pattern in selected_patterns:
        if pattern.values:
            base_row[pattern.field_name] = pattern.values[0]

    data_sets = [base_row]  # 只有一行，不生成变体

    return {
        "name": f"{scenario_name}_测试数据",
        "description": "从录制中自动提取",
        "data_type": "json",
        "data": data_sets,
        "tags": ["auto-generated", "recorded"],
        "project_id": project_id
    }
```

删除原有变体生成循环（`for pattern in selected_patterns[:3]` … `variant_row` … 整段）。

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend && python3 -m pytest tests/integration/test_data_extractor.py -x -p no:cacheprovider -o "addopts=" -v
```
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/recording/data_extractor.py tests/integration/test_data_extractor.py
git commit -m "feat: recording 只生成单行基准数据，去掉自动变体"
```

---

### Task 4: Recording API — 保存时写入 scenario_id

**Files:**
- Modify: `backend/app/api/recording.py`

- [ ] **Step 1: 修改 save-scenario 中 TestData 创建逻辑**

在 `backend/app/api/recording.py` 的 `save_scenario` 函数中，找到 TestData 创建代码（约 line 348-361）。在 TestData 构造函数中添加 `scenario_id`：

```python
# 在 db.add(test_data_record) 之前，已经有 scenario 对象（在 db.flush() 后）
# 修改 TestData 创建部分:
test_data_record = TestData(
    project_id=project_id_uuid,
    scenario_id=scenario.id,  # 新增：关联场景
    name=request.test_data.get("name", f"{request.scenario_name}_测试数据"),
    description=request.test_data.get("description", "从录制自动生成"),
    data_type="json",
    data=request.test_data.get("data", []),
    tags=request.test_data.get("tags", ["recording", "auto-generated"]),
    created_by=user.id
)
```

注意：`scenario` 对象需在 `db.add(scenario)` 和 `db.flush()` 之后创建，确保 `scenario.id` 可用。检查现有代码顺序确保 TestData 创建在 scenario flush 之后。

- [ ] **Step 2: 验证**

```bash
cd backend && python3 -c "from app.api.recording import router; print('Import OK')"
```
Expected: `Import OK`

- [ ] **Step 3: 提交**

```bash
git add backend/app/api/recording.py
git commit -m "feat: save-scenario 写入 TestData.scenario_id"
```

---

### Task 5: VariableResolver — 支持场景级数据查找

**Files:**
- Modify: `backend/app/services/variable_resolver.py`
- Test: `tests/integration/test_variable_resolver.py` (新建)

- [ ] **Step 1: 写失败的测试**

```python
# tests/integration/test_variable_resolver.py
import uuid
from unittest.mock import MagicMock, patch
from app.services.variable_resolver import VariableResolver
from app.models.ui_task import UICase
from app.models.test_data import TestData, DataBinding


class TestScenarioLevelDataLookup:
    def test_falls_back_to_scenario_data_when_no_case_binding(self):
        """用例无 DataBinding 时，应从场景级 TestData 解析变量"""
        scenario_id = uuid.uuid4()
        case_id = uuid.uuid4()
        data_id = uuid.uuid4()

        case = UICase(
            id=case_id,
            scenario_id=scenario_id,
            project_id=uuid.uuid4(),
            name="主流程",
            case_type="ui"
        )

        test_data = TestData(
            id=data_id,
            project_id=uuid.uuid4(),
            scenario_id=scenario_id,
            name="场景测试数据",
            data=[
                {"username": "scene_user", "password": "scene_pass"}
            ]
        )

        mock_db = MagicMock()
        # DataBinding 查询返回空（无用例级绑定）
        mock_db.query.return_value.filter.return_value.all.return_value = []
        # TestData 查询返回场景级数据
        mock_db.query.return_value.filter.return_value.first.return_value = test_data

        resolver = VariableResolver(mock_db)
        variables = resolver.resolve_case_variables(case, data_row_index=0)

        assert variables == {"username": "scene_user", "password": "scene_pass"}

    def test_case_binding_overrides_scenario_data(self):
        """用例有 DataBinding 时，优先使用用例级绑定"""
        scenario_id = uuid.uuid4()
        case_id = uuid.uuid4()

        case = UICase(
            id=case_id,
            scenario_id=scenario_id,
            project_id=uuid.uuid4(),
            name="主流程",
            case_type="ui"
        )

        case_binding = MagicMock()
        case_binding.data_id = uuid.uuid4()

        case_data = TestData(
            id=case_binding.data_id,
            project_id=uuid.uuid4(),
            scenario_id=None,
            name="用例级数据",
            data=[{"username": "case_user"}]
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [case_binding]
        mock_db.query.return_value.filter.return_value.first.return_value = case_data

        resolver = VariableResolver(mock_db)
        variables = resolver.resolve_case_variables(case, data_row_index=0)

        assert variables["username"] == "case_user"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python3 -m pytest tests/integration/test_variable_resolver.py -x -p no:cacheprovider -o "addopts=" -v
```
Expected: FAIL — 无 DataBinding 的用例返回空 variables

- [ ] **Step 3: 修改 resolve_case_variables 添加场景级 fallback**

```python
# app/services/variable_resolver.py — resolve_case_variables() 方法
def resolve_case_variables(self, case, data_row_index=0):
    variables = {}
    try:
        bindings = self.db.query(DataBinding).filter(
            DataBinding.case_id == case.id,
            DataBinding.enabled == 1
        ).all()

        if bindings:
            # 用例级绑定（override）
            for binding in bindings:
                test_data = self.db.query(TestData).filter(
                    TestData.id == binding.data_id
                ).first()
                if test_data:
                    data_rows = test_data.data or []
                    if data_rows:
                        idx = min(data_row_index, len(data_rows) - 1)
                        row = data_rows[idx]
                        if isinstance(row, dict):
                            variables.update(row)
        else:
            # 场景级 fallback
            test_data = self.db.query(TestData).filter(
                TestData.scenario_id == case.scenario_id
            ).first()
            if test_data:
                data_rows = test_data.data or []
                if data_rows:
                    idx = min(data_row_index, len(data_rows) - 1)
                    row = data_rows[idx]
                    if isinstance(row, dict):
                        variables.update(row)
    except Exception as e:
        logger.error(f"解析变量失败: {e}", exc_info=True)

    return variables
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend && python3 -m pytest tests/integration/test_variable_resolver.py -x -p no:cacheprovider -o "addopts=" -v
```
Expected: 2 PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/variable_resolver.py tests/integration/test_variable_resolver.py
git commit -m "feat: VariableResolver 支持场景级 TestData fallback"
```

---

### Task 6: StepExecutor — 接受并传递 data_row_index

**Files:**
- Modify: `backend/app/services/execution/step_executor.py`
- Modify: `backend/app/core/interfaces.py` (IStepExecutor 接口)
- Test: `tests/integration/test_step_executor.py` (追加)

- [ ] **Step 1: 修改 execute_step 签名**

```python
# step_executor.py — execute_step() 签名新增 data_row_index 参数
async def execute_step(
    self,
    step: UIStep,
    case_execution,
    scenario_execution,
    task_execution,
    case: Optional[UICase] = None,
    data_row_index: int = 0  # 新增
) -> StepExecution:
```

- [ ] **Step 2: 修改 VariableResolver 调用处的硬编码**

```python
# step_executor.py line ~91, 将 data_row_index=0 改为使用参数值
parameters = resolver.resolve_step_parameters(
    step_parameters=parameters,
    case=case,
    data_row_index=data_row_index  # 不再硬编码 0
)
```

- [ ] **Step 3: 更新 IStepExecutor 接口**

```python
# app/core/interfaces.py — IStepExecutor 的 execute_step 签名
async def execute_step(
    self,
    step,
    case_execution,
    scenario_execution,
    task_execution,
    case=None,
    data_row_index: int = 0  # 新增
) -> Any:
    ...
```

- [ ] **Step 4: 写测试验证**

```python
# tests/integration/test_step_executor.py (追加)
class TestStepExecutorDataRow:
    @pytest.mark.asyncio
    async def test_execute_step_passes_data_row_index(self):
        """StepExecutor 应将 data_row_index 传递给 VariableResolver"""
        from unittest.mock import MagicMock, AsyncMock, patch
        from app.services.execution.step_executor import StepExecutor

        mock_db = MagicMock()
        mock_engine = MagicMock()
        mock_engine.execute = AsyncMock(return_value={"success": True, "data": {}})
        mock_browser = MagicMock()
        mock_browser.get_page = AsyncMock()
        mock_debug = MagicMock()

        executor = StepExecutor(mock_db, mock_engine, mock_browser, mock_debug)

        step = MagicMock()
        step.keyword_id = uuid.uuid4()
        step.parameters = {"text": "${greeting}"}
        step.step_name = "test"
        step.step_order = 1
        step.continue_on_failure = False

        case = MagicMock()
        case.id = uuid.uuid4()
        case.scenario_id = uuid.uuid4()

        case_exec = MagicMock()
        case_exec.id = uuid.uuid4()
        scenario_exec = MagicMock()
        scenario_exec.id = uuid.uuid4()
        task_exec = MagicMock()
        task_exec.id = uuid.uuid4()

        with patch("app.services.execution.step_executor.VariableResolver") as MockVR:
            mock_resolver = MagicMock()
            mock_resolver.resolve_step_parameters.return_value = {"text": "hello"}
            MockVR.return_value = mock_resolver

            await executor.execute_step(
                step, case_exec, scenario_exec, task_exec, case=case,
                data_row_index=2
            )

            mock_resolver.resolve_step_parameters.assert_called_once_with(
                step_parameters={"text": "${greeting}"},
                case=case,
                data_row_index=2
            )
```

- [ ] **Step 5: 运行测试**

```bash
cd backend && python3 -m pytest tests/integration/test_step_executor.py::TestStepExecutorDataRow -x -p no:cacheprovider -o "addopts=" -v
```
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/services/execution/step_executor.py backend/app/core/interfaces.py tests/integration/test_step_executor.py
git commit -m "feat: StepExecutor 接受并传递 data_row_index"
```

---

### Task 7: TaskOrchestrator — 场景级数据迭代循环

**Files:**
- Modify: `backend/app/services/execution/task_orchestrator.py`
- Test: `tests/integration/test_orchestrator_data_iteration.py` (新建)

- [ ] **Step 1: 写失败的测试**

```python
# tests/integration/test_orchestrator_data_iteration.py
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from app.services.execution.task_orchestrator import TaskOrchestrator
from app.models.ui_task import UITask, UIScenario, UICase, UIStep
from app.models.execution import TestExecution, ScenarioExecution
from app.models.test_data import TestData


class TestDataIteration:
    @pytest.mark.asyncio
    async def test_iterates_for_each_data_row(self):
        """场景有 3 行测试数据时应创建 3 个 ScenarioExecution"""
        task_id = uuid.uuid4()
        scenario_id = uuid.uuid4()
        project_id = uuid.uuid4()

        task = UITask(
            id=task_id, project_id=project_id, name="test",
            task_type="ui", scenario_ids=[scenario_id], execution_config={}, tags=[]
        )
        scenario = UIScenario(
            id=scenario_id, task_id=task_id, project_id=project_id,
            name="test scenario", scenario_type="ui",
            case_ids=[uuid.uuid4()], execution_order=0
        )
        case = UICase(
            id=scenario.case_ids[0], scenario_id=scenario_id,
            project_id=project_id, name="main", case_type="ui",
            step_ids=[], priority="medium"
        )
        step = UIStep(
            id=uuid.uuid4(), case_id=case.id, keyword_id=uuid.uuid4(),
            step_name="step1", step_order=0, parameters={"text": "${x}"},
            continue_on_failure=False
        )
        case.step_ids = [step.id]

        test_data = TestData(
            id=uuid.uuid4(), project_id=project_id, scenario_id=scenario_id,
            name="test data",
            data=[
                {"x": "a"},  # 第0行
                {"x": "b"},  # 第1行
                {"x": "c"},  # 第2行
            ]
        )

        execution = TestExecution(
            id=uuid.uuid4(), task_id=task_id, project_id=project_id,
            status="running"
        )

        mock_db = MagicMock()
        # 模拟 _load_scenarios
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [scenario]
        # 模拟 TestData 查询
        mock_db.query.return_value.filter.return_value.first.return_value = test_data
        # 模拟 _load_cases
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [scenario],  # _load_scenarios
            test_data,   # TestData 查询
            [case],      # _load_cases
            [step],      # _load_steps (x3)
            [step],
            [step],
        ]

        mock_executor = MagicMock()
        mock_executor.execute_step = AsyncMock(return_value=MagicMock(
            status="passed"
        ))

        with patch("app.services.execution.task_orchestrator.uuid.uuid4", return_value=uuid.uuid4()):
            with patch("app.services.execution.task_orchestrator.datetime"):
                orchestrator = TaskOrchestrator(mock_db, mock_executor)
                result = await orchestrator.orchestrate_task_execution(
                    task, execution, {"use_agent": False}
                )

        # 验证创建了 3 个 ScenarioExecution
        add_calls = [
            c for c in mock_db.add.call_args_list
            if isinstance(c[0][0], ScenarioExecution)
        ]
        assert len(add_calls) == 3, f"应有 3 个 ScenarioExecution, 实际 {len(add_calls)}"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python3 -m pytest tests/integration/test_orchestrator_data_iteration.py -x -p no:cacheprovider -o "addopts=" -v
```
Expected: FAIL — 只创建 1 个 ScenarioExecution

- [ ] **Step 3: 修改 _orchestrate_scenario_execution 添加迭代循环**

```python
# task_orchestrator.py — _orchestrate_scenario_execution() 方法
async def _orchestrate_scenario_execution(
    self, scenario, task_execution, execution_order
) -> ScenarioExecution:
    import uuid

    # 查询场景级测试数据
    from ...models.test_data import TestData
    test_data = self.db.query(TestData).filter(
        TestData.scenario_id == scenario.id
    ).first()

    data_rows = test_data.data if test_data and test_data.data else []
    max_iterations = max(len(data_rows), 1)

    last_scenario_execution = None

    for data_row_index in range(max_iterations):
        data_row = data_rows[data_row_index] if data_row_index < len(data_rows) else {}

        scenario_execution = ScenarioExecution(
            id=uuid.uuid4(),
            test_execution_id=task_execution.id,
            scenario_id=scenario.id,
            status="pending",
            execution_order=execution_order,
            iteration=data_row_index,
            data_row_index=data_row_index,
            data_row=data_row,
            total_cases=0, total_steps=0, passed_steps=0, failed_steps=0
        )
        self.db.add(scenario_execution)
        self.db.commit()
        last_scenario_execution = scenario_execution

        try:
            cases = self._load_cases(scenario)
            for case in cases:
                case_execution = await self._orchestrate_case_execution(
                    case, scenario_execution, task_execution, data_row_index
                )
                self._update_scenario_stats(scenario_execution)
                if case_execution.status == "failed" or case_execution.result == "fail":
                    break

            scenario_execution.status = "completed"
            scenario_execution.result = "pass" if scenario_execution.failed_steps == 0 else "fail"
            self.db.commit()

        except Exception as e:
            logger.error(f"场景执行失败 (迭代 {data_row_index}): {e}")
            scenario_execution.status = "failed"
            scenario_execution.result = "fail"
            scenario_execution.error_message = str(e)
            self.db.commit()
            break  # 某行失败则停止后续迭代

    return last_scenario_execution or scenario_execution
```

- [ ] **Step 4: 修改 _orchestrate_case_execution 签名和调用**

```python
# task_orchestrator.py — _orchestrate_case_execution() 
async def _orchestrate_case_execution(
    self, case, scenario_execution, task_execution,
    data_row_index: int = 0  # 新增参数
) -> CaseExecution:
    ...
    # 在调用 step_executor.execute_step 时传入 data_row_index:
    step_execution = await self.step_executor.execute_step(
        step, case_execution, scenario_execution, task_execution, case,
        data_row_index=data_row_index  # 传入
    )
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd backend && python3 -m pytest tests/integration/test_orchestrator_data_iteration.py -x -p no:cacheprovider -o "addopts=" -v
```
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/services/execution/task_orchestrator.py tests/integration/test_orchestrator_data_iteration.py
git commit -m "feat: TaskOrchestrator 按测试数据行数迭代执行场景"
```

---

### Task 8: 数据库迁移 — 重建表结构

**Files:**
- Run: `backend/init_db.py` (或重新启动应用)

- [ ] **Step 1: 删除旧数据库并重建**

```bash
cd backend && rm -f test_platform.db && python3 init_db.py
```

- [ ] **Step 2: 验证新字段存在**

```bash
cd backend && python3 -c "
import sqlite3
conn = sqlite3.connect('test_platform.db')
cur = conn.cursor()
cur.execute(\"PRAGMA table_info(test_data)\")
cols = [r[1] for r in cur.fetchall()]
print('scenario_id' in cols)
cur.execute(\"PRAGMA table_info(scenario_executions)\")
cols2 = [r[1] for r in cur.fetchall()]
print('iteration' in cols2, 'data_row_index' in cols2, 'data_row' in cols2)
conn.close()
"
```
Expected: `True` `True True True`

- [ ] **Step 3: 提交**

```bash
# 不提交 .db 文件（在 .gitignore 中），只确认变更完成
```

---

### Task 9: 前端 — TestData 表格视图

**Files:**
- Modify: `frontend/src/pages/TestData.tsx`
- Modify: `frontend/src/api/testData.ts` (如有)

- [ ] **Step 1: 实现 TableEditor 组件**

核心逻辑：接收 `data: Record<string, any>[]`，渲染为可编辑表格。

```tsx
// 新增组件或直接在 TestData.tsx 中实现
interface TableEditorProps {
  columns: string[];        // 变量名列头
  rows: Record<string, any>[];
  onRowsChange: (rows: Record<string, any>[]) => void;
  onColumnsChange: (columns: string[]) => void;
}

function TableEditor({ columns, rows, onRowsChange, onColumnsChange }: TableEditorProps) {
  const addRow = () => {
    const lastRow = rows[rows.length - 1] || {};
    const newRow = { ...lastRow };  // 复制上一行
    onRowsChange([...rows, newRow]);
  };

  const deleteRow = (index: number) => {
    onRowsChange(rows.filter((_, i) => i !== index));
  };

  const updateCell = (rowIndex: number, col: string, value: string) => {
    const updated = rows.map((row, i) =>
      i === rowIndex ? { ...row, [col]: value } : row
    );
    onRowsChange(updated);
  };

  const addColumn = () => {
    const name = prompt("新变量名:");
    if (name && !columns.includes(name)) {
      onColumnsChange([...columns, name]);
      // 为所有行添加空值
      onRowsChange(rows.map(row => ({ ...row, [name]: "" })));
    }
  };

  const deleteColumn = (col: string) => {
    if (!confirm(`删除列 "${col}"？`)) return;
    onColumnsChange(columns.filter(c => c !== col));
    onRowsChange(rows.map(({ [col]: _, ...rest }) => rest));
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="border p-2 bg-gray-100 w-20"></th>
            {columns.map(col => (
              <th key={col} className="border p-2 bg-gray-100 group">
                <span>{col}</span>
                <button onClick={() => deleteColumn(col)}
                  className="ml-2 text-red-400 opacity-0 group-hover:opacity-100">×</button>
              </th>
            ))}
            <th className="border p-2 bg-gray-100 w-12">
              <button onClick={addColumn} className="text-blue-600">+列</button>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri}>
              <td className="border p-2 text-gray-500 text-center">第{ri + 1}行</td>
              {columns.map(col => (
                <td key={col} className="border p-0">
                  <input value={row[col] || ""}
                    onChange={e => updateCell(ri, col, e.target.value)}
                    className="w-full p-2 border-0 outline-none focus:bg-blue-50" />
                </td>
              ))}
              <td className="border p-1 text-center">
                <button onClick={() => deleteRow(ri)} className="text-red-400">×</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button onClick={addRow} className="mt-2 px-4 py-2 bg-blue-600 text-white rounded">
        + 添加行
      </button>
    </div>
  );
}
```

- [ ] **Step 2: 集成到 TestData 页面**

在 `TestData.tsx` 中，将 JSON 编辑区替换为 TableEditor。从 API 获取的 `data` 字段传入 `rows`，通过 `Object.keys(data[0] || {})` 提取列头：

```tsx
// 在 TestData 详情/编辑模态框中使用
const dataRows = testData?.data || [];
const columns = dataRows.length > 0
  ? Object.keys(dataRows[0])
  : [];
```

保存时将 `rows` 序列化回 `data: rows` 提交 API。

- [ ] **Step 3: 类型检查**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/pages/TestData.tsx
git commit -m "feat: TestData 表格编辑器替代 JSON 视图"
```

---

### Task 10: 前端 — 场景详情页测试数据入口

**Files:**
- Modify: `frontend/src/pages/Scenarios.tsx`

- [ ] **Step 1: 添加"测试数据"标签页**

在场景详情面板中新增一个 Tab "测试数据"：

```tsx
// 在场景详情视图的 Tab 栏中新增
<Tab label="测试数据">
  <ScenarioTestData scenarioId={selectedScenario.id} />
</Tab>
```

`ScenarioTestData` 组件：根据 `scenario_id` 查询 TestData，如存在则显示 TableEditor，如不存在则显示"暂无测试数据，创建"按钮。

```tsx
function ScenarioTestData({ scenarioId }: { scenarioId: string }) {
  const [testData, setTestData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadTestData(); }, [scenarioId]);

  const loadTestData = async () => {
    // GET /api/v1/test-data/?scenario_id=xxx
    const resp = await testDataApi.list({ scenario_id: scenarioId });
    if (resp.length > 0) setTestData(resp[0]);
    setLoading(false);
  };

  if (loading) return <div>加载中...</div>;
  if (!testData) return (
    <div className="p-4 text-center text-gray-500">
      暂无测试数据
      <Button onClick={createTestData}>+ 创建测试数据</Button>
    </div>
  );

  const columns = testData.data?.[0] ? Object.keys(testData.data[0]) : [];
  return (
    <TableEditor
      columns={columns}
      rows={testData.data || []}
      onRowsChange={async (rows) => {
        await testDataApi.update(testData.id, { data: rows });
      }}
      onColumnsChange={async (cols) => {
        await testDataApi.update(testData.id, { data: testData.data });
      }}
    />
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/Scenarios.tsx
git commit -m "feat: 场景详情新增测试数据编辑入口"
```

---

### Task 11: 前端 — 执行报告按迭代展示

**Files:**
- Modify: `frontend/src/pages/ExecutionReport.tsx`

- [ ] **Step 1: 按迭代分组渲染**

在场景执行结果区域，按 `iteration` 分组展示：

```tsx
// 按 iteration 分组 scenarioExecutions
const groupedByIteration = scenarioExecutions.reduce((acc, se) => {
  const iter = se.iteration ?? 0;
  if (!acc[iter]) acc[iter] = [];
  acc[iter].push(se);
  return acc;
}, {} as Record<number, typeof scenarioExecutions>);

return (
  <div>
    {Object.entries(groupedByIteration).map(([iter, executions]) => (
      <Card key={iter} className="p-4 mb-4">
        <h3 className="font-bold mb-2">
          迭代 {Number(iter) + 1}
          {executions[0]?.data_row && (
            <span className="text-sm text-gray-500 ml-2">
              数据: {JSON.stringify(executions[0].data_row)}
            </span>
          )}
        </h3>
        {/* 渲染该迭代下的用例执行结果 */}
        {executions.map(se => (
          <ScenarioResult key={se.id} execution={se} />
        ))}
      </Card>
    ))}
  </div>
);
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/ExecutionReport.tsx
git commit -m "feat: 执行报告按数据迭代轮次展示"
```

---

### Task 12: 端到端验证

- [ ] **Step 1: 启动后端和前端**

```bash
# 终端1
cd backend && python3 -m uvicorn app.main:app --reload

# 终端2
cd frontend && npm run dev
```

- [ ] **Step 2: 录制一个场景并验证**

```
1. 打开浏览器访问 http://localhost:3000
2. 登录 demo/demo123
3. 录制一个简单场景（导航 + 输入 + 点击）
4. 保存录制 → 检查保存后的场景
5. 打开场景详情 → 查看"测试数据"标签页
6. 确认只有 1 行数据（录制时的原始值）
7. 手动添加第 2 行数据
```

- [ ] **Step 3: 执行并验证迭代**

```
1. 执行该任务
2. 查看执行报告
3. 确认有 2 个迭代轮次
4. 确认每轮使用了不同的数据行
```

- [ ] **Step 4: 验证向后兼容（无测试数据的场景）**

```
1. 创建一个不带测试数据的场景
2. 执行
3. 确认正常执行 1 次
```
