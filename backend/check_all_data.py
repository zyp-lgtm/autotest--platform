#!/usr/bin/env python3
"""全面检查数据库数据"""
import sys
import os
import uuid
import json

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario, UICase, UIStep


def check_all_data():
    """检查所有数据"""
    db = Session(engine)

    try:
        print("=" * 60)
        print("检查任务数据")
        print("=" * 60)

        task = db.query(UITask).filter(
            UITask.name == "调试信息集成测试"
        ).first()

        if not task:
            print("❌ 任务不存在")
            return

        print(f"✅ 任务: {task.name}")
        print(f"   scenario_ids 类型: {type(task.scenario_ids)}")
        print(f"   scenario_ids: {task.scenario_ids}")

        scenario_ids = task.scenario_ids
        if isinstance(scenario_ids, str):
            try:
                scenario_ids = json.loads(scenario_ids)
            except:
                print("   ❌ scenario_ids 是无效的 JSON 字符串")
                return

        if not isinstance(scenario_ids, list):
            print(f"   ❌ scenario_ids 不是列表: {type(scenario_ids)}")
            return

        print(f"\n遍历 {len(scenario_ids)} 个场景:\n")

        for idx, scenario_id in enumerate(scenario_ids):
            print(f"场景 #{idx}: {scenario_id} (type: {type(scenario_id)})")

            # 检查类型
            if not isinstance(scenario_id, (str, uuid.UUID)):
                print(f"   ❌ 无效的类型")
                continue

            # 转换为 UUID
            try:
                if isinstance(scenario_id, uuid.UUID):
                    scenario_uuid = scenario_id
                else:
                    scenario_uuid = uuid.UUID(str(scenario_id))
            except ValueError as e:
                print(f"   ❌ UUID 转换失败: {e}")
                continue

            # 查询场景
            scenario = db.query(UIScenario).filter(
                UIScenario.id == scenario_uuid
            ).first()

            if not scenario:
                print(f"   ❌ 场景不存在")
                continue

            print(f"   ✅ 场景: {scenario.name}")
            print(f"      case_ids 类型: {type(scenario.case_ids)}")
            print(f"      case_ids: {scenario.case_ids}")

            case_ids = scenario.case_ids
            if isinstance(case_ids, str):
                try:
                    case_ids = json.loads(case_ids)
                except:
                    print(f"      ❌ case_ids 是无效的 JSON")
                    continue

            if not isinstance(case_ids, list):
                print(f"      ❌ case_ids 不是列表: {type(case_ids)}")
                continue

            for case_id in case_ids:
                print(f"\n      用例: {case_id}")

                try:
                    if isinstance(case_id, uuid.UUID):
                        case_uuid = case_id
                    else:
                        case_uuid = uuid.UUID(str(case_id))
                except ValueError as e:
                    print(f"         ❌ UUID 转换失败: {e}")
                    continue

                case = db.query(UICase).filter(
                    UICase.id == case_uuid
                ).first()

                if not case:
                    print(f"         ❌ 用例不存在")
                    continue

                print(f"         ✅ 用例: {case.name}")

                step_ids = case.step_ids
                if isinstance(step_ids, str):
                    try:
                        step_ids = json.loads(step_ids)
                    except:
                        print(f"            ❌ step_ids 是无效的 JSON")
                        continue

                if not isinstance(step_ids, list):
                    print(f"            ❌ step_ids 不是列表: {type(step_ids)}")
                    continue

                print(f"            步骤数: {len(step_ids)}")

        print("\n" + "=" * 60)
        print("数据检查完成")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    check_all_data()
