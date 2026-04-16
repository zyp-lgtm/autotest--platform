"""
缓存预热模块

在应用启动时预加载常用数据到缓存中，提升首次访问性能
"""
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.keyword import Keyword
from ..models.user import User
from ..models.ui_task import UITask
from .cache import get_cache
import logging

logger = logging.getLogger(__name__)


async def warmup_cache():
    """
    预热缓存

    加载常用数据到缓存中：
    1. 关键字列表（高频访问）
    2. 关键字类别
    3. 活跃用户列表
    """
    logger.info("开始缓存预热...")
    cache = get_cache()

    try:
        db: Session = SessionLocal()

        # 1. 缓存关键字列表
        try:
            keywords = db.query(Keyword).filter(
                Keyword.is_valid == True
            ).order_by(Keyword.category, Keyword.name).all()

            keyword_list = []
            for kw in keywords:
                keyword_list.append({
                    "id": str(kw.id),
                    "name": kw.name,
                    "category": kw.category,
                    "description": kw.description,
                    "enabled": kw.is_valid
                })

            # 按类别分别缓存
            from collections import defaultdict
            keywords_by_category = defaultdict(list)
            for kw in keyword_list:
                keywords_by_category[kw['category']].append(kw)

            # 缓存所有关键字
            cache.set("keywords:all", keyword_list, ttl=600)
            logger.info(f"✅ 缓存了 {len(keyword_list)} 个关键字")

            # 缓存各类别的关键字
            for category, kws in keywords_by_category.items():
                cache.set(f"keywords:category:{category}", kws, ttl=600)
                logger.info(f"✅ 缓存了类别 '{category}' 的 {len(kws)} 个关键字")

        except Exception as e:
            logger.error(f"❌ 缓存关键字失败: {e}")

        # 2. 缓存关键字类别
        try:
            categories = db.query(Keyword.category).distinct().all()
            category_list = [cat[0] for cat in categories]
            cache.set("keywords:categories", category_list, ttl=600)
            logger.info(f"✅ 缓存了 {len(category_list)} 个关键字类别")
        except Exception as e:
            logger.error(f"❌ 缓存关键字类别失败: {e}")

        # 3. 缓存活跃用户信息
        try:
            active_users = db.query(User).filter(
                User.is_active == True
            ).limit(100).all()

            for user in active_users:
                user_info = {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "role": user.role
                }
                cache.set(f"user_info:{user.username}", user_info, ttl=600)
            logger.info(f"✅ 缓存了 {len(active_users)} 个活跃用户")
        except Exception as e:
            logger.error(f"❌ 缓存用户信息失败: {e}")

        # 4. 缓存最近的任务
        try:
            recent_tasks = db.query(UITask).order_by(
                UITask.created_at.desc()
            ).limit(50).all()

            task_list = []
            for task in recent_tasks:
                task_list.append({
                    "id": str(task.id),
                    "project_id": str(task.project_id),
                    "name": task.name,
                    "description": task.description,
                    "task_type": task.task_type,
                    "tags": list(task.tags) if task.tags else []
                })

            cache.set("tasks:recent", task_list, ttl=300)
            logger.info(f"✅ 缓存了 {len(task_list)} 个最近任务")
        except Exception as e:
            logger.error(f"❌ 缓存最近任务失败: {e}")

        db.close()

        # 输出缓存统计
        stats = cache.get_stats()
        logger.info(f"📊 缓存预热完成: {stats['size']} 项, "
                   f"命中率: {stats['hit_rate']}")

    except Exception as e:
        logger.error(f"❌ 缓存预热失败: {e}")


async def warmup_on_startup():
    """
    应用启动时调用缓存预热
    """
    import asyncio
    await asyncio.create_task(warmup_cache())
