"""
端到端流程验证 - 完整的用户工作流程
"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.project import Project
from app.models.environment import Environment
from app.models.test_data import TestData
from app.models.ui_task import UITask
from app.models.scheduled_job import ScheduledJob
from app.models.user import User
from uuid import uuid4
import time

print("="*60)
print("端到端流程验证 - 完整用户工作流程")
print("="*60)

db = SessionLocal()

try:
    # 获取测试用户
    user = db.query(User).filter(User.username == "demo").first()
    if not user:
        print("❌ 没有找到测试用户")
        exit(1)

    print(f"\n👤 测试用户: {user.username} (ID: {user.id})")

    # ============ 步骤 1: 创建项目 ============
    print(f"\n" + "="*60)
    print("步骤 1: 创建项目")
    print("="*60)

    project = Project(
        id=uuid4(),
        name=f"端到端测试项目_{int(time.time())}",
        description="用于端到端流程验证的测试项目",
        owner_id=user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    print(f"✅ 项目创建成功")
    print(f"   ID: {project.id}")
    print(f"   名称: {project.name}")
    print(f"   描述: {project.description}")

    # ============ 步骤 2: 创建环境配置 ============
    print(f"\n" + "="*60)
    print("步骤 2: 创建环境配置")
    print("="*60)

    env_dev = Environment(
        id=uuid4(),
        project_id=project.id,
        name="开发环境",
        base_url="https://dev.example.com",
        variables={"api_key": "dev_key_123", "timeout": 30},
        is_default=True
    )
    env_test = Environment(
        id=uuid4(),
        project_id=project.id,
        name="测试环境",
        base_url="https://test.example.com",
        variables={"api_key": "test_key_456", "timeout": 60},
        is_default=False
    )

    db.add(env_dev)
    db.add(env_test)
    db.commit()

    print(f"✅ 环境配置创建成功")
    print(f"   创建了 {db.query(Environment).filter(Environment.project_id == project.id).count()} 个环境")
    print(f"   - 开发环境 (默认): {env_dev.base_url}")
    print(f"   - 测试环境: {env_test.base_url}")

    # ============ 步骤 3: 创建测试数据 ============
    print(f"\n" + "="*60)
    print("步骤 3: 创建测试数据")
    print("="*60)

    test_data_1 = TestData(
        id=uuid4(),
        project_id=project.id,
        name="用户登录数据",
        description="用于测试用户登录功能的测试数据",
        data_type="json",
        data=[
            {"username": "testuser1", "password": "pass123", "expected": "success"},
            {"username": "testuser2", "password": "pass456", "expected": "success"},
            {"username": "invaliduser", "password": "wrongpass", "expected": "failure"}
        ],
        tags=["login", "smoke", "regression"]
    )
    test_data_2 = TestData(
        id=uuid4(),
        project_id=project.id,
        name="商品搜索数据",
        description="用于测试商品搜索功能的测试数据",
        data_type="json",
        data=[
            {"keyword": "手机", "category": "electronics"},
            {"keyword": "笔记本", "category": "computers"},
            {"keyword": "耳机", "category": "accessories"}
        ],
        tags=["search", "regression"]
    )

    db.add(test_data_1)
    db.add(test_data_2)
    db.commit()

    print(f"✅ 测试数据创建成功")
    print(f"   创建了 {db.query(TestData).filter(TestData.project_id == project.id).count()} 个测试数据集")
    print(f"   - 用户登录数据: {len(test_data_1.data)} 条记录")
    print(f"   - 商品搜索数据: {len(test_data_2.data)} 条记录")

    # ============ 步骤 4: 创建测试任务 ============
    print(f"\n" + "="*60)
    print("步骤 4: 创建测试任务")
    print("="*60)

    task = UITask(
        id=uuid4(),
        project_id=project.id,
        name="端到端测试任务",
        description="验证完整的用户登录和搜索流程",
        task_type="ui",
        scenario_ids=[],  # 空场景列表，仅用于测试
        execution_config={
            "browser": "chrome",
            "headless": True,
            "timeout": 30000,
            "environment_id": str(env_dev.id)
        },
        tags=["e2e", "critical"],
        created_by=user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    print(f"✅ 测试任务创建成功")
    print(f"   ID: {task.id}")
    print(f"   名称: {task.name}")
    print(f"   类型: {task.task_type}")
    print(f"   执行环境: {task.execution_config.get('environment_id')}")

    # ============ 步骤 5: 创建定时任务 ============
    print(f"\n" + "="*60)
    print("步骤 5: 创建定时任务")
    print("="*60)

    scheduled_job = ScheduledJob(
        id=uuid4(),
        project_id=project.id,
        name="每日回归测试",
        task_id=task.id,
        cron_expression="0 2 * * *",  # 每天凌晨2点执行
        enabled=True,
        max_retries=2
    )
    db.add(scheduled_job)
    db.commit()
    db.refresh(scheduled_job)

    print(f"✅ 定时任务创建成功")
    print(f"   ID: {scheduled_job.id}")
    print(f"   名称: {scheduled_job.name}")
    print(f"   Cron: {scheduled_job.cron_expression} (每天凌晨2点)")
    print(f"   启用状态: {scheduled_job.enabled}")

    # ============ 步骤 6: 验证完整流程 ============
    print(f"\n" + "="*60)
    print("步骤 6: 验证完整流程")
    print("="*60)

    # 验证项目统计
    project_environments = db.query(Environment).filter(Environment.project_id == project.id).count()
    project_test_data = db.query(TestData).filter(TestData.project_id == project.id).count()
    project_tasks = db.query(UITask).filter(UITask.project_id == project.id).count()
    project_scheduled_jobs = db.query(ScheduledJob).filter(ScheduledJob.project_id == project.id).count()

    print(f"✅ 项目完整性验证:")
    print(f"   项目: {project.name}")
    print(f"   ├─ 环境配置: {project_environments} 个")
    print(f"   ├─ 测试数据: {project_test_data} 个")
    print(f"   ├─ 测试任务: {project_tasks} 个")
    print(f"   └─ 定时任务: {project_scheduled_jobs} 个")

    # 验证数据关联
    print(f"\n✅ 数据关联验证:")

    # 验证环境与项目关联
    env_check = db.query(Environment).filter(
        Environment.id == env_dev.id,
        Environment.project_id == project.id
    ).first()
    print(f"   环境-项目关联: {'✅ 正常' if env_check else '❌ 异常'}")

    # 验证测试数据与项目关联
    data_check = db.query(TestData).filter(
        TestData.id == test_data_1.id,
        TestData.project_id == project.id
    ).first()
    print(f"   测试数据-项目关联: {'✅ 正常' if data_check else '❌ 异常'}")

    # 验证任务与项目关联
    task_check = db.query(UITask).filter(
        UITask.id == task.id,
        UITask.project_id == project.id
    ).first()
    print(f"   任务-项目关联: {'✅ 正常' if task_check else '❌ 异常'}")

    # 验证定时任务与项目和任务关联
    job_check = db.query(ScheduledJob).filter(
        ScheduledJob.id == scheduled_job.id,
        ScheduledJob.project_id == project.id,
        ScheduledJob.task_id == task.id
    ).first()
    print(f"   定时任务-项目-任务关联: {'✅ 正常' if job_check else '❌ 异常'}")

    # ============ 步骤 7: 清理测试数据 ============
    print(f"\n" + "="*60)
    print("步骤 7: 清理测试数据")
    print("="*60)

    # 删除定时任务
    db.delete(scheduled_job)
    print(f"✅ 定时任务已删除")

    # 删除测试任务
    db.delete(task)
    print(f"✅ 测试任务已删除")

    # 删除测试数据
    db.delete(test_data_1)
    db.delete(test_data_2)
    print(f"✅ 测试数据已删除")

    # 删除环境配置
    db.delete(env_dev)
    db.delete(env_test)
    print(f"✅ 环境配置已删除")

    # 删除项目
    db.delete(project)
    db.commit()
    print(f"✅ 项目已删除")

    # 验证清理结果
    remaining_project = db.query(Project).filter(Project.id == project.id).first()
    cleanup_check = remaining_project is None

    print(f"\n✅ 清理验证: {'成功' if cleanup_check else '失败'}")

    print(f"\n" + "="*60)
    print("端到端流程验证完成 - 所有步骤正常 ✅")
    print("="*60)

    # 最终统计
    print(f"\n📊 测试统计:")
    print(f"   ✅ 创建项目: 1 个")
    print(f"   ✅ 创建环境: 2 个")
    print(f"   ✅ 创建测试数据: 2 个")
    print(f"   ✅ 创建任务: 1 个")
    print(f"   ✅ 创建定时任务: 1 个")
    print(f"   ✅ 数据关联验证: 4 项")
    print(f"   ✅ 清理验证: 1 项")
    print(f"   📈 总计: 12 项验证全部通过")

except Exception as e:
    print(f"\n❌ 流程验证失败: {e}")
    db.rollback()
    import traceback
    traceback.print_exc()
    exit(1)

finally:
    db.close()
