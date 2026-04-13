#!/usr/bin/env python3
"""检查数据库中的步骤执行记录"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.execution import TestExecution, StepExecution

db = Session(engine)

try:
    # 查询最近的执行记录
    executions = db.query(TestExecution).order_by(TestExecution.created_at.desc()).limit(5).all()

    print("=" * 60)
    print("最近的执行记录")
    print("=" * 60)

    for exec in executions:
        print(f"\n执行ID: {exec.id}")
        print(f"  任务ID: {exec.task_id}")
        print(f"  状态: {exec.status}")
        print(f"  结果: {exec.result}")
        print(f"  执行模式: {exec.execution_mode}")
        print(f"  总步骤: {exec.total_steps}")
        print(f"  通过: {exec.passed_steps}")
        print(f"  失败: {exec.failed_steps}")

        # 查询步骤执行记录
        steps = db.query(StepExecution).order_by(StepExecution.step_order).all()

        print(f"\n  步骤记录 (共 {len(steps)} 条):")
        for step in steps:
            print(f"    [{step.step_order}] {step.step_name}")
            print(f"      - 操作: {step.keyword_name}")
            print(f"      - 状态: {step.status}")
            print(f"      - 结果: {step.result}")
            if step.error_message:
                print(f"      - 错误: {step.error_message}")
            if step.output:
                print(f"      - 输出: {step.output}")

    # 如果有任何步骤记录，显示详细信息
    all_steps = db.query(StepExecution).all()
    if all_steps:
        print("\n" + "=" * 60)
        print("所有步骤执行记录详情")
        print("=" * 60)
        for step in all_steps:
            print(f"\n步骤ID: {step.id}")
            print(f"  名称: {step.step_name}")
            print(f"  操作: {step.keyword_name}")
            print(f"  类别: {step.category}")
            print(f"  状态: {step.status}")
            print(f"  结果: {step.result}")
            print(f"  case_execution_id: {step.case_execution_id}")
            print(f"  step_id: {step.step_id}")
            print(f"  keyword_id: {step.keyword_id}")
            if step.parameters:
                print(f"  参数: {step.parameters}")
            if step.error_message:
                print(f"  错误: {step.error_message}")
            if step.output:
                print(f"  输出: {step.output}")
    else:
        print("\n" + "=" * 60)
        print("⚠️  没有找到步骤执行记录")
        print("=" * 60)

finally:
    db.close()
