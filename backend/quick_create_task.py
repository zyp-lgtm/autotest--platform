#!/usr/bin/env python3
"""快速创建测试任务（直接操作数据库）"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal, engine
from app.models.ui_task import UITask, UIScenario, UICase, UIStep
from app.models.keyword import Keyword
import uuid

def create_test_task():
    """创建测试任务"""
    db = SessionLocal()

    try:
        # 1. 获取关键字
        print("1. 获取关键字...")
        keywords = {kw.name: kw for kw in db.query(Keyword).all()}

        required = ["NAVIGATE", "WAIT_FOR_ELEMENT", "INPUT", "CLICK"]
        missing = [k for k in required if k not in keywords]
        if missing:
            print(f"   ✗ 缺少关键字: {missing}")
            print(f"   可用关键字: {list(keywords.keys())}")
            return False

        print(f"   ✓ 找到 {len(keywords)} 个关键字")

        # 2. 获取或创建项目 ID（使用第一个任务的 project_id）
        print("\n2. 获取项目 ID...")
        existing_task = db.query(UITask).first()
        if existing_task:
            project_id = existing_task.project_id
            print(f"   ✓ 使用现有项目: {project_id}")
        else:
            project_id = uuid.uuid4()
            print(f"   ✓ 使用新项目 ID: {project_id}")

        # 3. 创建任务
        print("\n3. 创建任务...")
        task = UITask(
            id=uuid.uuid4(),
            project_id=project_id,
            name="🧪 混合结果测试（成功+失败）",
            description="测试 Agent 执行模式下的 continue_on_failure 参数",
            task_type="ui",
            scenario_ids=[],
            tags=["测试", "Agent"]
        )
        db.add(task)
        db.flush()  # 获取 task.id
        print(f"   ✓ 任务创建成功: {task.id}")

        # 4. 创建场景
        print("\n4. 创建场景...")
        scenario = UIScenario(
            id=uuid.uuid4(),
            project_id=project_id,
            task_id=task.id,
            name="混合结果场景",
            description="包含成功和失败步骤的测试场景",
            case_ids=[]
        )
        db.add(scenario)
        db.flush()

        # 更新任务的 scenario_ids
        task.scenario_ids = [str(scenario.id)]
        print(f"   ✓ 场景创建成功: {scenario.id}")

        # 5. 创建用例
        print("\n5. 创建用例...")
        case = UICase(
            id=uuid.uuid4(),
            project_id=project_id,
            scenario_id=scenario.id,
            name="混合结果用例",
            description="测试 continue_on_failure 参数",
            step_ids=[]
        )
        db.add(case)
        db.flush()

        # 更新场景的 case_ids
        scenario.case_ids = [str(case.id)]
        print(f"   ✓ 用例创建成功: {case.id}")

        # 6. 创建步骤
        print("\n6. 创建步骤...")
        steps_data = [
            {
                "name": "✅ 步骤1: 打开百度首页（应该成功）",
                "order": 1,
                "keyword": "NAVIGATE",
                "params": {"url": "https://www.baidu.com"},
                "continue_on_failure": False
            },
            {
                "name": "✅ 步骤2: 等待搜索框（应该成功）",
                "order": 2,
                "keyword": "WAIT_FOR_ELEMENT",
                "params": {"selector": "#kw", "state": "attached", "timeout": 5000},
                "continue_on_failure": False
            },
            {
                "name": "✅ 步骤3: 输入搜索关键词（应该成功）",
                "order": 3,
                "keyword": "INPUT",
                "params": {"selector": "#kw", "text": "Agent测试"},
                "continue_on_failure": False
            },
            {
                "name": "❌ 步骤4: 等待不存在的元素（应该失败）",
                "order": 4,
                "keyword": "WAIT_FOR_ELEMENT",
                "params": {"selector": "#non-existent-element-12345", "state": "visible", "timeout": 3000},
                "continue_on_failure": True  # 失败后继续
            },
            {
                "name": "❌ 步骤5: 点击不存在的按钮（应该失败）",
                "order": 5,
                "keyword": "CLICK",
                "params": {"selector": "#non-existent-button-67890"},
                "continue_on_failure": True  # 失败后继续
            },
            {
                "name": "✅ 步骤6: 点击真实搜索按钮（应该成功）",
                "order": 6,
                "keyword": "CLICK",
                "params": {"selector": "#su"},
                "continue_on_failure": False
            }
        ]

        step_ids = []
        for step_data in steps_data:
            step = UIStep(
                id=uuid.uuid4(),
                case_id=case.id,
                scenario_id=scenario.id,
                task_id=task.id,
                keyword_id=keywords[step_data["keyword"]].id,
                step_name=step_data["name"],
                step_order=step_data["order"],
                parameters=step_data["params"],
                continue_on_failure=step_data["continue_on_failure"],
                enabled=True
            )
            db.add(step)
            step_ids.append(step.id)
            print(f"   ✓ {step_data['name']}")

        # 更新用例的 step_ids
        case.step_ids = [str(sid) for sid in step_ids]

        # 提交所有更改
        db.commit()

        print("\n" + "=" * 60)
        print("✅ 测试任务创建成功！")
        print("=" * 60)
        print(f"任务 ID: {task.id}")
        print(f"任务名称: {task.name}")
        print(f"场景 ID: {scenario.id}")
        print(f"用例 ID: {case.id}")
        print(f"步骤数: {len(step_ids)}")

        print("\n📝 任务说明:")
        print("  • 步骤 1-3: 成功（导航、等待、输入）")
        print("  • 步骤 4-5: 失败但 continue_on_failure=True")
        print("  • 步骤 6: 点击搜索按钮")

        print("\n🌐 前端查看:")
        print("  1. 访问 http://localhost:3000")
        print("  2. 登录 demo/demo123")
        print(f"  3. 在任务列表中找到 '{task.name}'")
        print("  4. 点击执行按钮测试 Agent 模式")

        print("\n🎯 预期结果:")
        print("  • 总步骤: 6")
        print("  • 通过: 3-4 步")
        print("  • 失败: 2-3 步")
        print("  • 所有步骤都会被执行（步骤 4、5 虽失败但继续）")
        print("=" * 60)

        return True

    except Exception as e:
        db.rollback()
        print(f"\n✗ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("快速创建混合结果测试任务")
    print("=" * 60)
    success = create_test_task()
    sys.exit(0 if success else 1)
