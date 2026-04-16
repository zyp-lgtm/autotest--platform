"""
导航类关键字处理器

处理页面导航、浏览器控制等操作
"""
import logging
from typing import Dict, Any
from .base_handler import BaseKeywordHandler

logger = logging.getLogger(__name__)


class NavigateHandler(BaseKeywordHandler):
    """NAVIGATE 关键字 - 导航到指定 URL"""

    def __init__(self):
        super().__init__(
            name="NAVIGATE",
            category="navigation",
            description="导航到指定的 URL",
            parameter_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "目标 URL"
                    },
                    "wait_until": {
                        "type": "string",
                        "description": "等待条件 (load/domcontentloaded/networkidle)",
                        "default": "load"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "超时时间（毫秒）",
                        "default": 30000
                    }
                },
                "required": ["url"]
            },
            examples=[
                {
                    "description": "导航到百度",
                    "parameters": {"url": "https://www.baidu.com"}
                }
            ]
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        url = parameters["url"]
        wait_until = parameters.get("wait_until", "load")
        timeout = parameters.get("timeout", 30000)

        await page.goto(url, wait_until=wait_until, timeout=timeout)

        return {"url": url, "title": await page.title()}


class GoBackHandler(BaseKeywordHandler):
    """GO_BACK 关键字 - 返回上一页"""

    def __init__(self):
        super().__init__(
            name="GO_BACK",
            category="navigation",
            description="返回浏览器上一页",
            parameter_schema={
                "type": "object",
                "properties": {}
            }
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        await page.go_back()
        return {"action": "go_back"}


class RefreshHandler(BaseKeywordHandler):
    """REFRESH 关键字 - 刷新页面"""

    def __init__(self):
        super().__init__(
            name="REFRESH",
            category="navigation",
            description="刷新当前页面",
            parameter_schema={
                "type": "object",
                "properties": {}
            }
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        await page.reload()
        return {"action": "refresh"}


# 导出所有处理器
NAVIGATION_HANDLERS = [
    NavigateHandler(),
    GoBackHandler(),
    RefreshHandler()
]
