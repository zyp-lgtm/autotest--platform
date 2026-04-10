#!/usr/bin/env python3
"""调试任务数据"""
import sys
import os
import uuid
import json

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask, UIScenario, UICase, UIStep


def debug_task():
    """调试任务数据"""
    db = Session(engine)

    try:
        task_id = uuid.UUID("190d5cd7-55a4-4649-9248-9e26de4f33f8")
        task = db.query(UITask).filter(UITask.id == task_id).first()

        if not task:
            print("❌ 任务不存在")
            return

        print(f"✅ 任务: {task.name}")
        print(f"   scenario_ids 类型: {type(task.scenario_ids)}")
        print(f"   scenario_ids 值: {task.scenario_ids}")
        print(f"   scenario_ids 长度: {len(task.scenario_ids) if task.scenario_ids else 0}")

        scenario_ids = task.scenario_ids
        if isinstance(scenario_ids, str):
            print("   scenario_ids 是字符串，尝试解析...")
            try:
                scenario_ids = json.loads(scenario_ids)
                print(f"   解析后: {scenario_ids}")
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON 解析失败: {e}")
                return

        # 检查每个 scenario_id
        for idx, scenario_id in enumerate(scenario_ids):
            print(f"\n   场景 #{idx}:")
            print(f"      ID 类型: {type(scenario_id)}")
            print(f"      ID 值: {scenario_id}")
            print(f"      ID 值 repr: {repr(scenario_id)}")

            # 检查是否为有效 UUID
            try:
                if isinstance(scenario_id, uuid.UUID):
                    scenario_uuid = scenario_id
                    print(f"      ✅ 已经是 UUID 对象")
                else:
                    scenario_uuid = uuid.UUID(str(scenario_id))
                    print(f"      ✅ 转换为 UUID: {scenario_uuid}")
            except ValueError as e:
                print(f"      ❌ 无效的 UUID: {e}")
                continue

            # 查询场景
            scenario = db.query(UIScenario).filter(
                UIScenario.id == scenario_uuid
            ).first()

            if scenario:
                print(f"      ✅ 找到场景: {scenario.name}")
            else:
                print(f"      ❌ 场景不存在")

    finally:
        db.close()


if __name__ == "__main__":
    debug_task()
