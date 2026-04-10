#!/usr/bin/env python3
"""修复数据库中的 scenario_ids 格式（字典 -> 列表）"""
import sys
import os
import uuid
import json

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario, UICase


def fix_scenario_ids():
    """修复 scenario_ids 格式"""
    db = Session(engine)

    try:
        # 1. 修复任务的 scenario_ids
        tasks = db.query(UITask).all()

        for task in tasks:
            scenario_ids = task.scenario_ids

            # 如果是字典，转换为列表
            if isinstance(scenario_ids, dict):
                print(f"修复任务 {task.name} 的 scenario_ids")
                print(f"  旧值 (dict): {scenario_ids}")

                # 提取字典的键作为列表
                task.scenario_ids = list(scenario_ids.keys())

                print(f"  新值 (list): {task.scenario_ids}")

        # 2. 修复场景的 case_ids
        scenarios = db.query(UIScenario).all()

        for scenario in scenarios:
            case_ids = scenario.case_ids

            # 如果是字典，转换为列表
            if isinstance(case_ids, dict):
                print(f"修复场景 {scenario.name} 的 case_ids")
                print(f"  旧值 (dict): {case_ids}")
                scenario.case_ids = list(case_ids.keys())
                print(f"  新值 (list): {scenario.case_ids}")

        # 3. 修复用例的 step_ids
        cases = db.query(UICase).all()

        for case in cases:
            step_ids = case.step_ids

            # 如果是字典，转换为列表
            if isinstance(step_ids, dict):
                print(f"修复用例 {case.name} 的 step_ids")
                print(f"  旧值 (dict): {step_ids}")
                case.step_ids = list(step_ids.keys())
                print(f"  新值 (list): {case.step_ids}")

        # 提交更改
        db.commit()
        print("\n✅ 数据格式修复完成！")

        # 验证修复结果
        print("\n验证修复结果:")
        task = db.query(UITask).filter(
            UITask.name == "调试信息集成测试"
        ).first()
        if task:
            print(f"scenario_ids 类型: {type(task.scenario_ids)}")
            print(f"scenario_ids 值: {task.scenario_ids}")

    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    fix_scenario_ids()
