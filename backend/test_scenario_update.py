"""
测试任务 scenario_ids 更新功能
"""
import json
import uuid
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.ui_task import UITask

def test_scenario_update():
    """测试使用原生 SQL 更新 scenario_ids"""
    db = SessionLocal()

    try:
        # 获取第一个任务
        task = db.query(UITask).first()
        if not task:
            print("没有找到任务")
            return

        print(f"测试任务: {task.name}")
        print(f"任务 ID: {task.id}")
        print(f"更新前 scenario_ids: {task.scenario_ids}")

        # 生成一个测试场景 ID
        test_scenario_id = str(uuid.uuid4())
        print(f"\n准备添加场景 ID: {test_scenario_id}")

        # SQLite 存储的 UUID 没有横线，需要去除横线
        task_id_str = str(task.id).replace('-', '')
        print(f"查询用 task_id (无横线): {task_id_str}")

        # 查询当前的 scenario_ids
        result = db.execute(
            text("SELECT scenario_ids FROM ui_tasks WHERE id = :task_id"),
            {"task_id": task_id_str}
        )
        row = result.fetchone()

        if row:
            current_ids_json = row[0]
            print(f"\n原始 JSON: {current_ids_json}")

            # 解析 JSON
            try:
                if isinstance(current_ids_json, str):
                    current_ids = json.loads(current_ids_json)
                else:
                    current_ids = current_ids_json if current_ids_json else []
            except Exception as e:
                print(f"JSON 解析失败: {e}，使用空列表")
                current_ids = []

            # 确保是列表
            if not isinstance(current_ids, list):
                current_ids = []

            print(f"解析后的列表: {current_ids}")

            # 添加新场景 ID
            current_ids.append(test_scenario_id)
            new_ids_json = json.dumps(current_ids)

            print(f"准备更新为: {new_ids_json}")

            # 使用原生 SQL 直接更新
            update_result = db.execute(
                text("UPDATE ui_tasks SET scenario_ids = :scenario_ids WHERE id = :task_id"),
                {"scenario_ids": new_ids_json, "task_id": task_id_str}
            )

            print(f"更新行数: {update_result.rowcount}")

            # 提交事务
            db.commit()
            print("✓ 已提交事务")

            # 验证更新
            verify_result = db.execute(
                text("SELECT scenario_ids FROM ui_tasks WHERE id = :task_id"),
                {"task_id": task_id_str}
            )
            verify_row = verify_result.fetchone()
            print(f"\n验证查询结果: {verify_row[0] if verify_row else 'None'}")

            # 再次使用 ORM 验证
            db.refresh(task)
            print(f"ORM 查询结果: {task.scenario_ids}")

            # 检查新 ID 是否在列表中
            if test_scenario_id in task.scenario_ids:
                print(f"\n✓ 成功！场景 ID {test_scenario_id} 已添加到列表中")
            else:
                print(f"\n✗ 失败！场景 ID {test_scenario_id} 未在列表中")

        else:
            print(f"未找到任务 {task.id}")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()

    finally:
        db.close()

if __name__ == "__main__":
    test_scenario_update()
