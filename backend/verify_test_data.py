#!/usr/bin/env python3
"""验证测试数据是否正确更新"""
import sys
import os
import uuid
import json

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario, UICase, UIStep
from app.models.keyword import Keyword


def verify_test_data():
    """验证测试数据"""
    db = Session(engine)

    try:
        task = db.query(UITask).filter(
            UITask.name == "调试信息集成测试"
        ).first()

        if not task:
            print("❌ 未找到测试任务")
            return

        print(f"✅ 任务: {task.name}")

        scenario_ids = task.scenario_ids or []
        if isinstance(scenario_ids, str):
            scenario_ids = json.loads(scenario_ids)

        for scenario_id in scenario_ids:
            try:
                scenario_uuid = uuid.UUID(str(scenario_id))
            except ValueError:
                continue

            scenario = db.query(UIScenario).filter(
                UIScenario.id == scenario_uuid
            ).first()

            if not scenario:
                continue

            print(f"\n📋 场景: {scenario.name}")

            case_ids = scenario.case_ids or []
            if isinstance(case_ids, str):
                case_ids = json.loads(case_ids)

            for case_id in case_ids:
                try:
                    case_uuid = uuid.UUID(str(case_id))
                except ValueError:
                    continue

                case = db.query(UICase).filter(
                    UICase.id == case_uuid
                ).first()

                if not case:
                    continue

                print(f"  📝 用例: {case.name}")

                step_ids = case.step_ids or []
                if isinstance(step_ids, str):
                    step_ids = json.loads(step_ids)

                for step_id in step_ids:
                    try:
                        step_uuid = uuid.UUID(str(step_id))
                    except ValueError:
                        continue

                    step = db.query(UIStep).filter(
                        UIStep.id == step_uuid
                    ).first()

                    if not step:
                        continue

                    keyword = db.query(Keyword).filter(
                        Keyword.id == step.keyword_id
                    ).first()

                    if not keyword:
                        continue

                    params = step.parameters or {}
                    print(f"    - {keyword.name}: {params}")

    finally:
        db.close()


if __name__ == "__main__":
    verify_test_data()
