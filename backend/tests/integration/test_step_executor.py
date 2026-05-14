import uuid
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from app.services.execution.step_executor import StepExecutor


class TestStepExecutorDataRow:
    @pytest.mark.asyncio
    async def test_execute_step_passes_data_row_index(self):
        """StepExecutor 应将 data_row_index 传递给 VariableResolver"""
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
