"""
详细测试 CRUD API 的验证错误
"""
import time
import urllib.request
import json
from http.cookiejar import CookieJar

def wait_for_rate_limit():
    """等待速率限制重置"""
    print("⏳ 等待速率限制重置 (65 秒)...")
    time.sleep(65)
    print("✅ 速率限制已重置")

def make_request(method, endpoint, data=None, token=None):
    """发送 HTTP 请求"""
    url = f"http://localhost:8000/api/v1/{endpoint}"

    if method == "GET":
        req = urllib.request.Request(url, method="GET")
    elif method == "POST":
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method="POST")
        req.add_header("Content-Type", "application/json")
    elif method == "PUT":
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method="PUT")
        req.add_header("Content-Type", "application/json")

    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        response = opener.open(req)
        return json.loads(response.read().decode()), 200, None
    except urllib.error.HTTPError as e:
        error_detail = e.read().decode()
        return {"error": error_detail}, e.code, error_detail

# 创建 cookie jar 和 opener
cookie_jar = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# 等待速率限制
wait_for_rate_limit()

# 登录
print("🔐 登录系统...")
login_data = f"username=demo&password=demo123".encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=login_data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
response = opener.open(req)
result = json.loads(response.read().decode())
token = result.get('access_token')
print("✅ 登录成功")

# 获取项目ID
print("📋 获取项目列表...")
req = urllib.request.Request("http://localhost:8000/api/v1/projects/", method="GET")
req.add_header("Authorization", f"Bearer {token}")
response = opener.open(req)
projects = json.loads(response.read().decode())
project_id = projects[0]['id']
print(f"✅ 使用项目: {projects[0]['name']} (ID: {project_id})")

# 测试不同的 POST 请求格式
print("\n" + "="*60)
print("测试 POST /environments/ 的不同格式")
print("="*60)

test_cases = [
    {
        "name": "完整格式",
        "data": {
            "project_id": project_id,
            "name": "测试环境",
            "base_url": "https://test.example.com",
            "variables": {"api_key": "test123"},
            "is_default": False
        }
    },
    {
        "name": "最小格式",
        "data": {
            "project_id": project_id,
            "name": "测试环境"
        }
    },
    {
        "name": "只有名称",
        "data": {
            "name": "测试环境"
        }
    }
]

for i, test_case in enumerate(test_cases, 1):
    print(f"\n测试 {i}: {test_case['name']}")
    print(f"请求数据: {json.dumps(test_case['data'], indent=2)}")

    result, status, error_detail = make_request("POST", "environments/", test_case['data'], token)

    if status == 200:
        print(f"✅ 成功: {result.get('name')}")
        env_id = result.get('id')
        print(f"环境 ID: {env_id}")

        # 如果成功，测试后续操作
        print(f"\n  测试 GET /environments/{env_id}")
        result, status, _ = make_request("GET", f"environments/{env_id}", token=token)
        print(f"  {'✅' if status == 200 else '❌'} GET 结果: {status}")

        if status == 200:
            print(f"\n  测试 PUT /environments/{env_id}")
            result, status, error_detail = make_request("PUT", f"environments/{env_id}", {"name": "更新环境"}, token=token)
            print(f"  {'✅' if status == 200 else '❌'} PUT 结果: {status}")
            if status != 200:
                print(f"  错误详情: {error_detail}")

            if status == 200:
                print(f"\n  测试 DELETE /environments/{env_id}")
                result, status, _ = make_request("DELETE", f"environments/{env_id}", token=token)
                print(f"  {'✅' if status == 200 else '❌'} DELETE 结果: {status}")

        break  # 如果有一个成功，就不再测试其他格式
    else:
        print(f"❌ 失败: HTTP {status}")
        print(f"错误详情: {error_detail}")

# 测试 TestData
print("\n" + "="*60)
print("测试 POST /test-data/ 的不同格式")
print("="*60)

test_data_cases = [
    {
        "name": "完整格式",
        "data": {
            "project_id": project_id,
            "name": "测试数据集",
            "description": "用于测试",
            "data_type": "json",
            "data": [{"key": "value"}],
            "tags": ["test"]
        }
    },
    {
        "name": "最小格式",
        "data": {
            "project_id": project_id,
            "name": "测试数据集",
            "data": [{"key": "value"}]
        }
    }
]

for i, test_case in enumerate(test_data_cases, 1):
    print(f"\n测试 {i}: {test_case['name']}")
    print(f"请求数据: {json.dumps(test_case['data'], indent=2)}")

    result, status, error_detail = make_request("POST", "test-data/", test_case['data'], token)

    if status == 200:
        print(f"✅ 成功: {result.get('name')}")
        data_id = result.get('id')
        print(f"数据 ID: {data_id}")
        break  # 如果有一个成功，就不再测试其他格式
    else:
        print(f"❌ 失败: HTTP {status}")
        print(f"错误详情: {error_detail}")

print("\n" + "="*60)
print("测试完成")
print("="*60)
