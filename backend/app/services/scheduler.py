"""
任务调度器

提供定时任务调度功能，基于 cron 表达式
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from ..models.scheduled_job import ScheduledJob
from ..models.ui_task import UITask
from ..core.database import get_db

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    任务调度器

    功能：
    - 基于 cron 表达式的任务调度
    - 启用/禁用定时任务
    - 执行历史记录
    - 失败重试机制
    """

    def __init__(self):
        """初始化任务调度器"""
        self.scheduler = AsyncIOScheduler()
        self.executor_service = None
        self.running_jobs = {}

    async def start(self, executor_service=None) -> None:
        """
        启动调度器

        Args:
            executor_service: 执行器服务实例
        """
        self.executor_service = executor_service

        try:
            # 暂时禁用自动加载定时任务，避免模型映射问题
            # await self._load_scheduled_jobs()

            # 启动调度器
            self.scheduler.start()
            logger.info("✓ 任务调度器已启动")

        except Exception as e:
            logger.error(f"启动任务调度器失败: {e}", exc_info=True)
            raise

    async def stop(self) -> None:
        """停止调度器"""
        try:
            self.scheduler.shutdown()
            logger.info("✓ 任务调度器已停止")
        except Exception as e:
            logger.error(f"停止任务调度器失败: {e}")

    async def _load_scheduled_jobs(self) -> None:
        """从数据库加载定时任务"""
        try:
            db = next(get_db())

            # 获取所有启用的定时任务
            jobs = db.query(ScheduledJob).filter(
                ScheduledJob.enabled == True
            ).all()

            for job in jobs:
                await self.add_job(job)

            logger.info(f"✓ 已加载 {len(jobs)} 个定时任务")

        except Exception as e:
            logger.error(f"加载定时任务失败: {e}", exc_info=True)

    async def add_job(self, scheduled_job: ScheduledJob) -> None:
        """
        添加定时任务到调度器

        Args:
            scheduled_job: 定时任务模型实例
        """
        try:
            job_id = str(scheduled_job.id)

            # 移除已存在的任务
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

            # 解析 cron 表达式
            cron_parts = scheduled_job.cron_expression.split()
            if len(cron_parts) != 5:
                logger.error(f"无效的 cron 表达式: {scheduled_job.cron_expression}")
                return

            minute, hour, day, month, day_of_week = cron_parts

            # 创建 cron 触发器
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )

            # 添加任务
            self.scheduler.add_job(
                self._execute_scheduled_job,
                trigger=trigger,
                id=job_id,
                args=[scheduled_job],
                name=scheduled_job.name
            )

            # 更新下次运行时间
            next_run_time = self.scheduler.get_job(job_id).next_run_time
            scheduled_job.next_run_at = next_run_time

            # 存储运行中的任务信息
            self.running_jobs[job_id] = {
                "scheduled_job": scheduled_job,
                "trigger": trigger,
                "added_at": datetime.now(timezone.utc)
            }

            logger.info(f"✓ 已添加定时任务: {scheduled_job.name} (下次运行: {next_run_time})")

        except Exception as e:
            logger.error(f"添加定时任务失败: {e}", exc_info=True)

    async def remove_job(self, job_id: str) -> None:
        """
        移除定时任务

        Args:
            job_id: 任务ID
        """
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

            if job_id in self.running_jobs:
                del self.running_jobs[job_id]

            logger.info(f"✓ 已移除定时任务: {job_id}")

        except Exception as e:
            logger.error(f"移除定时任务失败: {e}", exc_info=True)

    async def _execute_scheduled_job(self, scheduled_job: ScheduledJob) -> None:
        """
        执行定时任务

        Args:
            scheduled_job: 定时任务实例
        """
        job_id = str(scheduled_job.id)
        logger.info(f"开始执行定时任务: {scheduled_job.name}")

        try:
            # 更新最后运行时间
            scheduled_job.last_run_at = datetime.now(timezone.utc)

            # 如果有执行器服务，执行任务
            if self.executor_service:
                db = next(get_db())

                try:
                    # 重置重试计数
                    scheduled_job.retry_count = 0

                    # 执行任务
                    result = await self.executor_service.execute_task(
                        task_id=str(scheduled_job.task_id),
                        user_id=str(scheduled_job.project.owner_id),
                        db=db
                    )

                    # 检查执行结果
                    if result.get("status") != "success":
                        # 执行失败，进行重试
                        await self._handle_execution_failure(scheduled_job, result.get("error"))
                    else:
                        logger.info(f"✓ 定时任务执行成功: {scheduled_job.name}")

                        # 重置重试计数
                        scheduled_job.retry_count = 0

                    # 更新下次运行时间
                    job = self.scheduler.get_job(job_id)
                    if job:
                        scheduled_job.next_run_at = job.next_run_time

                except Exception as e:
                    logger.error(f"定时任务执行异常: {e}")
                    await self._handle_execution_failure(scheduled_job, str(e))

            else:
                # 模拟执行（如果没有执行器服务）
                logger.info(f"模拟执行定时任务: {scheduled_job.name}")

        except Exception as e:
            logger.error(f"定时任务执行失败: {e}", exc_info=True)
            await self._handle_execution_failure(scheduled_job, str(e))

    async def _handle_execution_failure(self, scheduled_job: ScheduledJob, error: str) -> None:
        """
        处理执行失败和重试

        Args:
            scheduled_job: 定时任务实例
            error: 错误信息
        """
        # 增加重试计数
        scheduled_job.retry_count += 1

        if scheduled_job.retry_count < scheduled_job.max_retries:
            logger.warning(
                f"定时任务执行失败，进行重试 ({scheduled_job.retry_count}/{scheduled_job.max_retries}): "
                f"{scheduled_job.name} - {error}"
            )

            # 延迟重试
            await asyncio.sleep(2 ** scheduled_job.retry_count)  # 指数退避

            # 重新执行
            await self._execute_scheduled_job(scheduled_job)

        else:
            logger.error(
                f"定时任务执行失败，已达最大重试次数 ({scheduled_job.max_retries}): "
                f"{scheduled_job.name} - {error}"
            )

            # 重置重试计数
            scheduled_job.retry_count = 0

            # 可以选择禁用任务或发送告警
            # scheduled_job.enabled = False

    async def pause_job(self, job_id: str) -> None:
        """
        暂停定时任务

        Args:
            job_id: 任务ID
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.pause_job(job_id)
                logger.info(f"✓ 已暂停定时任务: {job_id}")

        except Exception as e:
            logger.error(f"暂停定时任务失败: {e}", exc_info=True)

    async def resume_job(self, job_id: str) -> None:
        """
        恢复定时任务

        Args:
            job_id: 任务ID
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.resume_job(job_id)
                logger.info(f"✓ 已恢复定时任务: {job_id}")

        except Exception as e:
            logger.error(f"恢复定时任务失败: {e}", exc_info=True)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            job_id: 任务ID

        Returns:
            任务状态信息
        """
        job = self.scheduler.get_job(job_id)

        if job:
            return {
                "id": job_id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "running": True
            }
        else:
            return {
                "id": job_id,
                "running": False
            }

    def get_all_jobs_status(self) -> List[Dict[str, Any]]:
        """获取所有任务状态"""
        jobs = []

        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            })

        return jobs

    def get_stats(self) -> Dict[str, Any]:
        """
        获取调度器统计信息

        Returns:
            统计信息字典
        """
        return {
            "running": self.scheduler.running,
            "total_jobs": len(self.scheduler.get_jobs()),
            "running_jobs": len(self.running_jobs)
        }


# 全局任务调度器实例
task_scheduler = TaskScheduler()
