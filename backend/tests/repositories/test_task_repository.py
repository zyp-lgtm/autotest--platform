"""
Task Repository 测试

测试任务相关的数据访问
"""
import pytest
import uuid

from app.repositories.task_repository import TaskRepository, ScenarioRepository, CaseRepository, StepRepository
from app.models.ui_task import UITask, UIScenario, UICase, UIStep


class TestTaskRepository:
    """测试 TaskRepository"""

    def test_get_by_project(self, session, test_task):
        """测试获取项目的任务列表"""
        repo = TaskRepository(session)

        tasks = repo.get_by_project(str(test_task.project_id))

        assert len(tasks) >= 1
        assert test_task.id in [t.id for t in tasks]

    def test_get_by_project_with_limit(self, session, test_task):
        """测试限制返回数量"""
        repo = TaskRepository(session)

        # 创建多个任务
        for i in range(5):
            task = UITask(
                name=f"Task {i}",
                description=f"Description {i}",
                task_type="ui",
                project_id=test_task.project_id,
                created_by=test_task.created_by
            )
            session.add(task)
        session.commit()

        tasks = repo.get_by_project(str(test_task.project_id), limit=3)

        assert len(tasks) == 3

    def test_add_scenario(self, session, test_task, test_user):
        """测试向任务添加场景"""
        repo = TaskRepository(session)

        # 创建场景
        scenario = UIScenario(
            name="Test Scenario",
            description="A test scenario",
            scenario_type="functional",
            task_id=test_task.id,
            project_id=test_task.project_id
        )
        session.add(scenario)
        session.commit()

        # 添加到任务
        success = repo.add_scenario(str(test_task.id), str(scenario.id))

        assert success is True

        # 验证
        task = repo.get_by_id(str(test_task.id))
        assert str(scenario.id).replace('-', '') in task.scenario_ids

    def test_remove_scenario(self, session, test_task, test_user):
        """测试从任务移除场景"""
        repo = TaskRepository(session)

        # 创建并添加场景
        scenario = UIScenario(
            name="Test Scenario",
            scenario_type="functional",
            task_id=test_task.id,
            project_id=test_task.project_id
        )
        session.add(scenario)
        session.commit()

        repo.add_scenario(str(test_task.id), str(scenario.id))

        # 移除场景
        success = repo.remove_scenario(str(test_task.id), str(scenario.id))

        assert success is True

        # 验证
        task = repo.get_by_id(str(test_task.id))
        assert str(scenario.id).replace('-', '') not in task.scenario_ids


class TestScenarioRepository:
    """测试 ScenarioRepository"""

    def test_get_by_task(self, session, test_task):
        """测试获取任务的所有场景"""
        repo = ScenarioRepository(session)

        # 创建场景
        for i in range(3):
            scenario = UIScenario(
                name=f"Scenario {i}",
                scenario_type="functional",
                task_id=test_task.id,
                project_id=test_task.project_id,
                execution_order=i
            )
            session.add(scenario)
        session.commit()

        scenarios = repo.get_by_task(str(test_task.id))

        assert len(scenarios) == 3
        assert scenarios[0].execution_order < scenarios[1].execution_order

    def test_add_case(self, session, test_task):
        """测试向场景添加用例"""
        scenario_repo = ScenarioRepository(session)

        # 创建场景
        scenario = UIScenario(
            name="Test Scenario",
            scenario_type="functional",
            task_id=test_task.id,
            project_id=test_task.project_id
        )
        session.add(scenario)
        session.commit()

        # 创建用例
        case = UICase(
            name="Test Case",
            case_type="functional",
            scenario_id=scenario.id,
            project_id=test_task.project_id
        )
        session.add(case)
        session.commit()

        # 添加到场景
        success = scenario_repo.add_case(str(scenario.id), str(case.id))

        assert success is True

        # 验证
        scenario = scenario_repo.get_by_id(str(scenario.id))
        assert str(case.id).replace('-', '') in scenario.case_ids

    def test_get_next_execution_order(self, session, test_task):
        """测试获取下一个执行顺序号"""
        repo = ScenarioRepository(session)

        # 创建 3 个场景
        for i in range(3):
            scenario = UIScenario(
                name=f"Scenario {i}",
                scenario_type="functional",
                task_id=test_task.id,
                project_id=test_task.project_id,
                execution_order=i
            )
            session.add(scenario)
        session.commit()

        next_order = repo.get_next_execution_order(str(test_task.id))

        assert next_order == 3


class TestCaseRepository:
    """测试 CaseRepository"""

    def test_get_by_scenario(self, session, test_task):
        """测试获取场景的所有用例"""
        repo = CaseRepository(session)

        # 创建场景
        scenario = UIScenario(
            name="Test Scenario",
            scenario_type="functional",
            task_id=test_task.id,
            project_id=test_task.project_id
        )
        session.add(scenario)
        session.commit()

        # 创建用例
        for i in range(2):
            case = UICase(
                name=f"Case {i}",
                case_type="functional",
                scenario_id=scenario.id,
                project_id=test_task.project_id
            )
            session.add(case)
        session.commit()

        cases = repo.get_by_scenario(str(scenario.id))

        assert len(cases) == 2

    def test_add_step(self, session, test_task, test_keyword):
        """测试向用例添加步骤"""
        case_repo = CaseRepository(session)

        # 创建场景和用例
        scenario = UIScenario(
            name="Test Scenario",
            scenario_type="functional",
            task_id=test_task.id,
            project_id=test_task.project_id
        )
        session.add(scenario)
        session.commit()

        case = UICase(
            name="Test Case",
            case_type="functional",
            scenario_id=scenario.id,
            project_id=test_task.project_id
        )
        session.add(case)
        session.commit()

        # 创建步骤
        step = UIStep(
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=test_task.id,
            keyword_id=test_keyword.id,
            step_name="Click button",
            step_order=0,
            step_type=test_keyword.category
        )
        session.add(step)
        session.commit()

        # 添加到用例
        success = case_repo.add_step(str(case.id), str(step.id))

        assert success is True


class TestStepRepository:
    """测试 StepRepository"""

    def test_get_by_case(self, session, test_task, test_keyword):
        """测试获取用例的所有步骤"""
        repo = StepRepository(session)

        # 创建场景和用例
        scenario = UIScenario(
            name="Test Scenario",
            scenario_type="functional",
            task_id=test_task.id,
            project_id=test_task.project_id
        )
        session.add(scenario)
        session.commit()

        case = UICase(
            name="Test Case",
            case_type="functional",
            scenario_id=scenario.id,
            project_id=test_task.project_id
        )
        session.add(case)
        session.commit()

        # 创建步骤
        for i in range(3):
            step = UIStep(
                case_id=case.id,
                scenario_id=scenario.id,
                task_id=test_task.id,
                keyword_id=test_keyword.id,
                step_name=f"Step {i}",
                step_order=i,
                step_type=test_keyword.category
            )
            session.add(step)
        session.commit()

        steps = repo.get_by_case(str(case.id))

        assert len(steps) == 3
        assert steps[0].step_order < steps[1].step_order

    def test_get_next_step_order(self, session, test_task, test_keyword):
        """测试获取下一个步骤顺序号"""
        repo = StepRepository(session)

        # 创建场景和用例
        scenario = UIScenario(
            name="Test Scenario",
            scenario_type="functional",
            task_id=test_task.id,
            project_id=test_task.project_id
        )
        session.add(scenario)
        session.commit()

        case = UICase(
            name="Test Case",
            case_type="functional",
            scenario_id=scenario.id,
            project_id=test_task.project_id
        )
        session.add(case)
        session.commit()

        # 创建 2 个步骤
        for i in range(2):
            step = UIStep(
                case_id=case.id,
                scenario_id=scenario.id,
                task_id=test_task.id,
                keyword_id=test_keyword.id,
                step_name=f"Step {i}",
                step_order=i,
                step_type=test_keyword.category
            )
            session.add(step)
        session.commit()

        next_order = repo.get_next_step_order(str(case.id))

        assert next_order == 2
