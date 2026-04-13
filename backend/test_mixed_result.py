#!/usr/bin/env python3
"""执行混合结果测试任务"""
import urllib.request
import urllib.parse
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def make_request(url, data=None, headers=None, method="GET", max_retries=3):
    """发送请求，支持重试"""
    for attempt in range(max_retries):
        try:
            if data:
                data = json.dumps(data).encode() if isinstance(data, dict) else data

            req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)

            with urllib.request.urlopen(req, timeout=10) as response:
                return json.load(response), response.status

        except urllib.error.HTTPError as e:
            if e.code == 429:  # 速率限制
                wait_time = (attempt + 1) * 5  # 5, 10, 15秒
                print(f"  ⏳ 速率限制，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            elif e.code == 500:  # 服务器错误
                error_body = e.read().decode() if hasattr(e, 'read') else str(e)
                print(f"  ✗ 服务器错误: {error_body[:200]}")
                return None, e.code
            else:
                raise

        except Exception as e:
            print(f"  ✗ 请求失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise

    return None, None

def main():
    print("=" * 60)
    print("混合结果测试 - Agent 执行模式")
    print("=" * 60)

    # 1. 登录
    print("\n1. 登录...")
    login_data = urllib.parse.urlencode({"username": "demo", "password": "demo123"}).encode()
    login_req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=login_data,
        method="POST"
    )
    login_req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(login_req) as response:
            login_result = json.load(response)
            token = login_result["access_token"]
            print(f"✓ 登录成功")
    except Exception as e:
        print(f"✗ 登录失败: {e}")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    # 2. 查询 Agent
    print("\n2. 检查 Agent 连接...")
    agents_data, status = make_request(f"{BASE_URL}/agents", headers=headers)
    if agents_data:
        print(f"✓ 发现 {agents_data['count']} 个 Agent")
        for agent_id, info in agents_data['agents'].items():
            print(f"  - {agent_id[:8]}... ({info.get('platform', 'unknown')})")
    else:
        print("✗ 无法查询 Agent 状态")
        sys.exit(1)

    # 3. 触发执行
    print("\n3. 触发任务执行...")
    task_id = "5b9427e8-37bf-45ad-a2ac-f28ebebf7559"
    execute_request = {
        "execution_config": {},
        "browser_config": {"use_agent": True, "headless": False},
        "environment": "production"
    }

    execution, status = make_request(
        f"{BASE_URL}/ui/tasks/{task_id}/execute",
        data=execute_request,
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )

    if not execution or status != 200:
        print(f"✗ 执行失败 (status: {status})")
        sys.exit(1)

    execution_id = execution['id']
    print(f"✓ 执行已创建")
    print(f"  执行ID: {execution_id}")
    print(f"  初始状态: {execution['status']}")
    print(f"  执行模式: {execution.get('execution_mode', 'unknown')}")

    # 4. 等待执行完成
    print("\n4. 等待执行完成...")
    max_wait = 120  # 最多等待 2 分钟
    start_time = time.time()
    last_status = None

    while time.time() - start_time < max_wait:
        time.sleep(2)

        status_data, _ = make_request(
            f"{BASE_URL}/ui/tasks/executions/{execution_id}",
            headers=headers
        )

        if not status_data:
            continue

        current_status = status_data['status']
        execution_mode = status_data.get('execution_mode', 'unknown')
        total_steps = status_data.get('total_steps', 0)
        passed_steps = status_data.get('passed_steps', 0)
        failed_steps = status_data.get('failed_steps', 0)
        error_msg = status_data.get('error_message', '')

        # 只在状态变化时打印
        if current_status != last_status:
            print(f"  状态: {current_status} | 模式: {execution_mode} | "
                  f"步骤: {passed_steps}/{total_steps} (失败: {failed_steps})")
            if error_msg and current_status == 'failed':
                print(f"  错误: {error_msg[:100]}")
            last_status = current_status

        if current_status in ['completed', 'failed']:
            break

    # 5. 获取最终结果
    print("\n5. 获取最终结果...")
    final_data, _ = make_request(
        f"{BASE_URL}/ui/tasks/executions/{execution_id}",
        headers=headers
    )

    if final_data:
        print()
        print("=" * 60)
        print("执行结果")
        print("=" * 60)
        print(f"执行ID: {final_data['id']}")
        print(f"任务ID: {final_data['task_id']}")
        print(f"状态: {final_data['status']}")
        print(f"结果: {final_data['result']}")
        print(f"执行模式: {final_data.get('execution_mode', 'unknown')}")
        print(f"总步骤: {final_data.get('total_steps', 0)}")
        print(f"通过: {final_data.get('passed_steps', 0)}")
        print(f"失败: {final_data.get('failed_steps', 0)}")
        print(f"跳过: {final_data.get('skipped_steps', 0)}")

        if final_data.get('error_message'):
            print(f"错误信息: {final_data['error_message']}")

        # 如果使用 Agent 模式，显示详细信息
        if final_data.get('execution_mode') == 'agent':
            print()
            print("✅ Agent 执行模式成功！")
            print()
            print("预期结果:")
            print("  - 3 个步骤成功（导航、等待搜索框、输入、点击搜索按钮）")
            print("  - 2 个步骤失败（等待不存在的元素、点击不存在的按钮）")
            print("  - 总共 6 个步骤中，4 个成功，2 个失败")
        else:
            print()
            print("⚠️  未使用 Agent 执行模式（使用直接执行）")

    print()
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
    print()
    print("下一步：")
    print("  1. 检查数据库中的步骤执行记录：")
    print("     python3 check_step_records.py")
    print()
    print("  2. 通过前端查看详细报告：")
    print(f"     访问: http://localhost:8000")
    print(f"     执行ID: {execution_id}")
    print("=" * 60)

if __name__ == "__main__":
    main()
