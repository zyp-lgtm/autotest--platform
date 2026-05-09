#!/usr/bin/env python3
"""
测试 Projects API 和 Tasks API 集成
验证项目管理功能是否正常工作
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_projects_api():
    """测试 Projects API"""
    print("=" * 60)
    print("测试 Projects API")
    print("=" * 60)

    # 1. 登录
    print("\n1. 登录...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "demo", "password": "demo123"}
    )
    response.raise_for_status()
    data = response.json()
    access_token = data["access_token"]
    csrf_token = data["csrf_token"]
    print(f"✓ 登录成功")
    print(f"  Access Token: {access_token[:20]}...")
    print(f"  CSRF Token: {csrf_token[:20]}...")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-CSRF-Token": csrf_token,
        "Content-Type": "application/json"
    }

    # 2. 创建项目
    print("\n2. 创建项目...")
    project_data = {
        "name": "测试项目 A",
        "description": "用于验证项目管理功能的测试项目"
    }

    response = requests.post(
        f"{BASE_URL}/projects/",
        json=project_data,
        headers=headers
    )

    if response.status_code == 200:
        project = response.json()
        project_id = project["id"]
        print(f"✓ 项目创建成功")
        print(f"  项目 ID: {project_id}")
        print(f"  项目名称: {project['name']}")
    else:
        print(f"✗ 项目创建失败: {response.text}")
        return None

    # 3. 获取项目列表
    print("\n3. 获取项目列表...")
    response = requests.get(
        f"{BASE_URL}/projects/",
        headers=headers
    )
    response.raise_for_status()
    projects = response.json()
    print(f"✓ 获取项目列表成功，共 {len(projects)} 个项目")

    for proj in projects:
        print(f"  - {proj['name']} (ID: {proj['id']})")

    # 4. 测试 Tasks API（带 project_id）
    print(f"\n4. 测试 Tasks API（project_id={project_id}）...")
    response = requests.get(
        f"{BASE_URL}/ui/tasks",
        params={"project_id": project_id},
        headers=headers
    )

    if response.status_code == 200:
        tasks = response.json()
        print(f"✓ 获取任务列表成功，共 {len(tasks)} 个任务")
        for task in tasks:
            print(f"  - {task.get('name', 'N/A')} (ID: {task.get('id', 'N/A')})")
    else:
        print(f"✗ 获取任务列表失败: {response.text}")
        print(f"  状态码: {response.status_code}")

    # 5. 创建任务
    print(f"\n5. 创建测试任务...")
    task_data = {
        "name": "示例任务",
        "description": "用于验证任务创建功能"
    }

    response = requests.post(
        f"{BASE_URL}/ui/tasks/",
        params={"project_id": project_id},
        json=task_data,
        headers=headers
    )

    if response.status_code == 200:
        task = response.json()
        print(f"✓ 任务创建成功")
        print(f"  任务 ID: {task['id']}")
        print(f"  任务名称: {task['name']}")
        print(f"  project_id: {task.get('project_id')}")
    else:
        print(f"✗ 任务创建失败: {response.text}")
        print(f"  状态码: {response.status_code}")

    print("\n" + "=" * 60)
    print("✓ 所有测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_projects_api()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
