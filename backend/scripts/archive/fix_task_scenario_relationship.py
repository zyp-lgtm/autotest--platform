#!/usr/bin/env python3
"""
修复任务和场景的关系

问题：任务 "1" 的 scenario_ids 为空，导致执行时无法加载场景、用例和步骤
解决：将场景 "1" 添加到任务 "1" 的 scenario_ids 中
"""
import sqlite3
import json
import sys

def fix_relationship():
    conn = sqlite3.connect('test_platform.db')
    cursor = conn.cursor()

    try:
        # 获取任务 1
        task_id = '726c0a92fdb34dccbf426c963a5483e8'
        cursor.execute("SELECT id, name, scenario_ids FROM ui_tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()

        if not task:
            print("❌ 任务不存在")
            return False

        print(f"✅ 找到任务: {task[1]} (ID: {task[0]})")
        print(f"   当前 scenario_ids: {task[2]}")

        # 查找属于该任务的所有场景
        cursor.execute(
            "SELECT id, name FROM ui_scenarios WHERE task_id = ? ORDER BY execution_order",
            (task_id,)
        )
        scenarios = cursor.fetchall()

        if not scenarios:
            print("❌ 没有找到属于该任务的场景")
            return False

        print(f"\n✅ 找到 {len(scenarios)} 个场景:")
        scenario_ids = []
        for scenario in scenarios:
            print(f"   - {scenario[1]} (ID: {scenario[0]})")
            scenario_ids.append(str(scenario[0]))

        # 更新任务的 scenario_ids
        new_scenario_ids = json.dumps(scenario_ids)
        cursor.execute(
            "UPDATE ui_tasks SET scenario_ids = ? WHERE id = ?",
            (new_scenario_ids, task_id)
        )
        conn.commit()

        print(f"\n✅ 已更新任务的 scenario_ids: {new_scenario_ids}")

        # 验证更新
        cursor.execute("SELECT scenario_ids FROM ui_tasks WHERE id = ?", (task_id,))
        updated = cursor.fetchone()
        print(f"✅ 验证: {updated[0]}")

        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("修复任务和场景的关系")
    print("=" * 60)
    print()

    success = fix_relationship()

    if success:
        print("\n" + "=" * 60)
        print("✅ 修复完成！现在可以执行任务了")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ 修复失败")
        print("=" * 60)
        sys.exit(1)
