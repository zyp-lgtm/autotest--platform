#!/usr/bin/env python3
"""快速验证数据"""
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario

db = Session(engine)

task = db.query(UITask).filter(
    UITask.name == "调试信息集成测试"
).first()

if task:
    print(f"任务: {task.name}")
    print(f"scenario_ids 类型: {type(task.scenario_ids)}")
    print(f"scenario_ids: {task.scenario_ids}")

    if task.scenario_ids and len(task.scenario_ids) > 0:
        scenario_id = task.scenario_ids[0]
        print(f"\n第一个场景 ID: {scenario_id} (type: {type(scenario_id)})")

        # 转换为 UUID
        try:
            if isinstance(scenario_id, uuid.UUID):
                scenario_uuid = scenario_id
            else:
                scenario_uuid = uuid.UUID(str(scenario_id))

            scenario = db.query(UIScenario).filter(
                UIScenario.id == scenario_uuid
            ).first()

            if scenario:
                print(f"✅ 找到场景: {scenario.name}")
                print(f"case_ids: {scenario.case_ids}")
            else:
                print(f"❌ 场景不存在")
        except Exception as e:
            print(f"❌ 错误: {e}")

db.close()
