from typing import Dict, Any
import httpx
import logging
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class KeywordEngine:
    """执行关键字并返回结果"""

    def __init__(self, browser_manager=None):
        """
        初始化关键字引擎

        Args:
            browser_manager: PlaywrightBrowser 实例（用于 UI 关键字）
        """
        self.browser_manager = browser_manager

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
        """执行 UI 测试关键字"""

        if not self.browser_manager:
            return {
                "success": False,
                "error": "浏览器管理器未初始化，请传入 PlaywrightBrowser 实例"
            }

        try:
            if keyword_name == "NAVIGATE":
                return await self._navigate(parameters)
            elif keyword_name == "CLICK":
                return await self._click(parameters)
            elif keyword_name == "INPUT":
                return await self._input(parameters)
            elif keyword_name == "WAIT_FOR_ELEMENT":
                return await self._wait_for_element(parameters)
            elif keyword_name == "SCREENSHOT":
                return await self._screenshot(parameters)
            else:
                return {"success": False, "error": f"未知的 UI 关键字: {keyword_name}"}

        except Exception as e:
            logger.error(f"执行 UI 关键字 {keyword_name} 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "keyword": keyword_name
            }

    # ========== UI 关键字实现 ==========

    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """导航到指定 URL"""
        url = params.get("url")
        if not url:
            return {"success": False, "error": "缺少必需参数: url"}

        wait_until = params.get("wait_until", "load")
        timeout = params.get("timeout", 30000)

        try:
            page = await self.browser_manager.get_page()

            # 导航到 URL
            await page.goto(
                url,
                wait_until=wait_until,
                timeout=timeout
            )

            # 获取页面标题
            title = await page.title()

            logger.info(f"导航成功: {url} - {title}")

            return {
                "success": True,
                "url": page.url,
                "title": title,
                "message": f"已导航到 {title}"
            }

        except PlaywrightTimeoutError:
            return {
                "success": False,
                "error": f"导航超时: {url}",
                "timeout": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"导航失败: {str(e)}"
            }

    async def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """点击页面元素"""
        selector = params.get("selector")
        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        timeout = params.get("timeout", 5000)
        force = params.get("force", False)
        click_count = params.get("click_count", 1)

        try:
            page = await self.browser_manager.get_page()

            # 设置超时
            page.set_default_timeout(timeout)

            # 点击元素（Playwright 自动等待）
            for _ in range(click_count):
                await page.click(selector, force=force)

            logger.info(f"点击成功: {selector}")

            return {
                "success": True,
                "message": f"已点击元素: {selector}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"点击失败: {str(e)}"
            }

    async def _input(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """在输入框中输入文本"""
        selector = params.get("selector")
        text = params.get("text", "")
        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        clear_first = params.get("clear_first", True)
        timeout = params.get("timeout", 5000)

        try:
            page = await self.browser_manager.get_page()

            # 使用 type() 方法模拟真实用户输入
            # 设置超时
            page.set_default_timeout(timeout)

            # 点击输入框激活它
            try:
                await page.click(selector, timeout=2000)
            except:
                pass  # 忽略点击失败

            # 清空（如果需要）
            if clear_first:
                try:
                    # 使用 Ctrl+A 选择全部，然后删除
                    await page.press(selector, "Control+A")
                    await page.press(selector, "Backspace")
                except:
                    pass  # 忽略清空失败

            # 输入文本（逐字符输入，模拟真实用户）
            await page.type(selector, text, delay=50)

            logger.info(f"输入成功: {selector} = '{text}'")

            return {
                "success": True,
                "message": f"已输入文本到 {selector}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"输入失败: {str(e)}"
            }

    async def _wait_for_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """等待元素出现"""
        selector = params.get("selector")
        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        state = params.get("state", "visible")
        timeout = params.get("timeout", 10000)

        try:
            page = await self.browser_manager.get_page()

            # 使用 Playwright 的 wait_for_selector
            await page.wait_for_selector(
                selector,
                state=state,
                timeout=timeout
            )

            logger.info(f"元素已就绪: {selector} (state={state})")

            return {
                "success": True,
                "message": f"元素已满足条件: {selector}"
            }

        except PlaywrightTimeoutError:
            return {
                "success": False,
                "error": f"等待超时: {selector} (state={state})",
                "timeout": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"等待失败: {str(e)}"
            }

    async def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """截取页面截图"""
        path = params.get("path")
        full_page = params.get("full_page", False)

        try:
            screenshot_path = await self.browser_manager.take_screenshot(
                path=path,
                full_page=full_page
            )

            return {
                "success": True,
                "screenshot_path": screenshot_path,
                "message": f"截图已保存: {screenshot_path}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"截图失败: {str(e)}"
            }