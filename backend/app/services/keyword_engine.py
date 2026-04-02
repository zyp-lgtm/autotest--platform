from typing import Dict, Any
import httpx


class KeywordEngine:
    """执行关键字并返回结果"""

    async def execute(
        self,
        keyword_def: Dict[str, Any],
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行指定关键字"""

        keyword_name = keyword_def.get("name")
        category = keyword_def.get("category")

        if category == "api":
            return await self._execute_api_keyword(keyword_name, parameters, context)
        elif category == "ui":
            return await self._execute_ui_keyword(keyword_name, parameters, context)
        else:
            return {"success": False, "error": f"未知类别: {category}"}

    async def _execute_api_keyword(
        self,
        keyword_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 API 测试关键字"""

        if keyword_name == "API_GET":
            return await self._api_get(parameters)
        elif keyword_name == "API_POST":
            return await self._api_post(parameters)
        elif keyword_name == "ASSERT_STATUS":
            return self._assert_status(parameters)
        else:
            return {"success": False, "error": f"未知的 API 关键字: {keyword_name}"}

    async def _api_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行 GET 请求"""
        async with httpx.AsyncClient() as client:
            url = params["url"]
            headers = params.get("headers", {})
            params_query = params.get("params", {})

            response = await client.get(url, headers=headers, params=params_query)

            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }

    async def _api_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行 POST 请求"""
        async with httpx.AsyncClient() as client:
            url = params["url"]
            headers = params.get("headers", {})
            body = params.get("body", {})

            response = await client.post(url, headers=headers, json=body)

            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }

    def _assert_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言状态码"""
        expected = params["expected_status"]
        actual = params.get("actual_status", 200)

        passed = actual == expected

        return {
            "success": passed,
            "passed": passed,
            "expected": expected,
            "actual": actual
        }

    async def _execute_ui_keyword(
        self,
        keyword_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 UI 测试关键字 (占位符，用于 Playwright)"""
        # TODO: 集成 Playwright
        return {
            "success": True,
            "message": f"UI 关键字 {keyword_name} 尚未实现"
        }