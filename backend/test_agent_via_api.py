#!/usr/bin/env python3
"""通过 API 触发 Agent 执行测试"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. 登录获取 Token
print("=" * 60)
print("1. 登录...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "demo", "password": "demo123"}
)
login_response.raise_for_status()
token = login_response.json()["access_token"]
print(f"✓ 登录成功")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 2. 查询已注册的 Agent
print("\n2. 查询 Agent...")
agents_response = requests.get(
    f"{BASE_URL}/agents",
    headers=headers
)
agents_response.raise_for_status()
agents_data = agents_response.json()
print(f"✓ 发现 {agents_data['count']} 个 Agent")
for agent_id in agents_data['agents'].keys():
    print(f"  - {agent_id}")

# 3. 触发任务执行
print("\n3. 触发任务执行...")
task_id = "190d5cd7-55a4-4649-9248-9e26de4f33f8"
execute_request = {
    "task_id": task_id,
    "execution_config": {},
    "browser_config": {"use_agent": True, "headless": False},
    "environment": "production"
}

execute_response = requests.post(
    f"{BASE_URL}/ui/executions",
    headers=headers,
    json=execute_request
)
execute_response.raise_for_status()
execution = execute_response.json()
print(f"✓ 执行已创建")
print(f"  执行ID: {execution['id']}")
print(f"  状态: {execution['status']}")
print(f"  模式: {execution.get('execution_mode', 'unknown')}")

# 4. 等待执行完成
print("\n4. 等待执行完成...")
execution_id = execution['id']
max_wait = 120  # 最多等待 2 分钟
start_time = time.time()

while time.time() - start_time < max_wait:
    time.sleep(2)  # 每 2 秒检查一次

    status_response = requests.get(
        f"{BASE_URL}/ui/executions/{execution_id}",
        headers=headers
    )
    status_response.raise_for_status()
    status = status_response.json()

    current_status = status['status']
    result = status.get('result', 'unknown')
    execution_mode = status.get('execution_mode', 'unknown')
    total_steps = status.get('total_steps', 0)
    passed_steps = status.get('passed_steps', 0)
    failed_steps = status.get('failed_steps', 0)

    print(f"  状态: {current_status}, 结果: {result}, 模式: {execution_mode}, "
          f"步骤: {passed_steps}/{total_steps} (失败: {failed_steps})")

    if current_status in ['completed', 'failed']:
        break

# 5. 显示最终结果
print("\n5. 最终结果:")
final_response = requests.get(
    f"{BASE_URL}/ui/executions/{execution_id}",
    headers=headers
)
final_response.raise_for_status()
final = final_response.json()

print(f"  执行ID: {final['id']}")
print(f"  任务ID: {final['task_id']}")
print(f"  状态: {final['status']}")
print(f"  结果: {final['result']}")
print(f"  模式: {final.get('execution_mode', 'unknown')}")
print(f"  总步骤: {final.get('total_steps', 0)}")
print(f"  通过: {final.get('passed_steps', 0)}")
print(f"  失败: {final.get('failed_steps', 0)}")
print(f"  错误: {final.get('error_message', 'None')}")

print("\n" + "=" * 60)
if final.get('execution_mode') == 'agent':
    print("✅ Agent 执行模式成功！")
else:
    print("⚠️  未使用 Agent 执行模式")

print("=" * 60)
