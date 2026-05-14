"""
VariableResolver 集成测试
"""
import uuid
from unittest.mock import MagicMock
from app.services.variable_resolver import VariableResolver
from app.models.ui_task import UICase
from app.models.test_data import TestData


class TestScenarioLevelDataLookup:
    def test_falls_back_to_scenario_data_when_no_case_binding(self):
        """用例无 DataBinding 时，应从场景级 TestData 解析变量"""
        scenario_id = uuid.uuid4()
        case_id = uuid.uuid4()

        case = UICase(
            id=case_id,
            scenario_id=scenario_id,
            project_id=uuid.uuid4(),
            name="主流程",
            case_type="ui"
        )

        test_data = TestData(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            scenario_id=scenario_id,
            name="场景测试数据",
            data=[{"username": "scene_user", "password": "scene_pass"}]
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
        case_binding_data_id = uuid.uuid4()

        case = UICase(
            id=case_id,
            scenario_id=scenario_id,
            project_id=uuid.uuid4(),
            name="主流程",
            case_type="ui"
        )

        # Mock DataBinding
        mock_binding = MagicMock()
        mock_binding.data_id = case_binding_data_id

        case_data = TestData(
            id=case_binding_data_id,
            project_id=uuid.uuid4(),
            scenario_id=None,
            name="用例级数据",
            data=[{"username": "case_user"}]
        )

        mock_db = MagicMock()
        # DataBinding 查询返回有绑定
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_binding]
        # TestData 查询返回用例级数据
        mock_db.query.return_value.filter.return_value.first.return_value = case_data

        resolver = VariableResolver(mock_db)
        variables = resolver.resolve_case_variables(case, data_row_index=0)

        assert variables["username"] == "case_user"
