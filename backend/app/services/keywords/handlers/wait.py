"""
等待类关键字处理器

处理各种等待操作
"""
import logging
from typing import Dict, Any
from .base_handler import BaseKeywordHandler

logger = logging.getLogger(__name__)


class WaitForElementHandler(BaseKeywordHandler):
    """WAIT_FOR_ELEMENT 关键字 - 等待元素出现"""

    def __init__(self):
        super().__init__(
            name="WAIT_FOR_ELEMENT",
            category="wait",
            description="等待元素出现（可指定状态）",
            parameter_schema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS 选择器或 XPath"
                    },
                    "state": {
                        "type": "string",
                        "description": "元素状态 (attached/visible/hidden)",
                        "default": "visible"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "超时时间（毫秒）",
                        "default": 30000
                    }
                },
                "required": ["selector"]
            },
            examples=[
                {
                    "description": "等待元素可见",
                    "parameters": {"selector": "#loading", "state": "hidden"}
                }
            ]
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        selector = parameters["selector"]
        state = parameters.get("state", "visible")
        timeout = parameters.get("timeout", 30000)

        element = page.locator(selector)

        # 根据状态等待
        if state == "attached":
            await element.wait_for(state="attached", timeout=timeout)
        elif state == "visible":
            await element.wait_for(state="visible", timeout=timeout)
        elif state == "hidden":
            await element.wait_for(state="hidden", timeout=timeout)
        else:
            raise ValueError(f"不支持的状态: {state}")

        return {"selector": selector, "state": state}


class SleepHandler(BaseKeywordHandler):
    """SLEEP 关键字 - 固定延迟"""

    def __init__(self):
        super().__init__(
            name="SLEEP",
            category="wait",
            description="等待指定时间（毫秒）",
            parameter_schema={
                "type": "object",
                "properties": {
                    "duration": {
                        "type": "number",
                        "description": "等待时间（毫秒）"
                    }
                },
                "required": ["duration"]
            }
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        import asyncio

        duration = parameters["duration"]
        await asyncio.sleep(duration / 1000)  # 转换为秒

        return {"duration": duration}


# 导出所有处理器
WAIT_HANDLERS = [
    WaitForElementHandler(),
    SleepHandler()
]
