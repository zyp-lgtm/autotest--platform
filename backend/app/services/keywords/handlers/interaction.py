"""
交互类关键字处理器

处理点击、输入、悬停等元素交互操作
"""
import logging
from typing import Dict, Any
from .base_handler import BaseKeywordHandler

logger = logging.getLogger(__name__)


class ClickHandler(BaseKeywordHandler):
    """CLICK 关键字 - 点击元素"""

    def __init__(self):
        super().__init__(
            name="CLICK",
            category="interaction",
            description="点击指定元素",
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
                    },
                    "force": {
                        "type": "boolean",
                        "description": "强制点击（忽略元素可见性）",
                        "default": False
                    },
                    "click_count": {
                        "type": "number",
                        "description": "点击次数",
                        "default": 1
                    }
                },
                "required": ["selector"]
            },
            examples=[
                {
                    "description": "点击按钮",
                    "parameters": {"selector": "#submit-button"}
                },
                {
                    "description": "强制点击隐藏元素",
                    "parameters": {"selector": "#hidden-btn", "force": True}
                }
            ]
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        selector = parameters["selector"]
        timeout = parameters.get("timeout", 30000)
        force = parameters.get("force", False)
        click_count = parameters.get("click_count", 1)

        element = page.locator(selector)
        await element.click(timeout=timeout, force=force, click_count=click_count)

        return {"selector": selector, "clicked": True}


class DoubleClickHandler(BaseKeywordHandler):
    """DOUBLE_CLICK 关键字 - 双击元素"""

    def __init__(self):
        super().__init__(
            name="DOUBLE_CLICK",
            category="interaction",
            description="双击指定元素",
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
        await element.dblclick(timeout=timeout)

        return {"selector": selector, "double_clicked": True}


class InputHandler(BaseKeywordHandler):
    """INPUT 关键字 - 输入文本"""

    def __init__(self):
        super().__init__(
            name="INPUT",
            category="interaction",
            description="在输入框中输入文本",
            parameter_schema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS 选择器或 XPath"
                    },
                    "text": {
                        "type": "string",
                        "description": "要输入的文本"
                    },
                    "clear": {
                        "type": "boolean",
                        "description": "输入前是否清空",
                        "default": True
                    },
                    "timeout": {
                        "type": "number",
                        "description": "超时时间（毫秒）",
                        "default": 30000
                    }
                },
                "required": ["selector", "text"]
            },
            examples=[
                {
                    "description": "输入搜索关键词",
                    "parameters": {"selector": "#search-input", "text": "Playwright"}
                }
            ]
        )

    async def _execute_logic(self, context, parameters: Dict[str, Any]) -> Dict[str, Any]:
        page = context.get("page")
        if not page:
            raise ValueError("上下文中缺少 page 对象")

        selector = parameters["selector"]
        text = parameters["text"]
        clear = parameters.get("clear", True)
        timeout = parameters.get("timeout", 30000)

        element = page.locator(selector)

        if clear:
            await element.clear(timeout=timeout)

        await element.fill(text, timeout=timeout)

        return {"selector": selector, "text": text, "filled": True}


class HoverHandler(BaseKeywordHandler):
    """HOVER 关键字 - 悬停在元素上"""

    def __init__(self):
        super().__init__(
            name="HOVER",
            category="interaction",
            description="鼠标悬停在指定元素上",
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
        await element.hover(timeout=timeout)

        return {"selector": selector, "hovered": True}


class SelectHandler(BaseKeywordHandler):
    """SELECT 关键字 - 下拉框选择"""

    def __init__(self):
        super().__init__(
            name="SELECT",
            category="interaction",
            description="在下拉框中选择选项",
            parameter_schema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS 选择器或 XPath"
                    },
                    "value": {
                        "type": "string",
                        "description": "要选择的值"
                    },
                    "label": {
                        "type": "string",
                        "description": "要选择的标签"
                    },
                    "index": {
                        "type": "number",
                        "description": "要选择的索引"
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

        # 支持三种选择方式
        if "value" in parameters:
            await element.select_option(value=parameters["value"], timeout=timeout)
        elif "label" in parameters:
            await element.select_option(label=parameters["label"], timeout=timeout)
        elif "index" in parameters:
            await element.select_option(index=parameters["index"], timeout=timeout)
        else:
            raise ValueError("必须提供 value、label 或 index 参数")

        return {"selector": selector, "selected": True}


# 导出所有处理器
INTERACTION_HANDLERS = [
    ClickHandler(),
    DoubleClickHandler(),
    InputHandler(),
    HoverHandler(),
    SelectHandler()
]
