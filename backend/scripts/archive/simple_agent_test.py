#!/usr/bin/env python3
"""简化的 Agent 执行测试"""
import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """登录获取 token"""
    data = urllib.parse.urlencode({"username": "demo", "password": "demo123"}).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as response:
        result = json.load(response)
        return result["access_token"]

def check_agents(token):
    """检查 Agent 连接"""
    headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(f"{BASE_URL}/agents", headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.load(response)
            return result["count"]
    except Exception as e:
        print(f"查询 Agent 失败: {e}")
        return 0

def execute_task(token, task_id):
    """执行任务"""
    headers = {"Authorization": f"Bearer {token}"}
    data = json.dumps({
        "execution_config": {},
        "browser_config": {"use_agent": True, "headless": False},
        "environment": "production"
    }).encode()

    req = urllib.request.Request(
        f"{BASE_URL}/ui/tasks/{task_id}/execute",
        data=data,
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.load(response)
            return result
    except urllib.error.HTTPError as e:
        print(f"HTTP 错误: {e.code}")
        if hasattr(e, 'read'):
            error = e.read().decode()
            print(f"错误详情: {error[:500]}")
        return None
    except Exception as e:
        print(f"执行失败: {e}")
        return None

def main():
    print("=" * 60)
    print("Agent 执行模式简化测试")
    print("=" * 60)

    # 1. 登录
    print("\n1. 登录...")
    token = login()
    print(f"✓ 登录成功")

    # 2. 检查 Agent
    print("\n2. 检查 Agent 连接...")
    agent_count = check_agents(token)
    print(f"Agent 数量: {agent_count}")

    if agent_count == 0:
        print("⚠️  没有可用的 Agent")
        print("请先启动 Agent: cd /path/to/agent && python3 agent.py")
        return

    # 3. 执行任务（使用混合结果测试任务）
    print("\n3. 执行任务...")
    task_id = "2d2af0a3-b630-4672-b478-8d691147f617"
    print(f"任务 ID: {task_id}")

    execution = execute_task(token, task_id)
    if execution:
        print(f"✓ 执行已创建")
        print(f"  执行ID: {execution.get('id')}")
        print(f"  状态: {execution.get('status')}")
        print(f"  执行模式: {execution.get('execution_mode')}")
        print(f"  总步骤: {execution.get('total_steps', 0)}")
        print(f"  通过: {execution.get('passed_steps', 0)}")
        print(f"  失败: {execution.get('failed_steps', 0)}")

        if execution.get('execution_mode') == 'agent':
            print("\n✅ Agent 执行模式成功！")
        else:
            print(f"\n⚠️  使用了 {execution.get('execution_mode')} 模式")
    else:
        print("✗ 执行失败")

if __name__ == "__main__":
    main()
