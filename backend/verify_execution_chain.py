#!/usr/bin/env python3
"""
验证执行链：任务 → 场景 → 用例 → 步骤
"""
import sqlite3
import json

def verify_chain():
    conn = sqlite3.connect('test_platform.db')
    cursor = conn.cursor()

    print("=" * 70)
    print("验证执行链")
    print("=" * 70)
    print()

    # 1. 获取任务
    task_id = '726c0a92fdb34dccbf426c963a5483e8'
    cursor.execute("SELECT id, name, scenario_ids FROM ui_tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    if not task:
        print("❌ 任务不存在")
        return

    print(f"📋 任务: {task[1]} (ID: {task[0]})")

    # 解析 scenario_ids
    scenario_ids = json.loads(task[2]) if task[2] else []
    print(f"   scenario_ids: {scenario_ids}")
    print(f"   场景数量: {len(scenario_ids)}")
    print()

    if not scenario_ids:
        print("❌ 没有场景，无法执行")
        conn.close()
        return

    # 2. 遍历场景
    total_cases = 0
    total_steps = 0

    for sid in scenario_ids:
        cursor.execute("SELECT id, name, case_ids FROM ui_scenarios WHERE id = ?", (sid,))
        scenario = cursor.fetchone()

        if not scenario:
            print(f"⚠️  场景 {sid} 不存在")
            continue

        print(f"📁 场景: {scenario[1]} (ID: {scenario[0]})")

        # 解析 case_ids
        case_ids = json.loads(scenario[2]) if scenario[2] else []
        print(f"   case_ids: {case_ids}")
        print(f"   用例数量: {len(case_ids)}")

        if not case_ids:
            print("   ⚠️  没有用例")
            print()
            continue

        # 3. 遍历用例
        for cid in case_ids:
            cursor.execute("SELECT id, name, step_ids FROM ui_test_cases WHERE id = ?", (cid,))
            case = cursor.fetchone()

            if not case:
                print(f"   ⚠️  用例 {cid} 不存在")
                continue

            print(f"   📄 用例: {case[1]} (ID: {case[0]})")

            # 解析 step_ids
            step_ids = json.loads(case[2]) if case[2] else []
            print(f"      step_ids: {step_ids}")
            print(f"      步骤数量: {len(step_ids)}")

            total_cases += 1
            total_steps += len(step_ids)

            if step_ids:
                # 4. 遍历步骤
                for step_id in step_ids:
                    cursor.execute(
                        "SELECT id, step_name, keyword_id FROM ui_test_steps WHERE id = ?",
                        (step_id,)
                    )
                    step = cursor.fetchone()
                    if step:
                        print(f"      🔧 步骤: {step[1]} (ID: {step[0]}, Keyword: {step[2]})")
                    else:
                        print(f"      ⚠️  步骤 {step_id} 不存在")

            print()

    # 总结
    print("=" * 70)
    print(f"✅ 执行链验证完成")
    print(f"   - 场景: {len(scenario_ids)}")
    print(f"   - 用例: {total_cases}")
    print(f"   - 步骤: {total_steps}")
    print("=" * 70)

    conn.close()

if __name__ == "__main__":
    verify_chain()
