#!/usr/bin/env python3
"""
更新测试数据 - 使用有效的百度搜索选择器
"""
import sys
import os
import uuid
import json

# 添加项目路径到 sys.path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario, UICase, UIStep
from app.models.keyword import Keyword


def update_test_data():
    """更新测试数据中的选择器"""
    db = Session(engine)

    try:
        # 1. 查找测试任务
        task = db.query(UITask).filter(
            UITask.name == "调试信息集成测试"
        ).first()

        if not task:
            print("❌ 未找到测试任务 '调试信息集成测试'")
            return

        print(f"✅ 找到任务: {task.name} (ID: {task.id})")

        # 2. 遍历场景（需要转换为 UUID）
        scenario_ids = task.scenario_ids or []
        if isinstance(scenario_ids, str):
            scenario_ids = json.loads(scenario_ids)

        for scenario_id in scenario_ids:
            # 转换为 UUID 对象
            try:
                if isinstance(scenario_id, uuid.UUID):
                    scenario_uuid = scenario_id
                else:
                    scenario_uuid = uuid.UUID(str(scenario_id))
            except ValueError:
                print(f"⚠️  跳过无效的场景 ID: {scenario_id}")
                continue

            scenario = db.query(UIScenario).filter(
                UIScenario.id == scenario_uuid
            ).first()

            if not scenario:
                continue

            print(f"\n📋 场景: {scenario.name}")

            # 3. 遍历用例
            case_ids = scenario.case_ids or []
            if isinstance(case_ids, str):
                case_ids = json.loads(case_ids)

            for case_id in case_ids:
                # 转换为 UUID 对象
                try:
                    if isinstance(case_id, uuid.UUID):
                        case_uuid = case_id
                    else:
                        case_uuid = uuid.UUID(str(case_id))
                except ValueError:
                    print(f"⚠️  跳过无效的用例 ID: {case_id}")
                    continue

                case = db.query(UICase).filter(
                    UICase.id == case_uuid
                ).first()

                if not case:
                    continue

                print(f"  📝 用例: {case.name}")

                # 4. 遍历步骤
                step_ids = case.step_ids or []
                if isinstance(step_ids, str):
                    step_ids = json.loads(step_ids)

                for step_id in step_ids:
                    # 转换为 UUID 对象
                    try:
                        if isinstance(step_id, uuid.UUID):
                            step_uuid = step_id
                        else:
                            step_uuid = uuid.UUID(str(step_id))
                    except ValueError:
                        print(f"⚠️  跳过无效的步骤 ID: {step_id}")
                        continue

                    step = db.query(UIStep).filter(
                        UIStep.id == step_uuid
                    ).first()

                    if not step:
                        continue

                    # 获取关键字名称
                    keyword = db.query(Keyword).filter(
                        Keyword.id == step.keyword_id
                    ).first()

                    if not keyword:
                        continue

                    # 更新参数
                    old_params = step.parameters or {}
                    new_params = {}

                    if keyword.name == "NAVIGATE":
                        new_params = {
                            "url": "https://www.baidu.com",
                            "wait_until": "load",
                            "timeout": 30000
                        }
                        print(f"    ✏️  更新步骤: {step.step_name} (NAVIGATE)")
                        print(f"       旧参数: {old_params}")
                        print(f"       新参数: {new_params}")

                    elif keyword.name == "INPUT":
                        new_params = {
                            "selector": "#kw",
                            "text": "测试搜索",
                            "clear_first": True,
                            "timeout": 5000
                        }
                        print(f"    ✏️  更新步骤: {step.step_name} (INPUT)")
                        print(f"       旧参数: {old_params}")
                        print(f"       新参数: {new_params}")

                    elif keyword.name == "CLICK":
                        new_params = {
                            "selector": "#su",
                            "timeout": 5000,
                            "force": False,
                            "click_count": 1
                        }
                        print(f"    ✏️  更新步骤: {step.step_name} (CLICK)")
                        print(f"       旧参数: {old_params}")
                        print(f"       新参数: {new_params}")

                    elif keyword.name == "WAIT_FOR_ELEMENT":
                        new_params = {
                            "selector": ".result",
                            "state": "visible",
                            "timeout": 10000
                        }
                        print(f"    ✏️  更新步骤: {step.step_name} (WAIT_FOR_ELEMENT)")
                        print(f"       旧参数: {old_params}")
                        print(f"       新参数: {new_params}")

                    elif keyword.name == "SCREENSHOT":
                        new_params = {
                            "path": "./screenshots/test_baidu.png",
                            "full_page": False
                        }
                        print(f"    ✏️  更新步骤: {step.step_name} (SCREENSHOT)")
                        print(f"       旧参数: {old_params}")
                        print(f"       新参数: {new_params}")

                    else:
                        # 保留其他步骤的参数
                        new_params = old_params

                    # 更新步骤
                    step.parameters = new_params

        # 5. 提交更改
        db.commit()
        print("\n✅ 测试数据更新成功！")

    except Exception as e:
        print(f"\n❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    update_test_data()
