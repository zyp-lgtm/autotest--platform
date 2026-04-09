#!/usr/bin/env python3
"""
添加数据库索引以优化查询性能

该脚本为 UI 任务相关的表添加索引，改善常用查询的性能。
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, Index
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.core.database import Base
from app.models.ui_task import UITask, UIScenario, UICase, UIStep


def create_indexes():
    """创建数据库索引"""

    settings = get_settings()
    database_url = settings.DATABASE_URL

    print(f"连接到数据库: {database_url}")

    # 创建引擎
    engine = create_engine(database_url)

    # 定义要添加的索引
    indexes = [
        # UITask 表索引
        Index('ix_ui_tasks_project_id', UITask.project_id),
        Index('ix_ui_tasks_created_by', UITask.created_by),
        Index('ix_ui_tasks_created_at', UITask.created_at),

        # UIScenario 表索引
        Index('ix_ui_scenarios_task_id', UIScenario.task_id),
        Index('ix_ui_scenarios_project_id', UIScenario.project_id),
        Index('ix_ui_scenarios_created_by', UIScenario.created_by),
        Index('ix_ui_scenarios_execution_order', UIScenario.execution_order),

        # UICase 表索引
        Index('ix_ui_test_cases_scenario_id', UICase.scenario_id),
        Index('ix_ui_test_cases_project_id', UICase.project_id),
        Index('ix_ui_test_cases_created_by', UICase.created_by),
        Index('ix_ui_test_cases_priority', UICase.priority),

        # UIStep 表索引
        Index('ix_ui_test_steps_case_id', UIStep.case_id),
        Index('ix_ui_test_steps_scenario_id', UIStep.scenario_id),
        Index('ix_ui_test_steps_task_id', UIStep.task_id),
        Index('ix_ui_test_steps_step_order', UIStep.step_order),
        Index('ix_ui_test_steps_enabled', UIStep.enabled),
    ]

    print("\n准备创建以下索引:")
    for idx in indexes:
        print(f"  - {idx.name}")

    # 创建索引
    print("\n开始创建索引...")
    for idx in indexes:
        try:
            idx.create(engine, checkfirst=True)
            print(f"✓ 索引 {idx.name} 创建成功")
        except Exception as e:
            print(f"✗ 索引 {idx.name} 创建失败: {e}")

    print("\n索引创建完成!")

    # 验证索引
    print("\n验证索引...")
    inspector = engine.dialect.get_inspector(engine)
    for table_name in ['ui_tasks', 'ui_scenarios', 'ui_test_cases', 'ui_test_steps']:
        indexes_info = inspector.get_indexes(table_name)
        print(f"\n{table_name} 表的索引:")
        for idx_info in indexes_info:
            print(f"  - {idx_info['name']}: {idx_info['column_names']}")


if __name__ == "__main__":
    create_indexes()
