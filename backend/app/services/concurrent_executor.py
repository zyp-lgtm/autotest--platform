"""
并发执行器

支持多个任务的并发执行，提高执行效率
"""
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ConcurrentExecutor:
    """
    并发执行器

    功能：
    - 并发执行多个任务
    - 可配置并发数量
    - 正确处理并发冲突
    - 执行状态监控
    """

    def __init__(self, max_concurrent: int = 4, executor_service=None):
        """
        初始化并发执行器

        Args:
            max_concurrent: 最大并发数
            executor_service: 执行器服务实例
        """
        self.max_concurrent = max_concurrent
        self.executor_service = executor_service
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_tasks_concurrent(
        self,
        task_ids: List[str],
        user_id: str,
        db: Session,
        max_concurrent: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        并发执行多个任务

        Args:
            task_ids: 任务ID列表
            user_id: 用户ID
            db: 数据库会话
            max_concurrent: 最大并发数（覆盖默认值）

        Returns:
            执行结果统计：
            {
                "total": int,           # 总任务数
                "success": int,          # 成功数
                "failed": int,           # 失败数
                "results": list,         # 详细结果
                "execution_time": float  # 执行时间
            }
        """
        if not task_ids:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "results": [],
                "execution_time": 0
            }

        # 使用指定的并发数或默认值
        concurrent_limit = max_concurrent or self.max_concurrent
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def execute_with_semaphore(task_id: str) -> Dict[str, Any]:
            """在信号量控制下执行单个任务"""
            async with semaphore:
                try:
                    logger.info(f"开始执行任务: {task_id} (并发限制: {concurrent_limit})")

                    # 调用执行器服务执行任务
                    if self.executor_service:
                        result = await self.executor_service.execute_task(
                            task_id=task_id,
                            user_id=user_id,
                            db=db
                        )
                        return result
                    else:
                        # 模拟执行（如果没有执行器服务）
                        await asyncio.sleep(1)  # 模拟执行时间
                        return {
                            "task_id": task_id,
                            "status": "success",
                            "message": "任务执行完成"
                        }

                except Exception as e:
                    logger.error(f"执行任务 {task_id} 失败: {e}")
                    return {
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e)
                    }

        start_time = datetime.now(timezone.utc)

        try:
            # 并发执行所有任务
            results = await asyncio.gather(
                *[execute_with_semaphore(task_id) for task_id in task_ids],
                return_exceptions=True
            )

            # 处理结果
            success_count = 0
            failed_count = 0
            processed_results = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # 处理异常
                    processed_results.append({
                        "task_id": task_ids[i],
                        "status": "failed",
                        "error": str(result)
                    })
                    failed_count += 1
                else:
                    processed_results.append(result)
                    if result.get("status") == "success":
                        success_count += 1
                    else:
                        failed_count += 1

            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()

            logger.info(f"并发执行完成: 总计 {len(task_ids)} 个，成功 {success_count} 个，失败 {failed_count} 个，耗时 {execution_time:.2f} 秒")

            return {
                "total": len(task_ids),
                "success": success_count,
                "failed": failed_count,
                "results": processed_results,
                "execution_time": execution_time,
                "concurrent_limit": concurrent_limit
            }

        except Exception as e:
            logger.error(f"并发执行失败: {e}", exc_info=True)
            return {
                "total": len(task_ids),
                "success": 0,
                "failed": len(task_ids),
                "error": str(e),
                "results": [],
                "execution_time": 0
            }

    async def execute_scenarios_concurrent(
        self,
        scenario_ids: List[str],
        task_id: str,
        user_id: str,
        db: Session,
        max_concurrent: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        并发执行多个场景

        Args:
            scenario_ids: 场景ID列表
            task_id: 任务ID
            user_id: 用户ID
            db: 数据库会话
            max_concurrent: 最大并发数

        Returns:
            执行结果统计
        """
        if not scenario_ids:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "results": []
            }

        concurrent_limit = max_concurrent or self.max_concurrent
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def execute_scenario_with_semaphore(scenario_id: str) -> Dict[str, Any]:
            """在信号量控制下执行单个场景"""
            async with semaphore:
                try:
                    logger.info(f"开始执行场景: {scenario_id}")

                    # 这里应该调用场景执行逻辑
                    # 暂时模拟执行
                    await asyncio.sleep(0.5)

                    return {
                        "scenario_id": scenario_id,
                        "status": "success",
                        "message": "场景执行完成"
                    }

                except Exception as e:
                    logger.error(f"执行场景 {scenario_id} 失败: {e}")
                    return {
                        "scenario_id": scenario_id,
                        "status": "failed",
                        "error": str(e)
                    }

        try:
            results = await asyncio.gather(
                *[execute_scenario_with_semaphore(scenario_id) for scenario_id in scenario_ids],
                return_exceptions=True
            )

            success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
            failed_count = len(results) - success_count

            logger.info(f"并发执行场景完成: 总计 {len(scenario_ids)} 个，成功 {success_count} 个，失败 {failed_count} 个")

            return {
                "total": len(scenario_ids),
                "success": success_count,
                "failed": failed_count,
                "results": results,
                "concurrent_limit": concurrent_limit
            }

        except Exception as e:
            logger.error(f"并发执行场景失败: {e}", exc_info=True)
            return {
                "total": len(scenario_ids),
                "success": 0,
                "failed": len(scenario_ids),
                "error": str(e),
                "results": []
            }

    def set_max_concurrent(self, max_concurrent: int) -> None:
        """
        设置最大并发数

        Args:
            max_concurrent: 新的最大并发数
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        logger.info(f"最大并发数已设置为: {max_concurrent}")

    def get_current_concurrent(self) -> int:
        """获取当前最大并发数"""
        return self.max_concurrent

    async def get_execution_stats(self) -> Dict[str, Any]:
        """
        获取执行统计信息

        Returns:
            统计信息字典
        """
        return {
            "max_concurrent": self.max_concurrent,
            "available_slots": self.semaphore._value,
            "active_tasks": self.max_concurrent - self.semaphore._value
        }


class ConcurrentExecutionManager:
    """
    并发执行管理器

    管理多个并发执行会话
    """

    def __init__(self):
        self.executors = {}
        self.execution_history = []

    def get_executor(self, execution_id: str, max_concurrent: int = 4) -> ConcurrentExecutor:
        """
        获取或创建并发执行器

        Args:
            execution_id: 执行会话ID
            max_concurrent: 最大并发数

        Returns:
            ConcurrentExecutor 实例
        """
        if execution_id not in self.executors:
            self.executors[execution_id] = ConcurrentExecutor(max_concurrent=max_concurrent)

        return self.executors[execution_id]

    async def execute_batch(
        self,
        execution_id: str,
        task_ids: List[str],
        user_id: str,
        db: Session,
        max_concurrent: int = 4
    ) -> Dict[str, Any]:
        """
        批量执行任务

        Args:
            execution_id: 执行会话ID
            task_ids: 任务ID列表
            user_id: 用户ID
            db: 数据库会话
            max_concurrent: 最大并发数

        Returns:
            执行结果
        """
        executor = self.get_executor(execution_id, max_concurrent)
        result = await executor.execute_tasks_concurrent(task_ids, user_id, db, max_concurrent)

        # 记录执行历史
        self.execution_history.append({
            "execution_id": execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_tasks": result["total"],
            "success_tasks": result["success"],
            "failed_tasks": result["failed"],
            "execution_time": result.get("execution_time", 0)
        })

        return result

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取执行历史

        Args:
            limit: 返回记录数

        Returns:
            执行历史列表
        """
        return self.execution_history[-limit:]


# 全局并发执行管理器实例
concurrent_manager = ConcurrentExecutionManager()
