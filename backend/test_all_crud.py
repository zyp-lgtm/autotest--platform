"""
测试所有模块的 CRUD 操作
"""
import urllib.request
import urllib.parse
import json
from http.cookiejar import CookieJar
from uuid import uuid4

class APITester:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.token = None

    def login(self, username="demo", password="demo123"):
        """登录"""
        login_url = f"{self.base_url}/auth/login"
        login_data = urllib.parse.urlencode({
            "username": username,
            "password": password
        }).encode()

        req = urllib.request.Request(login_url, data=login_data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        response = self.opener.open(req)
        result = json.loads(response.read().decode())
        self.token = result.get('access_token')
        print(f"✅ 登录成功")
        return True

    def get(self, endpoint):
        """GET 请求"""
        url = f"{self.base_url}/{endpoint}"
        req = urllib.request.Request(url, method="GET")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            response = self.opener.open(req)
            return json.loads(response.read().decode()), response.status
        except urllib.error.HTTPError as e:
            return {"error": e.read().decode()}, e.code
        except Exception as e:
            return {"error": str(e)}, 500

    def post(self, endpoint, data):
        """POST 请求"""
        url = f"{self.base_url}/{endpoint}"
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            response = self.opener.open(req)
            return json.loads(response.read().decode()), response.status
        except urllib.error.HTTPError as e:
            return {"error": e.read().decode()}, e.code
        except Exception as e:
            return {"error": str(e)}, 500

    def put(self, endpoint, data):
        """PUT 请求"""
        url = f"{self.base_url}/{endpoint}"
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method="PUT")
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            response = self.opener.open(req)
            return json.loads(response.read().decode()), response.status
        except urllib.error.HTTPError as e:
            return {"error": e.read().decode()}, e.code
        except Exception as e:
            return {"error": str(e)}, 500

    def delete(self, endpoint):
        """DELETE 请求"""
        url = f"{self.base_url}/{endpoint}"
        req = urllib.request.Request(url, method="DELETE")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            response = self.opener.open(req)
            return json.loads(response.read().decode()), response.status
        except urllib.error.HTTPError as e:
            return {"error": e.read().decode()}, e.code
        except Exception as e:
            return {"error": str(e)}, 500


def test_projects(tester):
    """测试项目模块 CRUD"""
    print("\n" + "="*50)
    print("测试项目模块 (Projects)")
    print("="*50)

    # GET - 获取项目列表
    print("\n1. GET /projects/")
    result, status = tester.get("projects/")
    if status == 200:
        projects = result
        print(f"   ✅ 成功 - 找到 {len(projects)} 个项目")
        if projects:
            project_id = projects[0]['id']
            project_name = projects[0]['name']
    else:
        print(f"   ❌ 失败 - {status}: {result}")
        return False

    # POST - 创建项目
    print("\n2. POST /projects/")
    import time
    new_project = {
        "name": f"测试项目_{int(time.time())}",
        "description": "用于测试的项目"
    }
    result, status = tester.post("projects/", new_project)
    if status == 200:
        new_project_id = result.get('id')
        print(f"   ✅ 成功 - 创建项目 ID: {new_project_id}")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    # PUT - 更新项目
    print("\n3. PUT /projects/{project_id}")
    update_data = {"name": "更新后的项目名"}
    result, status = tester.put(f"projects/{project_id}", update_data)
    if status == 200:
        print(f"   ✅ 成功 - 项目已更新")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    # DELETE - 删除项目
    print("\n4. DELETE /projects/{project_id}")
    result, status = tester.delete(f"projects/{new_project_id}")
    if status == 200:
        print(f"   ✅ 成功 - 项目已删除")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    return True


def test_environments(tester, project_id):
    """测试环境配置模块 CRUD"""
    print("\n" + "="*50)
    print("测试环境配置模块 (Environments)")
    print("="*50)

    # GET - 获取环境列表
    print(f"\n1. GET /environments/?project_id={project_id}")
    result, status = tester.get(f"environments/?project_id={project_id}")
    if status == 200:
        environments = result
        print(f"   ✅ 成功 - 找到 {len(environments)} 个环境")
    else:
        print(f"   ❌ 失败 - {status}: {result}")
        return False

    # POST - 创建环境
    print("\n2. POST /environments/")
    new_env = {
        "project_id": project_id,
        "name": "测试环境",
        "base_url": "https://test.example.com",
        "variables": {"api_key": "test123"},
        "is_default": False
    }
    result, status = tester.post("environments/", new_env)
    if status == 200:
        env_id = result.get('id')
        print(f"   ✅ 成功 - 创建环境 ID: {env_id}")
    else:
        print(f"   ❌ 失败 - {status}: {result}")
        return False

    # GET - 获取单个环境
    print(f"\n3. GET /environments/{env_id}")
    result, status = tester.get(f"environments/{env_id}")
    if status == 200:
        print(f"   ✅ 成功 - 环境: {result.get('name')}")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    # PUT - 更新环境
    print(f"\n4. PUT /environments/{env_id}")
    update_data = {"name": "更新后的环境"}
    result, status = tester.put(f"environments/{env_id}", update_data)
    if status == 200:
        print(f"   ✅ 成功 - 环境已更新")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    # DELETE - 删除环境
    print(f"\n5. DELETE /environments/{env_id}")
    result, status = tester.delete(f"environments/{env_id}")
    if status == 200:
        print(f"   ✅ 成功 - 环境已删除")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    return True


def test_test_data(tester, project_id):
    """测试测试数据模块 CRUD"""
    print("\n" + "="*50)
    print("测试测试数据模块 (TestData)")
    print("="*50)

    # GET - 获取测试数据列表
    print(f"\n1. GET /test-data/?project_id={project_id}")
    result, status = tester.get(f"test-data/?project_id={project_id}")
    if status == 200:
        test_data_list = result
        print(f"   ✅ 成功 - 找到 {len(test_data_list)} 个测试数据")
    else:
        print(f"   ❌ 失败 - {status}: {result}")
        return False

    # POST - 创建测试数据
    print("\n2. POST /test-data/")
    new_data = {
        "project_id": project_id,
        "name": "测试数据集",
        "description": "用于测试的数据",
        "data_type": "json",
        "data": [{"username": "test1", "password": "pass123"}],
        "tags": ["smoke", "regression"]
    }
    result, status = tester.post("test-data/", new_data)
    if status == 200:
        data_id = result.get('id')
        print(f"   ✅ 成功 - 创建测试数据 ID: {data_id}")
    else:
        print(f"   ❌ 失败 - {status}: {result}")
        return False

    # GET - 获取单个测试数据
    print(f"\n3. GET /test-data/{data_id}")
    result, status = tester.get(f"test-data/{data_id}")
    if status == 200:
        print(f"   ✅ 成功 - 测试数据: {result.get('name')}")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    # PUT - 更新测试数据
    print(f"\n4. PUT /test-data/{data_id}")
    update_data = {"name": "更新后的数据集"}
    result, status = tester.put(f"test-data/{data_id}", update_data)
    if status == 200:
        print(f"   ✅ 成功 - 测试数据已更新")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    # DELETE - 删除测试数据
    print(f"\n5. DELETE /test-data/{data_id}")
    result, status = tester.delete(f"test-data/{data_id}")
    if status == 200:
        print(f"   ✅ 成功 - 测试数据已删除")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    return True


def test_scheduled_jobs(tester, project_id):
    """测试定时任务模块 CRUD"""
    print("\n" + "="*50)
    print("测试定时任务模块 (ScheduledJobs)")
    print("="*50)

    # 先获取一个任务ID用于测试
    result, status = tester.get(f"tasks/?project_id={project_id}")
    if status != 200 or not result:
        print("   ⚠️  跳过 - 没有可用的任务")
        return True

    task_id = result[0]['id']
    print(f"   使用任务 ID: {task_id}")

    # GET - 获取定时任务列表
    print(f"\n1. GET /scheduled-jobs/?project_id={project_id}")
    result, status = tester.get(f"scheduled-jobs/?project_id={project_id}")
    if status == 200:
        jobs = result
        print(f"   ✅ 成功 - 找到 {len(jobs)} 个定时任务")
    else:
        print(f"   ❌ 失败 - {status}: {result}")
        # 即使列表获取失败，也继续测试创建操作

    # POST - 创建定时任务
    print("\n2. POST /scheduled-jobs/")
    import time
    new_job = {
        "project_id": project_id,
        "name": f"测试定时任务_{int(time.time())}",
        "task_id": task_id,
        "cron_expression": "0 9 * * *",
        "enabled": True,
        "max_retries": 3
    }
    result, status = tester.post("scheduled-jobs/", new_job)
    if status == 200:
        job_id = result.get('id')
        print(f"   ✅ 成功 - 创建定时任务 ID: {job_id}")
    else:
        print(f"   ❌ 失败 - {status}: {result}")
        return False

    # GET - 获取单个定时任务
    print(f"\n3. GET /scheduled-jobs/{job_id}")
    result, status = tester.get(f"scheduled-jobs/{job_id}")
    if status == 200:
        print(f"   ✅ 成功 - 定时任务: {result.get('name')}")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    # PUT - 更新定时任务
    print(f"\n4. PUT /scheduled-jobs/{job_id}")
    update_data = {"name": f"更新后的定时任务_{int(time.time())}"}
    result, status = tester.put(f"scheduled-jobs/{job_id}", update_data)
    if status == 200:
        print(f"   ✅ 成功 - 定时任务已更新")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    # DELETE - 删除定时任务
    print(f"\n5. DELETE /scheduled-jobs/{job_id}")
    result, status = tester.delete(f"scheduled-jobs/{job_id}")
    if status == 200:
        print(f"   ✅ 成功 - 定时任务已删除")
    else:
        print(f"   ❌ 失败 - {status}: {result}")

    return True


def main():
    """主测试函数"""
    tester = APITester()

    # 登录
    print("="*50)
    print("登录系统")
    print("="*50)
    tester.login()

    # 获取第一个项目ID用于测试
    result, _ = tester.get("projects/")
    if not result:
        print("❌ 无法获取项目列表")
        return

    project_id = result[0]['id']
    print(f"\n使用项目 ID: {project_id} 进行测试")

    # 测试各个模块
    test_projects(tester)
    test_environments(tester, project_id)
    test_test_data(tester, project_id)
    test_scheduled_jobs(tester, project_id)

    print("\n" + "="*50)
    print("测试完成")
    print("="*50)


if __name__ == "__main__":
    main()
