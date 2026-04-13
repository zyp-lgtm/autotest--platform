#!/usr/bin/env python3
"""通过 API 触发 Agent 执行（使用 urllib，无需 requests）"""
import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

# 1. 登录获取 Token
print("=" * 60)
print("1. 登录...")
login_data = urllib.parse.urlencode({"username": "demo", "password": "demo123"}).encode()
login_req = urllib.request.Request(f"{BASE_URL}/auth/login", data=login_data, method="POST")
login_req.add_header("Content-Type", "application/x-www-form-urlencoded")

try:
    with urllib.request.urlopen(login_req) as response:
        login_result = json.load(response)
        token = login_result["access_token"]
        print(f"✓ 登录成功")
except Exception as e:
    print(f"✗ 登录失败: {e}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 2. 查询已注册的 Agent
print("\n2. 查询 Agent...")
agents_req = urllib.request.Request(f"{BASE_URL}/agents", headers=headers)
try:
    with urllib.request.urlopen(agents_req) as response:
        agents_data = json.load(response)
        print(f"✓ 发现 {agents_data['count']} 个 Agent")
        for agent_id in agents_data['agents'].keys():
            print(f"  - {agent_id}")
except Exception as e:
    print(f"✗ 查询 Agent 失败: {e}")
    exit(1)

# 3. 触发任务执行
print("\n3. 触发任务执行...")
task_id = "190d5cd7-55a4-4649-9248-9e26de4f33f8"
execute_request = {
    "execution_config": {},
    "browser_config": {"use_agent": True, "headless": False},
    "environment": "production"
}

execute_data = json.dumps(execute_request).encode()
execute_req = urllib.request.Request(
    f"{BASE_URL}/ui/tasks/{task_id}/execute",
    data=execute_data,
    headers={**headers, "Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(execute_req) as response:
        execution = json.load(response)
        print(f"✓ 执行已创建")
        print(f"  执行ID: {execution['id']}")
        print(f"  状态: {execution['status']}")
        print(f"  模式: {execution.get('execution_mode', 'unknown')}")
        execution_id = execution['id']
except Exception as e:
    print(f"✗ 执行失败: {e}")
    # 读取错误响应
    if hasattr(e, 'read'):
        error_body = e.read().decode()
        print(f"  错误详情: {error_body}")
    exit(1)

# 4. 等待执行完成
print("\n4. 等待执行完成...")
max_wait = 120  # 最多等待 2 分钟
start_time = time.time()

while time.time() - start_time < max_wait:
    time.sleep(2)  # 每 2 秒检查一次

    status_req = urllib.request.Request(
        f"{BASE_URL}/ui/tasks/executions/{execution_id}",
        headers=headers
    )

    try:
        with urllib.request.urlopen(status_req) as response:
            status = json.load(response)

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
    except Exception as e:
        print(f"  查询状态失败: {e}")
        break

# 5. 显示最终结果
print("\n5. 最终结果:")
final_req = urllib.request.Request(
    f"{BASE_URL}/ui/tasks/executions/{execution_id}",
    headers=headers
)

try:
    with urllib.request.urlopen(final_req) as response:
        final = json.load(response)

        print(f"  执行ID: {final['id']}")
        print(f"  任务ID: {final['task_id']}")
        print(f"  状态: {final['status']}")
        print(f"  结果: {final['result']}")
        print(f"  模式: {final.get('execution_mode', 'unknown')}")
        print(f"  总步骤: {final.get('total_steps', 0)}")
        print(f"  通过: {final.get('passed_steps', 0)}")
        print(f"  失败: {final.get('failed_steps', 0)}")
        print(f"  错误: {final.get('error_message', 'None')}")
except Exception as e:
    print(f"✗ 获取最终结果失败: {e}")

print("\n" + "=" * 60)
if final.get('execution_mode') == 'agent':
    print("✅ Agent 执行模式成功！")
else:
    print("⚠️  未使用 Agent 执行模式")
print("=" * 60)
