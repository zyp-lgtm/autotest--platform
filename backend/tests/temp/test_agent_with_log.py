#!/usr/bin/env python3
"""完整测试 Agent 执行流程并显示详细日志"""
import sys
import os
import uuid
import asyncio
import logging

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.ui_task import UITask
from app.services.execution.executor import TaskExecutor
from app.schemas.execution import ExecutionRequest

# 配置日志输出到文件和终端
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/test_agent.log')
    ]
)

async def test_with_full_log():
    """测试并保存完整日志"""
    db = Session(engine)

    try:
        task_id = uuid.UUID("190d5cd7-55a4-4649-9248-9e26de4f33f8")

        request = ExecutionRequest(
            task_id=task_id,
            execution_config={},
            browser_config={"use_agent": True, "headless": False},
            environment="production"
        )

        executor = TaskExecutor(db)

        print("=" * 60)
        print("Agent 执行测试（详细日志）")
        print("=" * 60)

        result = await executor.execute_task(request)

        print(f"\n最终结果:")
        print(f"  模式: {result.execution_mode}")
        print(f"  状态: {result.status}")
        print(f"  结果: {result.result}")
        print(f"  总步骤: {result.total_steps}")
        print(f"  通过: {result.passed_steps}")
        print(f"  失败: {result.failed_steps}")
        print(f"  错误: {result.error_message}")

    finally:
        db.close()

    print("\n完整日志已保存到: /tmp/test_agent.log")
    print("查看日志: cat /tmp/test_agent.log | grep -E '(场景|步骤|Agent)'")

if __name__ == "__main__":
    asyncio.run(test_with_full_log())
