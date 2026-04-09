"""
API 关键字执行器

处理所有 API 类型的关键字（HTTP 请求、断言等）
"""
from typing import Dict, Any
import httpx
import logging
from .base_engine import BaseKeywordEngine

logger = logging.getLogger(__name__)


class APIKeywordEngine(BaseKeywordEngine):
    """API 关键字执行器"""

    async def execute(
        self,
        keyword_def: Any,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行 API 关键字

        Args:
            keyword_def: 关键字定义
            parameters: 关键字参数
            context: 执行上下文

        Returns:
            执行结果
        """
        keyword_name, category = self._extract_keyword_info(keyword_def)

        # 路由到具体的 API 关键字方法
        if keyword_name == "API_GET":
            return await self._api_get(parameters)
        elif keyword_name == "API_POST":
            return await self._api_post(parameters)
        elif keyword_name == "ASSERT_STATUS":
            return self._assert_status(parameters)
        else:
            return self._error_response(f"未知的 API 关键字: {keyword_name}")

    async def _api_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行 GET 请求"""
        try:
            async with httpx.AsyncClient() as client:
                url = params["url"]
                headers = params.get("headers", {})
                params_query = params.get("params", {})

                response = await client.get(url, headers=headers, params=params_query)

                # 判断响应类型
                content_type = response.headers.get("content-type", "")
                if content_type.startswith("application/json"):
                    body = response.json()
                else:
                    body = response.text

                return self._success_response({
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": body
                })

        except Exception as e:
            logger.error(f"GET 请求失败: {str(e)}")
            return self._error_response(f"GET 请求失败: {str(e)}")

    async def _api_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行 POST 请求"""
        try:
            async with httpx.AsyncClient() as client:
                url = params["url"]
                headers = params.get("headers", {})
                body = params.get("body", {})

                response = await client.post(url, headers=headers, json=body)

                # 判断响应类型
                content_type = response.headers.get("content-type", "")
                if content_type.startswith("application/json"):
                    body = response.json()
                else:
                    body = response.text

                return self._success_response({
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": body
                })

        except Exception as e:
            logger.error(f"POST 请求失败: {str(e)}")
            return self._error_response(f"POST 请求失败: {str(e)}")

    def _assert_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言状态码"""
        try:
            status_code = params.get("status_code")
            expected = params.get("expected")

            if not status_code:
                return self._error_response("缺少 status_code 参数")

            if status_code == expected:
                return self._success_response({
                    "message": f"状态码匹配: {status_code}"
                })
            else:
                return self._error_response(
                    f"状态码不匹配: 期望 {expected}, 实际 {status_code}"
                )

        except Exception as e:
            logger.error(f"状态码断言失败: {str(e)}")
            return self._error_response(f"状态码断言失败: {str(e)}")
