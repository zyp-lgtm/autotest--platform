"""
任务管理 API 集成测试

直接测试运行中的 FastAPI 服务
"""

import requests
import uuid
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


class TaskAPITester:
    """任务 API 测试器"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        # 使用固定的测试项目ID（需要在数据库中存在）
        self.project_id = "550e8400-e29b-41d4-a716-446655440000"
        self.created_task_ids = []

    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """打印测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")

    def test_health_check(self) -> bool:
        """测试健康检查"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            passed = response.status_code == 200
            self.print_result("健康检查", passed, f"状态码: {response.status_code}")
            return passed
        except Exception as e:
            self.print_result("健康检查", False, str(e))
            return False

    def test_create_task(self) -> bool:
        """测试创建任务"""
        try:
            # 首先创建一个项目（使用固定ID以便测试）
            project_id = "550e8400-e29b-41d4-a716-446655440000"

            response = requests.post(
                f"{self.base_url}/api/v1/ui/tasks/",
                params={"project_id": project_id},
                json={
                    "name": "自动化测试任务",
                    "description": "由自动化测试创建",
                    "tags": ["自动化", "API测试"]
                },
                timeout=10
            )

            passed = response.status_code == 200
            if passed:
                task = response.json()
                self.created_task_ids.append(task["id"])
                details = f"任务ID: {task['id']}, 名称: {task['name']}"
            else:
                details = f"状态码: {response.status_code}, 响应: {response.text[:100]}"

            self.print_result("创建任务", passed, details)
            return passed
        except Exception as e:
            self.print_result("创建任务", False, str(e))
            return False

    def test_list_tasks(self) -> bool:
        """测试获取任务列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/ui/tasks/",
                params={"project_id": self.project_id},
                timeout=10
            )

            passed = response.status_code == 200
            if passed:
                tasks = response.json()
                details = f"找到 {len(tasks)} 个任务"
                if tasks:
                    details += f", 第一个任务: {tasks[0]['name']}"
            else:
                details = f"状态码: {response.status_code}"

            self.print_result("获取任务列表", passed, details)
            return passed
        except Exception as e:
            self.print_result("获取任务列表", False, str(e))
            return False

    def test_get_task(self) -> bool:
        """测试获取单个任务"""
        if not self.created_task_ids:
            self.print_result("获取单个任务", False, "没有可用的任务ID")
            return False

        try:
            task_id = self.created_task_ids[0]
            response = requests.get(
                f"{self.base_url}/api/v1/ui/tasks/{task_id}",
                timeout=10
            )

            passed = response.status_code == 200
            if passed:
                task = response.json()
                details = f"任务: {task['name']}, 标签: {task.get('tags', [])}"
            else:
                details = f"状态码: {response.status_code}"

            self.print_result("获取单个任务", passed, details)
            return passed
        except Exception as e:
            self.print_result("获取单个任务", False, str(e))
            return False

    def test_update_task(self) -> bool:
        """测试更新任务"""
        if not self.created_task_ids:
            self.print_result("更新任务", False, "没有可用的任务ID")
            return False

        try:
            task_id = self.created_task_ids[0]
            response = requests.put(
                f"{self.base_url}/api/v1/ui/tasks/{task_id}",
                json={
                    "name": "更新后的任务名",
                    "description": "任务已被更新",
                    "tags": ["更新", "测试"]
                },
                timeout=10
            )

            passed = response.status_code == 200
            if passed:
                task = response.json()
                details = f"新名称: {task['name']}, 新标签: {task.get('tags', [])}"
            else:
                details = f"状态码: {response.status_code}"

            self.print_result("更新任务", passed, details)
            return passed
        except Exception as e:
            self.print_result("更新任务", False, str(e))
            return False

    def test_execute_task(self) -> bool:
        """测试执行任务"""
        if not self.created_task_ids:
            self.print_result("执行任务", False, "没有可用的任务ID")
            return False

        try:
            task_id = self.created_task_ids[0]
            response = requests.post(
                f"{self.base_url}/api/v1/ui/tasks/{task_id}/execute",
                timeout=10
            )

            passed = response.status_code == 200
            if passed:
                result = response.json()
                details = f"执行ID: {result.get('execution_id')}, 状态: {result.get('status')}"
            else:
                details = f"状态码: {response.status_code}"

            self.print_result("执行任务", passed, details)
            return passed
        except Exception as e:
            self.print_result("执行任务", False, str(e))
            return False

    def test_delete_task(self) -> bool:
        """测试删除任务"""
        if not self.created_task_ids:
            self.print_result("删除任务", False, "没有可用的任务ID")
            return False

        try:
            # 删除第一个任务
            task_id = self.created_task_ids.pop(0)
            response = requests.delete(
                f"{self.base_url}/api/v1/ui/tasks/{task_id}",
                timeout=10
            )

            passed = response.status_code == 200
            if passed:
                details = f"任务 {task_id[:8]}... 已删除"
            else:
                details = f"状态码: {response.status_code}"

            self.print_result("删除任务", passed, details)

            # 验证删除
            verify_response = requests.get(
                f"{self.base_url}/api/v1/ui/tasks/{task_id}",
                timeout=10
            )
            if verify_response.status_code == 404:
                self.print_result("验证任务已删除", True, "任务确实不存在")
            else:
                self.print_result("验证任务已删除", False, "任务仍然存在")

            return passed
        except Exception as e:
            self.print_result("删除任务", False, str(e))
            return False

    def test_404_errors(self) -> bool:
        """测试 404 错误"""
        fake_id = str(uuid.uuid4())
        all_passed = True

        # 测试获取不存在的任务
        response = requests.get(f"{self.base_url}/api/v1/ui/tasks/{fake_id}", timeout=10)
        passed = response.status_code == 404
        self.print_result("404 - 获取不存在的任务", passed)

        # 测试更新不存在的任务
        response = requests.put(
            f"{self.base_url}/api/v1/ui/tasks/{fake_id}",
            json={"name": "测试"}
        )
        passed = response.status_code == 404
        self.print_result("404 - 更新不存在的任务", passed)

        # 测试删除不存在的任务
        response = requests.delete(f"{self.base_url}/api/v1/ui/tasks/{fake_id}", timeout=10)
        passed = response.status_code == 404
        self.print_result("404 - 删除不存在的任务", passed)

        return all_passed

    def cleanup(self):
        """清理创建的任务"""
        for task_id in self.created_task_ids:
            try:
                requests.delete(f"{self.base_url}/api/v1/ui/tasks/{task_id}", timeout=5)
            except:
                pass

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("任务管理 API 集成测试")
        print("=" * 60)
        print(f"项目ID: {self.project_id}")
        print(f"API地址: {self.base_url}")
        print("=" * 60)
        print()

        results = []

        # 运行测试
        results.append(("健康检查", self.test_health_check()))
        results.append(("创建任务", self.test_create_task()))
        results.append(("获取任务列表", self.test_list_tasks()))
        results.append(("获取单个任务", self.test_get_task()))
        results.append(("更新任务", self.test_update_task()))
        results.append(("执行任务", self.test_execute_task()))
        results.append(("删除任务", self.test_delete_task()))
        results.append(("404错误处理", self.test_404_errors()))

        # 清理
        self.cleanup()

        # 打印总结
        print()
        print("=" * 60)
        print("测试结果汇总")
        print("=" * 60)

        passed_count = sum(1 for _, passed in results if passed)
        total_count = len(results)

        for test_name, passed in results:
            status = "✅" if passed else "❌"
            print(f"{status} {test_name}")

        print()
        print(f"总计: {passed_count}/{total_count} 测试通过")
        print(f"成功率: {passed_count/total_count*100:.1f}%")
        print("=" * 60)

        return passed_count == total_count


if __name__ == "__main__":
    tester = TaskAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
