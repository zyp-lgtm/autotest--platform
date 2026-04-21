"""
直接测试定时任务 CRUD 操作（使用数据库）
"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.scheduled_job import ScheduledJob
from app.models.ui_task import UITask
from app.models.project import Project
from app.models.user import User
from uuid import uuid4
import time

print("="*60)
print("定时任务模块完整 CRUD 测试")
print("="*60)

db = SessionLocal()

try:
    # 获取测试用户和项目
    user = db.query(User).filter(User.username == "demo").first()
    if not user:
        print("❌ 没有找到测试用户")
        exit(1)

    # 查找有任务的项目
    projects = db.query(Project).filter(Project.owner_id == user.id).all()
    test_project = None
    test_task = None

    for project in projects:
        tasks = db.query(UITask).filter(UITask.project_id == project.id).all()
        if tasks:
            test_project = project
            test_task = tasks[0]
            break

    if not test_project or not test_task:
        print("❌ 没有找到有任务的项目")
        exit(1)

    print(f"\n✅ 找到测试数据:")
    print(f"   项目: {test_project.name} (ID: {test_project.id})")
    print(f"   任务: {test_task.name} (ID: {test_task.id})")

    # 1. 创建定时任务
    print(f"\n" + "="*60)
    print("1. 创建定时任务 (POST)")
    print("="*60)

    try:
        new_job = ScheduledJob(
            id=uuid4(),
            project_id=test_project.id,
            name=f"测试定时任务_{int(time.time())}",
            task_id=test_task.id,
            cron_expression="0 9 * * *",
            enabled=True,
            max_retries=3
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        print(f"✅ 成功创建定时任务")
        print(f"   ID: {new_job.id}")
        print(f"   名称: {new_job.name}")
        print(f"   Cron: {new_job.cron_expression}")
        print(f"   启用: {new_job.enabled}")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        exit(1)

    # 2. 获取定时任务列表
    print(f"\n" + "="*60)
    print("2. 获取定时任务列表 (GET)")
    print("="*60)

    try:
        jobs = db.query(ScheduledJob).filter(
            ScheduledJob.project_id == test_project.id
        ).all()

        print(f"✅ 成功获取定时任务列表")
        print(f"   找到 {len(jobs)} 个定时任务")
        for job in jobs:
            print(f"   - {job.name} (启用: {job.enabled})")
    except Exception as e:
        print(f"❌ 获取列表失败: {e}")
        import traceback
        traceback.print_exc()

    # 3. 获取单个定时任务
    print(f"\n" + "="*60)
    print(f"3. 获取单个定时任务 (GET /{new_job.id})")
    print("="*60)

    try:
        job = db.query(ScheduledJob).filter(
            ScheduledJob.id == new_job.id
        ).first()

        if job:
            print(f"✅ 成功获取定时任务")
            print(f"   名称: {job.name}")
            print(f"   Cron: {job.cron_expression}")
            print(f"   启用: {job.enabled}")
            print(f"   最大重试: {job.max_retries}")
        else:
            print(f"❌ 任务不存在")
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()

    # 4. 更新定时任务
    print(f"\n" + "="*60)
    print(f"4. 更新定时任务 (PUT /{new_job.id})")
    print("="*60)

    try:
        job.name = f"更新后的定时任务_{int(time.time())}"
        job.enabled = False
        job.max_retries = 5
        db.commit()
        db.refresh(job)

        print(f"✅ 成功更新定时任务")
        print(f"   新名称: {job.name}")
        print(f"   启用: {job.enabled}")
        print(f"   最大重试: {job.max_retries}")
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()

    # 5. 删除定时任务
    print(f"\n" + "="*60)
    print(f"5. 删除定时任务 (DELETE /{new_job.id})")
    print("="*60)

    try:
        job_id = new_job.id
        db.delete(new_job)
        db.commit()

        print(f"✅ 成功删除定时任务")

        # 验证删除
        deleted_job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if deleted_job:
            print(f"❌ 删除验证失败：任务仍然存在")
        else:
            print(f"✅ 删除验证成功：任务已从数据库移除")
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()

    print(f"\n" + "="*60)
    print("定时任务 CRUD 测试完成 - 所有操作正常 ✅")
    print("="*60)

finally:
    db.close()
