#!/usr/bin/env python3
"""检查测试任务的完整数据"""
import sqlite3

conn = sqlite3.connect('test_platform.db')
cursor = conn.cursor()

# 查找混合结果测试任务
cursor.execute("SELECT id, name FROM ui_tasks WHERE name LIKE '%混合结果%'")
tasks = cursor.fetchall()

if not tasks:
    print("✗ 没有找到混合结果测试任务")
else:
    for task_id, task_name in tasks:
        print(f"✓ 任务: {task_name}")
        print(f"  ID: {task_id}")

        # 查找场景
        cursor.execute("SELECT id, name, case_ids FROM ui_scenarios WHERE task_id = ?", (task_id,))
        scenarios = cursor.fetchall()

        for scenario_id, scenario_name, case_ids in scenarios:
            print(f"\n✓ 场景: {scenario_name}")
            print(f"  ID: {scenario_id}")
            print(f"  case_ids: {case_ids}")

            if case_ids:
                import json
                case_ids_list = json.loads(case_ids) if isinstance(case_ids, str) else case_ids
                print(f"  case_ids 数量: {len(case_ids_list)}")

                # 查找用例
                for case_id in case_ids_list:
                    cursor.execute("SELECT id, name, step_ids FROM ui_test_cases WHERE id = ?", (case_id,))
                    case = cursor.fetchone()

                    if case:
                        case_id, case_name, step_ids = case
                        print(f"\n✓ 用例: {case_name}")
                        print(f"  ID: {case_id}")
                        print(f"  step_ids: {step_ids}")

                        if step_ids:
                            step_ids_list = json.loads(step_ids) if isinstance(step_ids, str) else step_ids
                            print(f"  step_ids 数量: {len(step_ids_list)}")

                            # 统计步骤
                            print(f"\n✓ 应该有 {len(step_ids_list)} 个步骤")
                        else:
                            print(f"  ✗ step_ids 为空")
                    else:
                        print(f"\n✗ 用例不存在: {case_id}")
            else:
                print(f"  ✗ case_ids 为空")

conn.close()
