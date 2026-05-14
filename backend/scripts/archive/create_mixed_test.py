#!/usr/bin/env python3
"""创建包含成功和失败步骤的测试任务"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario, UICase, UIStep
from app.models.user import User
from app.models.project import Project
from app.models.keyword import Keyword

# 创建会话
db = Session(engine)

try:
    # 获取测试用户
    test_user = db.query(User).filter(User.username == "demo").first()
    if not test_user:
        print("错误: 找不到测试用户 demo")
        sys.exit(1)

    # 获取或创建测试项目
    test_project = db.query(Project).filter(Project.name == "测试项目").first()
    if not test_project:
        print("测试项目不存在，自动创建...")
        test_project = Project(
            id=uuid.uuid4(),
            name="测试项目",
            description="测试自动化平台测试项目",
            owner_id=test_user.id
        )
        db.add(test_project)
        db.commit()
        db.flush()
        print(f"✓ 自动创建测试项目: {test_project.name}")

    # 创建新任务
    task_id = uuid.uuid4()
    task = UITask(
        id=task_id,
        project_id=test_project.id,
        name="混合结果测试（成功+失败）",
        description="测试 Agent 执行模式下的成功和失败步骤报告",
        task_type="ui",
        tags=["测试", "混合结果"]
    )
    db.add(task)
    db.commit()
    print(f"✓ 创建任务: {task.name}")

    # 创建场景
    scenario_id = uuid.uuid4()
    scenario = UIScenario(
        id=scenario_id,
        project_id=test_project.id,
        task_id=task.id,
        name="混合结果场景",
        description="包含成功和失败步骤的测试场景",
        execution_order=1
    )
    db.add(scenario)
    db.flush()  # 立即写入，获取 scenario.id
    print(f"✓ 创建场景: {scenario.name}")

    # 更新任务的 scenario_ids（使用无连字符格式，与 SQLite 存储一致）
    task.scenario_ids = [str(scenario_id).replace('-', '')]
    db.commit()
    print(f"✓ 已更新任务的 scenario_ids")

    # 创建用例
    case_id = uuid.uuid4()
    case = UICase(
        id=case_id,
        project_id=test_project.id,
        scenario_id=scenario.id,
        name="混合结果用例",
        description="测试 Agent 如何处理成功和失败的步骤",
        priority="P1"
    )
    db.add(case)
    db.flush()  # 立即写入数据库，获取 case.id
    print(f"✓ 创建用例: {case.name}")

    # 更新场景的 case_ids（使用无连字符的 UUID 格式，与 SQLite 存储一致）
    scenario.case_ids = [str(case_id).replace('-', '')]
    db.commit()
    print(f"✓ 已更新场景的 case_ids")

    # 获取关键字
    navigate_kw = db.query(Keyword).filter(Keyword.name == "NAVIGATE").first()
    wait_kw = db.query(Keyword).filter(Keyword.name == "WAIT_FOR_ELEMENT").first()
    input_kw = db.query(Keyword).filter(Keyword.name == "INPUT").first()
    click_kw = db.query(Keyword).filter(Keyword.name == "CLICK").first()

    if not all([navigate_kw, wait_kw, input_kw, click_kw]):
        print("错误: 缺少必要的关键字")
        sys.exit(1)

    # 创建步骤（包含成功和失败的）
    step_ids = []  # 记录步骤 ID
    steps = [
        # ✅ 步骤1: 成功 - 导航到百度
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=task.id,
            keyword_id=navigate_kw.id,
            step_name="✅ 步骤1: 打开百度首页（应该成功）",
            step_order=1,
            parameters={"url": "https://www.baidu.com"},
            enabled=True
        ),

        # ✅ 步骤2: 成功 - 等待存在的元素
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=task.id,
            keyword_id=wait_kw.id,
            step_name="✅ 步骤2: 等待搜索框（应该成功）",
            step_order=2,
            parameters={
                "selector": "#kw",
                "state": "attached",  # 使用 attached 而不是 visible，因为元素可能隐藏
                "timeout": 5000
            },
            enabled=True
        ),

        # ✅ 步骤3: 成功 - 输入文本
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=task.id,
            keyword_id=input_kw.id,
            step_name="✅ 步骤3: 输入搜索关键词（应该成功）",
            step_order=3,
            parameters={
                "selector": "#kw",
                "text": "Agent测试"
            },
            enabled=True
        ),

        # ❌ 步骤4: 失败 - 等待不存在的元素
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=task.id,
            keyword_id=wait_kw.id,
            step_name="❌ 步骤4: 等待不存在的元素（应该失败）",
            step_order=4,
            parameters={
                "selector": "#non-existent-element-12345",
                "state": "visible",
                "timeout": 3000
            },
            enabled=True,
            continue_on_failure=True  # 失败后继续执行
        ),

        # ❌ 步骤5: 失败 - 点击不存在的元素
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=task.id,
            keyword_id=click_kw.id,
            step_name="❌ 步骤5: 点击不存在的按钮（应该失败）",
            step_order=5,
            parameters={
                "selector": "#non-existent-button-67890"
            },
            enabled=True,
            continue_on_failure=True
        ),

        # ✅ 步骤6: 成功 - 点击搜索按钮（恢复成功）
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=task.id,
            keyword_id=click_kw.id,
            step_name="✅ 步骤6: 点击真实搜索按钮（应该成功）",
            step_order=6,
            parameters={
                "selector": "#su"
            },
            enabled=True
        ),
    ]

    for step in steps:
        db.add(step)
        step_ids.append(str(step.id).replace('-', ''))  # 收集步骤 ID（无连字符格式）
    db.commit()
    print(f"✓ 创建 {len(steps)} 个步骤（3个成功 + 3个失败）")

    # 更新用例的 step_ids（使用无连字符格式，与 SQLite 存储一致）
    case.step_ids = step_ids
    db.commit()
    print(f"✓ 已更新用例的 step_ids（{len(step_ids)} 个步骤）")

    print()
    print("=" * 60)
    print("混合结果测试任务创建成功！")
    print("=" * 60)
    print(f"任务ID: {task.id}")
    print(f"任务名称: {task.name}")
    print(f"场景数: 1")
    print(f"用例数: 1")
    print(f"步骤数: {len(steps)}")
    print()
    print("预期结果:")
    print("  - 步骤1-3: 成功（导航、等待、输入）")
    print("  - 步骤4-5: 失败（等待不存在的元素、点击不存在的按钮）")
    print("  - 步骤6: 成功（点击真实搜索按钮）")
    print()
    print("测试要点:")
    print("  1. 验证 Agent 执行模式正确创建步骤记录")
    print("  2. 验证失败步骤在报告中详细显示")
    print("  3. 验证成功和失败步骤都正确记录")
    print("  4. 验证 continue_on_failure 参数生效")
    print("=" * 60)

finally:
    db.close()
