#!/usr/bin/env python3
"""测试任务执行流程"""
import sys
import os
import uuid
import json
import asyncio

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask
from app.services.execution.executor import TaskExecutor
from app.schemas.execution import ExecutionRequest


async def test_execution():
    """测试执行流程"""
    db = Session(engine)

    try:
        task_id = uuid.UUID("190d5cd7-55a4-4649-9248-9e26de4f33f8")

        # 创建执行请求
        request = ExecutionRequest(
            task_id=task_id,
            execution_config={},
            browser_config={"headless": False},
            environment="production"
        )

        # 创建执行器
        executor = TaskExecutor(db)

        print("开始执行任务...")
        result = await executor.execute_task(request)

        print(f"\n执行结果:")
        print(f"  状态: {result.status}")
        print(f"  结果: {result.result}")
        print(f"  总步骤数: {result.total_steps}")
        print(f"  通过步骤: {result.passed_steps}")
        print(f"  失败步骤: {result.failed_steps}")
        print(f"  错误信息: {result.error_message}")
        print(f"  执行模式: {result.execution_mode}")

        # 查询执行记录
        from app.models.execution import TestExecution
        execution = db.query(TestExecution).filter(
            TestExecution.id == result.id
        ).first()

        if execution:
            print(f"\n执行记录详情:")
            print(f"  scenario_executions 数量: {len(execution.scenario_executions)}")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_execution())
