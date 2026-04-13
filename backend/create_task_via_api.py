#!/usr/bin/env python3
"""通过 API 创建混合结果测试任务"""
import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8000/api/v1"

def api_request(method, endpoint, data=None, token=None, is_form=False, query_params=None):
    """统一的 API 请求函数"""
    url = f"{BASE_URL}{endpoint}"

    # 添加查询参数
    if query_params:
        query_string = urllib.parse.urlencode(query_params)
        url = f"{url}?{query_string}"

    if is_form:
        # 表单数据
        body = urllib.parse.urlencode(data).encode('utf-8')
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        # JSON 数据
        body = json.dumps(data).encode('utf-8') if data else None
        headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            if response_data:
                return json.loads(response_data)
            return {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
        print(f"HTTP Error {e.code}: {error_body[:200]}")
        return None
    except Exception as e:
        print(f"Request Error: {e}")
        return None

def login():
    """登录获取 token"""
    print("1. 登录...")
    result = api_request("POST", "/auth/login",
                        data={"username": "demo", "password": "demo123"},
                        is_form=True)
    if result and "access_token" in result:
        print("   ✓ 登录成功")
        return result["access_token"]
    else:
        print("   ✗ 登录失败")
        return None

def get_keywords(token):
    """获取所有关键字"""
    print("\n2. 获取关键字列表...")
    result = api_request("GET", "/ui/keywords", token=token)

    if result:
        keywords = result if isinstance(result, list) else result.get("items", [])
        keyword_map = {kw["name"]: kw for kw in keywords}
        print(f"   ✓ 获取到 {len(keywords)} 个关键字")
        return keyword_map
    else:
        print("   ✗ 获取关键字失败")
        return {}

def get_project_id(token):
    """获取测试项目 ID（使用现有项目）"""
    print("\n3. 获取测试项目...")

    # 尝试获取任务列表来推断项目 ID
    result = api_request("GET", "/ui/tasks", token=token)

    if result and isinstance(result, list) and len(result) > 0:
        # 使用第一个任务的项目 ID
        project_id = result[0].get("project_id")
        if project_id:
            print(f"   ✓ 使用现有项目: {project_id}")
            return project_id

    # 如果没有任务，使用默认 UUID
    print("   使用默认测试项目 ID")
    return "00000000-0000-0000-0000-000000000001"

def create_task(token, project_id):
    """创建测试任务"""
    print("\n4. 创建测试任务...")
    result = api_request("POST", "/ui/tasks", token=token,
                        query_params={"project_id": project_id},
                        data={
                            "name": "混合结果测试（成功+失败）",
                            "description": "测试 Agent 执行模式下的混合场景"
                        })

    if result and "id" in result:
        print(f"   ✓ 任务创建成功: {result['id']}")
        print(f"   任务名称: {result['name']}")
        return result["id"]
    else:
        print("   ✗ 任务创建失败")
        return None

def create_scenario(token, task_id):
    """创建测试场景"""
    print("\n5. 创建测试场景...")
    result = api_request("POST", "/ui/scenarios", token=token,
                        data={
                            "name": "混合结果场景",
                            "description": "包含成功和失败步骤的测试场景",
                            "task_id": task_id
                        })

    if result and "id" in result:
        scenario_id = result["id"]
        print(f"   ✓ 场景创建成功: {scenario_id}")
        print(f"   场景名称: {result['name']}")

        # 更新任务的 scenario_ids
        api_request("PUT", f"/ui/tasks/{task_id}", token=token,
                   data={"scenario_ids": [scenario_id]})
        print(f"   ✓ 任务 scenario_ids 已更新")

        return scenario_id
    else:
        print("   ✗ 场景创建失败")
        return None

def create_case(token, scenario_id):
    """创建测试用例"""
    print("\n6. 创建测试用例...")
    result = api_request("POST", "/ui/testcases", token=token,
                        data={
                            "name": "混合结果用例",
                            "description": "测试 continue_on_failure 参数",
                            "scenario_id": scenario_id
                        })

    if result and "id" in result:
        case_id = result["id"]
        print(f"   ✓ 用例创建成功: {case_id}")
        print(f"   用例名称: {result['name']}")

        # 更新场景的 case_ids
        api_request("PUT", f"/ui/scenarios/{scenario_id}", token=token,
                   data={"case_ids": [case_id]})
        print(f"   ✓ 场景 case_ids 已更新")

        return case_id
    else:
        print("   ✗ 用例创建失败")
        return None

def create_steps(token, case_id, keyword_map):
    """创建测试步骤"""
    print("\n7. 创建测试步骤...")

    steps = [
        {
            "step_name": "✅ 步骤1: 打开百度首页（应该成功）",
            "step_order": 1,
            "keyword_id": keyword_map.get("NAVIGATE", {}).get("id"),
            "parameters": {"url": "https://www.baidu.com"},
            "continue_on_failure": False
        },
        {
            "step_name": "✅ 步骤2: 等待搜索框（应该成功）",
            "step_order": 2,
            "keyword_id": keyword_map.get("WAIT_FOR_ELEMENT", {}).get("id"),
            "parameters": {"selector": "#kw", "state": "attached", "timeout": 5000},
            "continue_on_failure": False
        },
        {
            "step_name": "✅ 步骤3: 输入搜索关键词（应该成功）",
            "step_order": 3,
            "keyword_id": keyword_map.get("INPUT", {}).get("id"),
            "parameters": {"selector": "#kw", "text": "Agent测试"},
            "continue_on_failure": False
        },
        {
            "step_name": "❌ 步骤4: 等待不存在的元素（应该失败）",
            "step_order": 4,
            "keyword_id": keyword_map.get("WAIT_FOR_ELEMENT", {}).get("id"),
            "parameters": {"selector": "#non-existent-element-12345", "state": "visible", "timeout": 3000},
            "continue_on_failure": True  # 失败后继续
        },
        {
            "step_name": "❌ 步骤5: 点击不存在的按钮（应该失败）",
            "step_order": 5,
            "keyword_id": keyword_map.get("CLICK", {}).get("id"),
            "parameters": {"selector": "#non-existent-button-67890"},
            "continue_on_failure": True  # 失败后继续
        },
        {
            "step_name": "✅ 步骤6: 点击真实搜索按钮（应该成功）",
            "step_order": 6,
            "keyword_id": keyword_map.get("CLICK", {}).get("id"),
            "parameters": {"selector": "#su"},
            "continue_on_failure": False
        }
    ]

    step_ids = []
    for i, step_data in enumerate(steps, 1):
        # 添加 case_id
        step_data["case_id"] = case_id

        result = api_request("POST", "/ui/steps", token=token, data=step_data)

        if result and "id" in result:
            step_ids.append(result["id"])
            print(f"   ✓ 步骤 {i} 创建成功: {result['step_name'][:40]}...")
        else:
            print(f"   ✗ 步骤 {i} 创建失败")

    # 更新用例的 step_ids
    if step_ids:
        api_request("PUT", f"/ui/testcases/{case_id}", token=token,
                   data={"step_ids": step_ids})
        print(f"   ✓ 用例 step_ids 已更新 ({len(step_ids)} 个步骤)")

    return step_ids

def main():
    print("=" * 60)
    print("通过 API 创建混合结果测试任务")
    print("=" * 60)

    # 1. 登录
    token = login()
    if not token:
        return

    # 2. 获取关键字
    keyword_map = get_keywords(token)
    if not keyword_map:
        return

    # 检查必需关键字
    required_keywords = ["NAVIGATE", "WAIT_FOR_ELEMENT", "INPUT", "CLICK"]
    missing = [kw for kw in required_keywords if kw not in keyword_map]
    if missing:
        print(f"\n✗ 缺少必需关键字: {', '.join(missing)}")
        return

    # 3. 获取项目 ID
    project_id = get_project_id(token)
    if not project_id:
        return

    # 4. 创建任务
    task_id = create_task(token, project_id)
    if not task_id:
        return

    # 5. 创建场景
    scenario_id = create_scenario(token, task_id)
    if not scenario_id:
        return

    # 6. 创建用例
    case_id = create_case(token, scenario_id)
    if not case_id:
        return

    # 7. 创建步骤
    step_ids = create_steps(token, case_id, keyword_map)

    print("\n" + "=" * 60)
    print("✅ 测试任务创建完成！")
    print("=" * 60)
    print(f"任务 ID: {task_id}")
    print(f"场景 ID: {scenario_id}")
    print(f"用例 ID: {case_id}")
    print(f"步骤数: {len(step_ids)}")
    print("\n预期执行结果:")
    print("  - 步骤 1-3: 成功")
    print("  - 步骤 4-5: 失败但 continue_on_failure=True，继续执行")
    print("  - 步骤 6: 成功或失败")
    print("\n现在可以:")
    print("  1. 访问 http://localhost:3000 查看任务")
    print("  2. 在任务列表页找到 '混合结果测试（成功+失败）'")
    print("  3. 点击执行按钮测试 Agent 执行模式")
    print("=" * 60)

if __name__ == "__main__":
    main()
