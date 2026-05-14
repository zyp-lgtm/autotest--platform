"""
TaskOrchestrator 数据驱动执行集成测试

验证场景级数据迭代循环：场景绑定 TestData 多行数据时，应迭代执行多次。
"""
import uuid
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone
import pytest
from app.services.execution.task_orchestrator import TaskOrchestrator
from app.models.ui_task import UITask, UIScenario, UICase, UIStep
from app.models.execution import TestExecution, ScenarioExecution
from app.models.test_data import TestData


class TestDataIteration:
    """场景级数据迭代测试"""

    @pytest.mark.asyncio
    async def test_iterates_for_each_data_row(self):
        """场景有3行测试数据时应创建3个ScenarioExecution"""
        task_id = uuid.uuid4()
        scenario_id = uuid.uuid4()
        project_id = uuid.uuid4()
        case_id = uuid.uuid4()
        step_id = uuid.uuid4()

        task = UITask(
            id=task_id, project_id=project_id, name="test",
            task_type="ui", scenario_ids=[scenario_id], execution_config={}, tags=[]
        )
        scenario = UIScenario(
            id=scenario_id, task_id=task_id, project_id=project_id,
            name="test scenario", scenario_type="ui",
            case_ids=[case_id], execution_order=0
        )
        case = UICase(
            id=case_id, scenario_id=scenario_id,
            project_id=project_id, name="main", case_type="ui",
            step_ids=[step_id], priority="medium"
        )
        step = UIStep(
            id=step_id, case_id=case_id,
            step_name="test step", step_type="navigation",
            keyword_id=uuid.uuid4(), step_order=0,
            scenario_id=scenario_id, task_id=task_id,
            parameters={}, continue_on_failure=False
        )

        test_data = TestData(
            id=uuid.uuid4(), project_id=project_id, scenario_id=str(scenario_id),
            name="test data", data_type="json",
            data=[{"x": "a"}, {"x": "b"}, {"x": "c"}]
        )

        execution = TestExecution(
            id=uuid.uuid4(), task_id=task_id, project_id=project_id,
            status="running", started_at=datetime.now(timezone.utc)
        )

        mock_db = MagicMock()
        # Set up TestData query to return test_data via .first()
        testdata_filter_mock = MagicMock()
        testdata_query_mock = MagicMock()
        testdata_query_mock.filter.return_value = testdata_filter_mock
        testdata_filter_mock.first.return_value = test_data
        mock_db.query.return_value = testdata_query_mock

        mock_step_execution = MagicMock(status="passed", result="pass")
        mock_executor = MagicMock()
        mock_executor.execute_step = AsyncMock(return_value=mock_step_execution)

        orchestrator = TaskOrchestrator(mock_db, mock_executor)

        # Mock internal helper methods to isolate the data iteration logic
        orchestrator._load_scenarios = MagicMock(return_value=[scenario])
        orchestrator._load_cases = MagicMock(return_value=[case])
        orchestrator._load_steps = MagicMock(return_value=[step])
        orchestrator._update_execution_stats = MagicMock()
        orchestrator._update_scenario_stats = MagicMock()
        orchestrator._is_cancelled = MagicMock(return_value=False)

        await orchestrator.orchestrate_task_execution(task, execution, {"use_agent": False})

        # Verify 3 ScenarioExecution objects were added (one per data row)
        scenario_adds = [
            call for call in mock_db.add.call_args_list
            if isinstance(call[0][0], ScenarioExecution)
        ]
        assert len(scenario_adds) == 3, (
            f"应有3个ScenarioExecution（3行数据），实际{len(scenario_adds)}"
        )

        # Verify each ScenarioExecution has correct iteration metadata
        expected_rows = [{"x": "a"}, {"x": "b"}, {"x": "c"}]
        for i, call in enumerate(scenario_adds):
            se = call[0][0]
            assert se.data_row_index == i, (
                f"迭代{i}: data_row_index应为{i}，实际{se.data_row_index}"
            )
            assert se.data_row == expected_rows[i], (
                f"迭代{i}: data_row应为{expected_rows[i]}，实际{se.data_row}"
            )
            assert se.iteration == i, (
                f"迭代{i}: iteration应为{i}，实际{se.iteration}"
            )

        # Verify step_executor.execute_step was called once per iteration
        # (one case with one step per iteration = 3 total calls)
        execute_calls = mock_executor.execute_step.call_args_list
        assert len(execute_calls) == 3, (
            f"应有3次execute_step调用（每次迭代1个步骤），实际{len(execute_calls)}"
        )
        for i, call in enumerate(execute_calls):
            assert call.kwargs["data_row_index"] == i, (
                f"execute_step调用{i}: data_row_index应为{i}，"
                f"实际{call.kwargs.get('data_row_index')}"
            )

    @pytest.mark.asyncio
    async def test_no_test_data_executes_once(self):
        """场景无TestData时应只执行一次（兜底）"""
        task_id = uuid.uuid4()
        scenario_id = uuid.uuid4()
        project_id = uuid.uuid4()
        case_id = uuid.uuid4()
        step_id = uuid.uuid4()

        task = UITask(
            id=task_id, project_id=project_id, name="test",
            task_type="ui", scenario_ids=[scenario_id], execution_config={}, tags=[]
        )
        scenario = UIScenario(
            id=scenario_id, task_id=task_id, project_id=project_id,
            name="test scenario", scenario_type="ui",
            case_ids=[case_id], execution_order=0
        )
        case = UICase(
            id=case_id, scenario_id=scenario_id,
            project_id=project_id, name="main", case_type="ui",
            step_ids=[step_id], priority="medium"
        )
        step = UIStep(
            id=step_id, case_id=case_id,
            step_name="test step", step_type="navigation",
            keyword_id=uuid.uuid4(), step_order=0,
            scenario_id=scenario_id, task_id=task_id,
            parameters={}, continue_on_failure=False
        )

        execution = TestExecution(
            id=uuid.uuid4(), task_id=task_id, project_id=project_id,
            status="running", started_at=datetime.now(timezone.utc)
        )

        mock_db = MagicMock()
        # TestData query returns None (no test data)
        testdata_filter_mock = MagicMock()
        testdata_query_mock = MagicMock()
        testdata_query_mock.filter.return_value = testdata_filter_mock
        testdata_filter_mock.first.return_value = None
        mock_db.query.return_value = testdata_query_mock

        mock_step_execution = MagicMock(status="passed", result="pass")
        mock_executor = MagicMock()
        mock_executor.execute_step = AsyncMock(return_value=mock_step_execution)

        orchestrator = TaskOrchestrator(mock_db, mock_executor)

        orchestrator._load_scenarios = MagicMock(return_value=[scenario])
        orchestrator._load_cases = MagicMock(return_value=[case])
        orchestrator._load_steps = MagicMock(return_value=[step])
        orchestrator._update_execution_stats = MagicMock()
        orchestrator._update_scenario_stats = MagicMock()
        orchestrator._is_cancelled = MagicMock(return_value=False)

        await orchestrator.orchestrate_task_execution(task, execution, {"use_agent": False})

        scenario_adds = [
            call for call in mock_db.add.call_args_list
            if isinstance(call[0][0], ScenarioExecution)
        ]
        assert len(scenario_adds) == 1, (
            f"无TestData时应只有1个ScenarioExecution，实际{len(scenario_adds)}"
        )

        se = scenario_adds[0][0][0]
        assert se.data_row_index == 0
        assert se.data_row == {}
        assert se.iteration == 0

    @pytest.mark.asyncio
    async def test_empty_data_list_executes_once(self):
        """TestData.data为空列表时应只执行一次"""
        task_id = uuid.uuid4()
        scenario_id = uuid.uuid4()
        project_id = uuid.uuid4()
        case_id = uuid.uuid4()
        step_id = uuid.uuid4()

        task = UITask(
            id=task_id, project_id=project_id, name="test",
            task_type="ui", scenario_ids=[scenario_id], execution_config={}, tags=[]
        )
        scenario = UIScenario(
            id=scenario_id, task_id=task_id, project_id=project_id,
            name="test scenario", scenario_type="ui",
            case_ids=[case_id], execution_order=0
        )
        case = UICase(
            id=case_id, scenario_id=scenario_id,
            project_id=project_id, name="main", case_type="ui",
            step_ids=[step_id], priority="medium"
        )
        step = UIStep(
            id=step_id, case_id=case_id,
            step_name="test step", step_type="navigation",
            keyword_id=uuid.uuid4(), step_order=0,
            scenario_id=scenario_id, task_id=task_id,
            parameters={}, continue_on_failure=False
        )

        test_data = TestData(
            id=uuid.uuid4(), project_id=project_id, scenario_id=str(scenario_id),
            name="empty data", data_type="json",
            data=[]  # 空列表
        )

        execution = TestExecution(
            id=uuid.uuid4(), task_id=task_id, project_id=project_id,
            status="running", started_at=datetime.now(timezone.utc)
        )

        mock_db = MagicMock()
        testdata_filter_mock = MagicMock()
        testdata_query_mock = MagicMock()
        testdata_query_mock.filter.return_value = testdata_filter_mock
        testdata_filter_mock.first.return_value = test_data
        mock_db.query.return_value = testdata_query_mock

        mock_step_execution = MagicMock(status="passed", result="pass")
        mock_executor = MagicMock()
        mock_executor.execute_step = AsyncMock(return_value=mock_step_execution)

        orchestrator = TaskOrchestrator(mock_db, mock_executor)

        orchestrator._load_scenarios = MagicMock(return_value=[scenario])
        orchestrator._load_cases = MagicMock(return_value=[case])
        orchestrator._load_steps = MagicMock(return_value=[step])
        orchestrator._update_execution_stats = MagicMock()
        orchestrator._update_scenario_stats = MagicMock()
        orchestrator._is_cancelled = MagicMock(return_value=False)

        await orchestrator.orchestrate_task_execution(task, execution, {"use_agent": False})

        scenario_adds = [
            call for call in mock_db.add.call_args_list
            if isinstance(call[0][0], ScenarioExecution)
        ]
        assert len(scenario_adds) == 1, (
            f"空data列表时应只有1个ScenarioExecution，实际{len(scenario_adds)}"
        )
