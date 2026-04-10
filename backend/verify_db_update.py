#!/usr/bin/env python3
"""直接查询 SQLite 数据库"""
import sqlite3

db_path = "/Users/apple/aicode/.worktrees/test-platform/backend/test_platform.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询任务的 scenario_ids
cursor.execute("""
    SELECT name, scenario_ids
    FROM ui_tasks
    WHERE name = '调试信息集成测试'
""")

result = cursor.fetchone()
if result:
    name, scenario_ids = result
    print(f"任务名称: {name}")
    print(f"scenario_ids (原始): {scenario_ids}")
    print(f"scenario_ids (类型): {type(scenario_ids)}")

    # 解析 JSON
    import json
    if scenario_ids:
        parsed = json.loads(scenario_ids)
        print(f"scenario_ids (解析后): {parsed}")
        print(f"解析后类型: {type(parsed)}")

        # 检查是列表还是字典
        if isinstance(parsed, dict):
            print("❌ 还是字典格式！")
            print(f"字典键: {list(parsed.keys())}")
        elif isinstance(parsed, list):
            print("✅ 已是列表格式")
            print(f"列表长度: {len(parsed)}")
else:
    print("❌ 未找到任务")

conn.close()
