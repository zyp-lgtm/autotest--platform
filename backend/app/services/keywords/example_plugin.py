"""
示例关键字插件

演示如何使用插件化系统创建自定义关键字。

## 使用方式

1. 在应用启动时导入此插件：
   ```python
   from app.services.keywords.example_plugin import load_example_keywords
   load_example_keywords()
   ```

2. 或者使用装饰器自动注册（本模块导入时自动注册）
"""

import logging
from app.services.keywords.keyword_registry import (
    register_ui_keyword,
    register_api_keyword,
    register_custom_keyword
)

logger = logging.getLogger(__name__)


# ============================================================================
# UI 关键字示例
# ============================================================================

@register_ui_keyword(
    name="CUSTOM_NAVIGATE",
    description="自定义导航关键字 - 演示插件化系统",
    author="Platform Team",
    version="1.0.0",
    aliases=["NAV"]
)
async def custom_navigate(parameters: dict, context: dict) -> dict:
    """
    自定义导航关键字

    Args:
        parameters: {"url": "https://example.com", "timeout": 30000}
        context: {"page": page_object}

    Returns:
        {"success": True, "data": {"url": "..."}}
    """
    url = parameters.get("url")
    timeout = parameters.get("timeout", 30000)

    page = context.get("page")
    if not page:
        return {
            "success": False,
            "error": "缺少 page 对象"
        }

    try:
        await page.goto(url, timeout=timeout)
        logger.info(f"✅ 导航到: {url}")

        return {
            "success": True,
            "data": {
                "url": url,
                "title": await page.title()
            }
        }
    except Exception as e:
        logger.error(f"❌ 导航失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@register_ui_keyword(
    name="CUSTOM_CLICK",
    description="自定义点击关键字 - 支持多种定位方式",
    author="Platform Team",
    version="1.0.0"
)
async def custom_click(parameters: dict, context: dict) -> dict:
    """
    自定义点击关键字

    支持多种定位方式：id, css, xpath, text

    Args:
        parameters: {
            "locator": {"type": "id", "value": "submit-btn"},
            "timeout": 5000,
            "force": False
        }

    Returns:
        {"success": True, "data": {"clicked": True}}
    """
    locator = parameters.get("locator", {})
    timeout = parameters.get("timeout", 5000)
    force = parameters.get("force", False)

    page = context.get("page")
    if not page:
        return {
            "success": False,
            "error": "缺少 page 对象"
        }

    try:
        # 构建选择器
        locator_type = locator.get("type", "css")
        locator_value = locator.get("value", "")

        if locator_type == "id":
            selector = f"#{locator_value}"
        elif locator_type == "xpath":
            selector = f"xpath={locator_value}"
        elif locator_type == "text":
            selector = f"text={locator_value}"
        else:  # css
            selector = locator_value

        # 点击元素
        element = page.locator(selector)
        await element.click(timeout=timeout, force=force)

        logger.info(f"✅ 点击元素: {selector}")

        return {
            "success": True,
            "data": {
                "selector": selector,
                "clicked": True
            }
        }
    except Exception as e:
        logger.error(f"❌ 点击失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# API 关键字示例
# ============================================================================

@register_api_keyword(
    name="CUSTOM_API_GET",
    description="自定义 GET 请求 - 支持重试和缓存",
    author="Platform Team",
    version="1.0.0"
)
async def custom_api_get(parameters: dict, context: dict) -> dict:
    """
    自定义 API GET 请求

    Args:
        parameters: {
            "url": "https://api.example.com/data",
            "headers": {"Authorization": "Bearer xxx"},
            "retry": 3,
            "cache_ttl": 60
        }

    Returns:
        {"success": True, "data": {"status_code": 200, "body": {...}}}
    """
    import httpx
    import asyncio

    url = parameters.get("url")
    headers = parameters.get("headers", {})
    retry = parameters.get("retry", 3)
    cache_ttl = parameters.get("cache_ttl", 0)

    # 检查缓存（简化版）
    if cache_ttl > 0 and hasattr(context, "cache"):
        cached = context.cache.get(url)
        if cached:
            logger.info(f"✅ 缓存命中: {url}")
            return {"success": True, "data": cached}

    # 带重试的请求
    last_error = None
    for attempt in range(retry):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                result = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }

                # 缓存结果
                if cache_ttl > 0 and hasattr(context, "cache"):
                    context.cache.set(url, result, ttl=cache_ttl)

                logger.info(f"✅ API 请求成功: {url} (状态码: {response.status_code})")
                return {"success": True, "data": result}

        except Exception as e:
            last_error = e
            logger.warning(f"⚠️  请求失败 (尝试 {attempt + 1}/{retry}): {e}")
            if attempt < retry - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避

    return {
        "success": False,
        "error": f"请求失败（重试 {retry} 次后）: {last_error}"
    }


# ============================================================================
# 自定义关键字示例
# ============================================================================

@register_custom_keyword(
    name="DATA_TRANSFORM",
    description="数据转换 - 对测试数据进行转换",
    author="Platform Team",
    version="1.0.0",
    aliases=["TRANSFORM"]
)
async def data_transform(parameters: dict, context: dict) -> dict:
    """
    数据转换关键字

    支持多种数据转换操作：
    - json_to_xml: JSON 转 XML
    - base64_encode: Base64 编码
    - hash: 计算哈希值
    - extract: 提取字段

    Args:
        parameters: {
            "operation": "base64_encode",
            "data": "hello",
            "options": {}
        }

    Returns:
        {"success": True, "data": {"result": "aGVsbG8="}}
    """
    import base64
    import hashlib
    import json

    operation = parameters.get("operation")
    data = parameters.get("data", "")
    options = parameters.get("options", {})

    try:
        if operation == "base64_encode":
            result = base64.b64encode(data.encode()).decode()

        elif operation == "base64_decode":
            result = base64.b64decode(data).decode()

        elif operation == "hash":
            hash_type = options.get("type", "md5")
            if hash_type == "md5":
                result = hashlib.md5(data.encode()).hexdigest()
            elif hash_type == "sha256":
                result = hashlib.sha256(data.encode()).hexdigest()
            else:
                result = hashlib.sha1(data.encode()).hexdigest()

        elif operation == "extract":
            path = options.get("path", "")
            if isinstance(data, str):
                data = json.loads(data)
            # 简化版的 JSONPath
            keys = path.split(".")
            result = data
            for key in keys:
                result = result.get(key)

        elif operation == "json_to_xml":
            # 简化版 JSON 转 XML
            result = f"<root>{json.dumps(data)}</root>"

        else:
            return {
                "success": False,
                "error": f"未知操作: {operation}"
            }

        logger.info(f"✅ 数据转换: {operation} -> {result}")

        return {
            "success": True,
            "data": {"result": result}
        }

    except Exception as e:
        logger.error(f"❌ 数据转换失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@register_custom_keyword(
    name="ASSERT_CUSTOM",
    description="自定义断言 - 支持多种断言类型",
    author="Platform Team",
    version="1.0.0"
)
async def assert_custom(parameters: dict, context: dict) -> dict:
    """
    自定义断言关键字

    支持多种断言类型：
    - equals: 相等断言
    - contains: 包含断言
    - greater_than: 大于断言
    - regex: 正则匹配
    - json_schema: JSON Schema 验证

    Args:
        parameters: {
            "type": "equals",
            "actual": "hello",
            "expected": "hello"
        }

    Returns:
        {"success": True, "data": {"passed": True}}
    """
    import re

    assert_type = parameters.get("type", "equals")
    actual = parameters.get("actual")
    expected = parameters.get("expected")
    message = parameters.get("message", "")

    try:
        passed = False
        error_msg = ""

        if assert_type == "equals":
            passed = actual == expected
            error_msg = f"期望 {expected}，实际 {actual}"

        elif assert_type == "contains":
            passed = expected in actual if isinstance(actual, (str, list)) else False
            error_msg = f"期望 {actual} 包含 {expected}"

        elif assert_type == "greater_than":
            passed = actual > expected
            error_msg = f"期望 {actual} > {expected}"

        elif assert_type == "regex":
            pattern = expected
            passed = bool(re.search(pattern, actual))
            error_msg = f"期望 {actual} 匹配模式 {pattern}"

        elif assert_type == "less_than":
            passed = actual < expected
            error_msg = f"期望 {actual} < {expected}"

        else:
            return {
                "success": False,
                "error": f"未知断言类型: {assert_type}"
            }

        if passed:
            logger.info(f"✅ 断言通过: {assert_type}")
            return {
                "success": True,
                "data": {
                    "passed": True,
                    "type": assert_type
                }
            }
        else:
            logger.warning(f"❌ 断言失败: {error_msg}")
            return {
                "success": False,
                "error": error_msg or "断言失败",
                "data": {
                    "passed": False,
                    "type": assert_type
                }
            }

    except Exception as e:
        logger.error(f"❌ 断言执行失败: {e}")
        return {
            "success": False,
            "error": f"断言执行失败: {str(e)}"
        }


# ============================================================================
# 插件加载函数
# ============================================================================

def load_example_keywords():
    """
    加载示例关键字插件

    在应用启动时调用此函数来注册所有示例关键字。
    由于使用了装饰器，关键字在导入时已自动注册。
    """
    logger.info("📦 示例关键字插件已加载")
    logger.info("  - CUSTOM_NAVIGATE (别名: NAV)")
    logger.info("  - CUSTOM_CLICK")
    logger.info("  - CUSTOM_API_GET")
    logger.info("  - DATA_TRANSFORM (别名: TRANSFORM)")
    logger.info("  - ASSERT_CUSTOM")


# 自动加载（当模块被导入时）
load_example_keywords()
