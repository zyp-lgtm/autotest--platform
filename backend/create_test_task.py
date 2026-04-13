#!/usr/bin/env python3
"""创建测试任务"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario, UICase, UIStep
from app.models.user import User
from app.models.project import Project

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
        test_project = Project(
            id=uuid.uuid4(),
            name="测试项目",
            description="百度搜索测试",
            owner_id=test_user.id  # 使用 owner_id 而不是 created_by
        )
        db.add(test_project)
        db.commit()
        db.refresh(test_project)
        print(f"✓ 创建项目: {test_project.name}")

    # 检查任务是否已存在
    task_id = uuid.UUID("190d5cd7-55a4-4649-9248-9e26de4f33f8")
    existing_task = db.query(UITask).filter(UITask.id == task_id).first()
    if existing_task:
        print(f"✓ 任务已存在: {existing_task.name}")
        print(f"  ID: {existing_task.id}")
        sys.exit(0)

    # 创建任务
    task = UITask(
        id=task_id,
        project_id=test_project.id,
        name="百度搜索测试",
        description="自动化测试百度搜索功能",
        task_type="ui"  # 使用 task_type 而不是 status
    )
    db.add(task)
    db.commit()
    print(f"✓ 创建任务: {task.name}")

    # 创建场景
    scenario = UIScenario(
        id=uuid.uuid4(),
        project_id=test_project.id,
        task_id=task.id,
        name="基本搜索场景",
        description="测试百度基本搜索功能",
        execution_order=1  # 使用 execution_order 而不是 scenario_order
    )
    db.add(scenario)
    db.commit()
    print(f"✓ 创建场景: {scenario.name}")

    # 创建用例
    case = UICase(
        id=uuid.uuid4(),
        project_id=test_project.id,
        scenario_id=scenario.id,
        name="搜索测试用例",
        description="在百度搜索关键词",
        priority="P1"
        # 移除 case_order，该字段不存在
    )
    db.add(case)
    db.commit()
    print(f"✓ 创建用例: {case.name}")

    # 获取关键字
    from app.models.keyword import Keyword
    navigate_kw = db.query(Keyword).filter(Keyword.name == "NAVIGATE").first()
    wait_kw = db.query(Keyword).filter(Keyword.name == "WAIT_FOR_ELEMENT").first()
    input_kw = db.query(Keyword).filter(Keyword.name == "INPUT").first()
    click_kw = db.query(Keyword).filter(Keyword.name == "CLICK").first()

    if not all([navigate_kw, wait_kw, input_kw, click_kw]):
        print("错误: 缺少必要的关键字")
        sys.exit(1)

    # 创建步骤
    steps = [
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,  # 添加 scenario_id
            task_id=task.id,  # 添加 task_id
            keyword_id=navigate_kw.id,
            step_name="打开百度首页",
            step_order=1,
            parameters={"url": "https://www.baidu.com"}
        ),
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=task.id,
            keyword_id=wait_kw.id,
            step_name="等待搜索框加载",
            step_order=2,
            parameters={"selector": "#kw", "state": "visible", "timeout": 5000}
        ),
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=task.id,
            keyword_id=input_kw.id,
            step_name="输入搜索关键词",
            step_order=3,
            parameters={"selector": "#kw", "text": "测试自动化"}
        ),
        UIStep(
            id=uuid.uuid4(),
            case_id=case.id,
            scenario_id=scenario.id,
            task_id=task.id,
            keyword_id=click_kw.id,
            step_name="点击搜索按钮",
            step_order=4,
            parameters={"selector": "#su"}
        )
    ]

    for step in steps:
        db.add(step)
    db.commit()
    print(f"✓ 创建 {len(steps)} 个步骤")

    print()
    print("=" * 60)
    print("测试任务创建成功！")
    print("=" * 60)
    print(f"任务ID: {task.id}")
    print(f"任务名称: {task.name}")
    print(f"场景数: 1")
    print(f"用例数: 1")
    print(f"步骤数: {len(steps)}")
    print("=" * 60)

finally:
    db.close()
