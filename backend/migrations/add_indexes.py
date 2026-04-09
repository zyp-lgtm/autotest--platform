"""
添加数据库索引以优化查询性能

执行此脚本将为所有外键字段添加索引，显著提升查询性能
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()


def add_indexes():
    """添加所有外键字段的索引"""

    # 连接数据库
    engine = create_engine(settings.DATABASE_URL)

    indexes = [
        # UITask 表
        ("idx_ui_tasks_project_id", "ui_tasks", "project_id"),
        ("idx_ui_tasks_created_by", "ui_tasks", "created_by"),

        # UIScenario 表
        ("idx_ui_scenarios_project_id", "ui_scenarios", "project_id"),
        ("idx_ui_scenarios_task_id", "ui_scenarios", "task_id"),
        ("idx_ui_scenarios_created_by", "ui_scenarios", "created_by"),

        # UICase 表
        ("idx_ui_test_cases_project_id", "ui_test_cases", "project_id"),
        ("idx_ui_test_cases_scenario_id", "ui_test_cases", "scenario_id"),
        ("idx_ui_test_cases_created_by", "ui_test_cases", "created_by"),

        # UIStep 表
        ("idx_ui_test_steps_case_id", "ui_test_steps", "case_id"),
        ("idx_ui_test_steps_scenario_id", "ui_test_steps", "scenario_id"),
        ("idx_ui_test_steps_task_id", "ui_test_steps", "task_id"),
        ("idx_ui_test_steps_keyword_id", "ui_test_steps", "keyword_id"),

        # TestExecution 表
        ("idx_test_executions_task_id", "test_executions", "task_id"),
        ("idx_test_executions_project_id", "test_executions", "project_id"),
        ("idx_test_executions_user_id", "test_executions", "user_id"),

        # ScenarioExecution 表
        ("idx_scenario_executions_test_execution_id", "scenario_executions", "test_execution_id"),
        ("idx_scenario_executions_scenario_id", "scenario_executions", "scenario_id"),

        # CaseExecution 表
        ("idx_case_executions_scenario_execution_id", "case_executions", "scenario_execution_id"),
        ("idx_case_executions_case_id", "case_executions", "case_id"),

        # StepExecution 表
        ("idx_step_executions_case_execution_id", "step_executions", "case_execution_id"),
        ("idx_step_executions_step_id", "step_executions", "step_id"),
        ("idx_step_executions_keyword_id", "step_executions", "keyword_id"),
        ("idx_step_executions_retry_of", "step_executions", "retry_of"),

        # TestData 表
        ("idx_test_data_project_id", "test_data", "project_id"),
        ("idx_test_data_created_by", "test_data", "created_by"),

        # Keywords 表（如果存在）
        ("idx_keywords_category", "keywords", "category"),
        ("idx_keywords_is_valid", "keywords", "is_valid"),
    ]

    with engine.connect() as conn:
        created_count = 0
        skipped_count = 0
        error_count = 0

        print("🚀 开始添加数据库索引...\n")

        for index_name, table_name, column_name in indexes:
            try:
                # 检查索引是否已存在
                check_sql = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name=:index_name
                """)

                result = conn.execute(check_sql, {"index_name": index_name}).fetchone()

                if result:
                    print(f"⏭️  索引已存在: {index_name}")
                    skipped_count += 1
                    continue

                # 创建索引
                create_sql = text(f"""
                    CREATE INDEX {index_name}
                    ON {table_name} ({column_name})
                """)

                conn.execute(create_sql)
                conn.commit()

                print(f"✅ 创建索引: {index_name} ON {table_name}({column_name})")
                created_count += 1

            except Exception as e:
                print(f"❌ 创建索引失败: {index_name} - {str(e)}")
                error_count += 1

        print(f"\n📊 索引添加完成:")
        print(f"   ✅ 成功创建: {created_count} 个")
        print(f"   ⏭️  已存在跳过: {skipped_count} 个")
        print(f"   ❌ 创建失败: {error_count} 个")

        # 显示创建的索引
        print(f"\n🔍 验证索引:")
        for index_name, table_name, column_name in indexes[:5]:  # 只显示前5个
            try:
                check_sql = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name=:index_name
                """)
                result = conn.execute(check_sql, {"index_name": index_name}).fetchone()
                status = "✅" if result else "❌"
                print(f"   {status} {index_name}")
            except:
                print(f"   ❌ {index_name}")

        print(f"\n✨ 数据库索引优化完成！")


if __name__ == "__main__":
    add_indexes()
