#!/usr/bin/env python3
"""
修复 UUID 格式问题

问题：*_ids 字段使用带连字符的 UUID，但数据库存储无连字符格式
解决：将所有 *_ids 字段统一为无连字符格式
"""
import sqlite3
import json
import re

def remove_hyphens(uuid_str):
    """移除 UUID 中的连字符"""
    return uuid_str.replace('-', '')

def fix_all_uuid_fields():
    conn = sqlite3.connect('test_platform.db')
    cursor = conn.cursor()

    print("=" * 70)
    print("修复所有 *_ids 字段的 UUID 格式")
    print("=" * 70)
    print()

    # 1. 修复任务的 scenario_ids
    print("📋 修复任务的 scenario_ids...")
    cursor.execute("SELECT id, name, scenario_ids FROM ui_tasks")
    tasks = cursor.fetchall()

    for task_id, name, scenario_ids in tasks:
        if not scenario_ids:
            continue

        ids_list = json.loads(scenario_ids)
        fixed_list = [remove_hyphens(sid) for sid in ids_list]

        if json.dumps(fixed_list) != scenario_ids:
            cursor.execute(
                "UPDATE ui_tasks SET scenario_ids = ? WHERE id = ?",
                (json.dumps(fixed_list), task_id)
            )
            print(f"   ✅ 任务 '{name}': {scenario_ids} → {json.dumps(fixed_list)}")

    conn.commit()
    print()

    # 2. 修复场景的 case_ids
    print("📁 修复场景的 case_ids...")
    cursor.execute("SELECT id, name, case_ids FROM ui_scenarios")
    scenarios = cursor.fetchall()

    for scenario_id, name, case_ids in scenarios:
        if not case_ids:
            continue

        ids_list = json.loads(case_ids)
        fixed_list = [remove_hyphens(cid) for cid in ids_list]

        if json.dumps(fixed_list) != case_ids:
            cursor.execute(
                "UPDATE ui_scenarios SET case_ids = ? WHERE id = ?",
                (json.dumps(fixed_list), scenario_id)
            )
            print(f"   ✅ 场景 '{name}': {case_ids} → {json.dumps(fixed_list)}")

    conn.commit()
    print()

    # 3. 修复用例的 step_ids
    print("📄 修复用例的 step_ids...")
    cursor.execute("SELECT id, name, step_ids FROM ui_test_cases")
    cases = cursor.fetchall()

    for case_id, name, step_ids in cases:
        if not step_ids:
            continue

        ids_list = json.loads(step_ids)
        fixed_list = [remove_hyphens(sid) for sid in ids_list]

        if json.dumps(fixed_list) != step_ids:
            cursor.execute(
                "UPDATE ui_test_cases SET step_ids = ? WHERE id = ?",
                (json.dumps(fixed_list), case_id)
            )
            print(f"   ✅ 用例 '{name}': {step_ids} → {json.dumps(fixed_list)}")

    conn.commit()
    print()

    # 4. 统计
    cursor.execute("SELECT COUNT(*) FROM ui_tasks")
    task_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ui_scenarios")
    scenario_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ui_test_cases")
    case_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ui_test_steps")
    step_count = cursor.fetchone()[0]

    print("=" * 70)
    print("✅ 修复完成！")
    print(f"   - 任务: {task_count}")
    print(f"   - 场景: {scenario_count}")
    print(f"   - 用例: {case_count}")
    print(f"   - 步骤: {step_count}")
    print("=" * 70)

    conn.close()

if __name__ == "__main__":
    fix_all_uuid_fields()
