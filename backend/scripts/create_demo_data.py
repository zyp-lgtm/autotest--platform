"""
创建Demo测试数据
用于演示完整的测试流程
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import uuid
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.project import Project
from app.models.ui_task import UITask, UIScenario, UICase, UIStep
from app.models.keyword import Keyword


def create_demo_data():
    """创建完整的demo测试数据"""
    db: Session = SessionLocal()

    try:
        print("=" * 50)
        print("开始创建Demo测试数据...")
        print("=" * 50)

        # 1. 确保有测试用户
        print("\n[1/7] 检查测试用户...")
        test_user = db.query(User).filter(User.username == "demo").first()
        if not test_user:
            from app.core.security import hash_password
            test_user = User(
                username="demo",
                email="demo@example.com",
                full_name="Demo User",
                hashed_password=hash_password("demo123"),
                is_active=True,
                role="user"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"  ✓ 创建测试用户: {test_user.username}")
        else:
            print(f"  ✓ 测试用户已存在: {test_user.username}")

        # 2. 创建测试项目
        print("\n[2/7] 创建测试项目...")
        existing_project = db.query(Project).filter(Project.name == "百度搜索演示项目").first()
        if existing_project:
            project = existing_project
            print(f"  ✓ 项目已存在: {project.name}")
        else:
            project = Project(
                name="百度搜索演示项目",
                description="演示如何使用测试自动化平台进行UI测试",
                created_by=test_user.id
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            print(f"  ✓ 创建项目: {project.name}")

        # 3. 创建测试任务
        print("\n[3/7] 创建测试任务...")
        existing_task = db.query(UITask).filter(UITask.name == "百度搜索测试").first()
        if existing_task:
            task = existing_task
            # 删除旧数据
            db.query(UIScenario).filter(UIScenario.task_id == task.id).delete()
            db.commit()
            print(f"  ✓ 清空任务数据: {task.name}")
        else:
            task = UITask(
                name="百度搜索测试",
                description="演示百度搜索功能的UI自动化测试",
                project_id=project.id,
                task_type="ui",
                scenario_ids=[],
                tags=["demo", "ui", "baidu"],
                created_by=test_user.id
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            print(f"  ✓ 创建任务: {task.name}")

        # 4. 获取关键字
        print("\n[4/7] 获取测试关键字...")
        keyword_map = {}
        all_keywords = db.query(Keyword).all()
        for kw in all_keywords:
            keyword_map[kw.name] = kw
            print(f"  ✓ 找到关键字: {kw.name} ({kw.category})")

        required_keywords = ["NAVIGATE", "INPUT", "CLICK", "WAIT_FOR_ELEMENT"]
        missing = [k for k in required_keywords if k not in keyword_map]
        if missing:
            print(f"  ⚠ 警告: 缺少关键字: {', '.join(missing)}")

        # 5. 创建测试场景
        print("\n[5/7] 创建测试场景...")
        scenario = UIScenario(
            name="百度搜索场景",
            description="在百度首页搜索关键词并验证结果",
            project_id=project.id,
            task_id=task.id,
            scenario_type="ui",
            case_ids=[],
            execution_order=0,
            tags=["搜索", "冒烟测试"],
            created_by=test_user.id
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        print(f"  ✓ 创建场景: {scenario.name}")

        # 更新任务的场景列表
        task.scenario_ids = [scenario.id]

        # 6. 创建测试用例
        print("\n[6/7] 创建测试用例...")
        test_case = UICase(
            name="搜索关键词测试用例",
            description="打开百度首页，输入关键词并搜索",
            project_id=project.id,
            scenario_id=scenario.id,
            case_type="ui",
            step_ids=[],
            priority="P1",
            tags=["搜索", "核心功能"],
            created_by=test_user.id
        )
        db.add(test_case)
        db.commit()
        db.refresh(test_case)
        print(f"  ✓ 创建用例: {test_case.name}")

        # 更新场景的用例列表
        scenario.case_ids = [test_case.id]

        # 7. 创建测试步骤
        print("\n[7/7] 创建测试步骤...")
        steps_to_create = []

        if "NAVIGATE" in keyword_map:
            steps_to_create.append({
                "step_name": "打开百度首页",
                "keyword_id": keyword_map["NAVIGATE"].id,
                "parameters": {"url": "https://www.baidu.com"},
                "step_order": 0
            })
            print(f"  ✓ 步骤1: 打开百度首页")

        if "INPUT" in keyword_map:
            steps_to_create.append({
                "step_name": "输入搜索关键词",
                "keyword_id": keyword_map["INPUT"].id,
                "parameters": {
                    "selector": "#kw",
                    "text": "测试自动化平台",
                    "clear_first": True
                },
                "step_order": 1
            })
            print(f"  ✓ 步骤2: 输入搜索关键词")

        if "CLICK" in keyword_map:
            steps_to_create.append({
                "step_name": "点击搜索按钮",
                "keyword_id": keyword_map["CLICK"].id,
                "parameters": {
                    "selector": "#su",
                    "timeout": 5000
                },
                "step_order": 2
            })
            print(f"  ✓ 步骤3: 点击搜索按钮")

        if "WAIT_FOR_ELEMENT" in keyword_map:
            steps_to_create.append({
                "step_name": "等待搜索结果",
                "keyword_id": keyword_map["WAIT_FOR_ELEMENT"].id,
                "parameters": {
                    "selector": ".result",
                    "state": "visible",
                    "timeout": 10000
                },
                "step_order": 3
            })
            print(f"  ✓ 步骤4: 等待搜索结果")

        # 批量创建步骤
        step_ids = []
        for step_data in steps_to_create:
            step = UIStep(
                case_id=test_case.id,
                scenario_id=scenario.id,
                task_id=task.id,
                **step_data,
                enabled=True,
                continue_on_failure=False
            )
            db.add(step)
            step_ids.append(step.id)

        db.commit()

        # 更新用例的步骤列表
        test_case.step_ids = step_ids
        db.commit()

        print("\n" + "=" * 50)
        print("Demo数据创建完成!")
        print("=" * 50)
        print(f"\n项目ID: {project.id}")
        print(f"任务ID: {task.id}")
        print(f"场景ID: {scenario.id}")
        print(f"用例ID: {test_case.id}")
        print(f"步骤数: {len(steps_to_create)}")
        print(f"\n使用以下命令测试任务:")
        print(f"  curl -X POST http://localhost:8000/api/v1/ui/tasks/{task.id}/execute")

        return {
            "project_id": str(project.id),
            "task_id": str(task.id),
            "scenario_id": str(scenario.id),
            "case_id": str(test_case.id),
            "steps_count": len(steps_to_create)
        }

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    result = create_demo_data()
    if result:
        print("\n✓ Demo数据创建成功!")
    else:
        print("\n✗ Demo数据创建失败!")
        sys.exit(1)
