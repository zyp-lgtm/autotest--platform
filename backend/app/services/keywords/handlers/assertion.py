"""
断言类关键字处理器

处理各种断言操作
"""
import logging
from typing import Dict, Any, Any
from .base_handler import BaseKeywordHandler

logger = logging.getLogger(__name__)


class AssertTextHandler(BaseKeywordHandler):
    """ASSERT_TEXT 关键字 - 断言文本内容"""

    def __init__(self):
        super().__init__(
            name="ASSERT_TEXT",
            category="assertion",
            description="断言元素的文本内容",
            parameter_schema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS 选择器或 XPath"
                    },
                    "expected": {
                        "type": "string",
                        "description": "期望的文本"
                    },
                    "exact": {
                        "type": "boolean",
                        "description": "是否精确匹配",
                        "default": False
                    },
                    "timeout": {
                        "type": "number",
                        "description": "超时时间（毫秒）",
                        "default": 30000
                    }
                },
                "required": ["selector", "expected"]
            }
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        selector = parameters["selector"]
        expected = parameters["expected"]
        exact = parameters.get("exact", False)
        timeout = parameters.get("timeout", 30000)

        element = page.locator(selector)
        actual_text = await element.inner_text(timeout=timeout)

        if exact:
            assertion_result = actual_text == expected
        else:
            assertion_result = expected in actual_text

        if not assertion_result:
            raise AssertionError(f"文本断言失败: 期望 '{expected}', 实际 '{actual_text}'")

        return {"selector": selector, "expected": expected, "actual": actual_text}


class AssertVisibleHandler(BaseKeywordHandler):
    """ASSERT_VISIBLE 关键字 - 断言元素可见"""

    def __init__(self):
        super().__init__(
            name="ASSERT_VISIBLE",
            category="assertion",
            description="断言元素可见",
            parameter_schema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS 选择器或 XPath"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "超时时间（毫秒）",
                        "default": 30000
                    }
                },
                "required": ["selector"]
            }
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        selector = parameters["selector"]
        timeout = parameters.get("timeout", 30000)

        element = page.locator(selector)
        is_visible = await element.is_visible(timeout=timeout)

        if not is_visible:
            raise AssertionError(f"元素不可见: {selector}")

        return {"selector": selector, "visible": True}


class AssertURLHandler(BaseKeywordHandler):
    """ASSERT_URL 关键字 - 断言当前 URL"""

    def __init__(self):
        super().__init__(
            name="ASSERT_URL",
            category="assertion",
            description="断言当前页面 URL",
            parameter_schema={
                "type": "object",
                "properties": {
                    "expected": {
                        "type": "string",
                        "description": "期望的 URL（支持部分匹配）"
                    },
                    "exact": {
                        "type": "boolean",
                        "description": "是否精确匹配",
                        "default": False
                    }
                },
                "required": ["expected"]
            }
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        expected = parameters["expected"]
        exact = parameters.get("exact", False)

        actual_url = page.url

        if exact:
            assertion_result = actual_url == expected
        else:
            assertion_result = expected in actual_url

        if not assertion_result:
            raise AssertionError(f"URL 断言失败: 期望 '{expected}', 实际 '{actual_url}'")

        return {"expected": expected, "actual": actual_url}


class AssertTitleHandler(BaseKeywordHandler):
    """ASSERT_TITLE 关键字 - 断言页面标题"""

    def __init__(self):
        super().__init__(
            name="ASSERT_TITLE",
            category="assertion",
            description="断言页面标题",
            parameter_schema={
                "type": "object",
                "properties": {
                    "expected": {
                        "type": "string",
                        "description": "期望的标题"
                    },
                    "exact": {
                        "type": "boolean",
                        "description": "是否精确匹配",
                        "default": False
                    }
                },
                "required": ["expected"]
            }
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        expected = parameters["expected"]
        exact = parameters.get("exact", False)

        actual_title = await page.title()

        if exact:
            assertion_result = actual_title == expected
        else:
            assertion_result = expected in actual_title

        if not assertion_result:
            raise AssertionError(f"标题断言失败: 期望 '{expected}', 实际 '{actual_title}'")

        return {"expected": expected, "actual": actual_title}


# 导出所有处理器
ASSERTION_HANDLERS = [
    AssertTextHandler(),
    AssertVisibleHandler(),
    AssertURLHandler(),
    AssertTitleHandler()
]
