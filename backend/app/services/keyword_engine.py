from typing import Dict, Any, Union
import httpx
import logging
import re
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
        keyword_def: Any,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行指定关键字

        Args:
            keyword_def: 关键字定义（SQLAlchemy 模型或字典）
            parameters: 关键字参数
            context: 执行上下文
        """

        # 兼容 SQLAlchemy 对象和字典
        if hasattr(keyword_def, "name"):
            # SQLAlchemy 模型
            keyword_name = keyword_def.name
            category = keyword_def.category
        else:
            # 字典
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
            if keyword_name == "打开浏览器":
                return await self._open_browser(parameters)
            elif keyword_name == "NAVIGATE":
                return await self._navigate(parameters)
            elif keyword_name == "CLICK":
                return await self._click(parameters)
            elif keyword_name == "INPUT":
                return await self._input(parameters)
            elif keyword_name == "WAIT_FOR_ELEMENT":
                return await self._wait_for_element(parameters)
            elif keyword_name == "SCREENSHOT":
                return await self._screenshot(parameters)
            elif keyword_name == "SELECT":
                return await self._select(parameters)
            elif keyword_name == "CHECKBOX":
                return await self._checkbox(parameters)
            elif keyword_name == "HOVER":
                return await self._hover(parameters)
            elif keyword_name == "ASSERT_TEXT":
                return await self._assert_text(parameters)
            elif keyword_name == "ASSERT_VISIBLE":
                return await self._assert_visible(parameters)
            elif keyword_name == "ASSERT_URL":
                return await self._assert_url(parameters)
            elif keyword_name == "ASSERT_TITLE":
                return await self._assert_title(parameters)
            elif keyword_name == "ASSERT_ELEMENT_COUNT":
                return await self._assert_element_count(parameters)
            elif keyword_name == "GET_TEXT":
                return await self._get_text(parameters)
            elif keyword_name == "SCROLL":
                return await self._scroll(parameters)
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

    async def _open_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """打开浏览器或切换浏览器类型

        支持参数:
        - browser_type: 浏览器类型（chromium/firefox/webkit，默认 chromium）
        - headless: 是否无头模式（默认 True）
        - use_local: 是否连接到本地浏览器（ws://host.docker.internal:9222）
        - remote_url: 远程浏览器 WebSocket URL（如 ws://192.168.1.100:9222）
        - viewport: 视口大小（如 {"width": 1920, "height": 1080}）
        - timeout: 默认超时时间（毫秒）
        """
        browser_type = params.get("browser_type", "chromium")
        headless = params.get("headless", True)
        use_local = params.get("use_local", False)
        remote_url = params.get("remote_url")
        viewport = params.get("viewport")
        timeout = params.get("timeout")

        # 验证浏览器类型（本地/远程连接仅支持 Chromium）
        if use_local or remote_url:
            if browser_type != "chromium":
                logger.warning(f"本地/远程连接仅支持 Chromium，自动切换类型")
                browser_type = "chromium"
            # 本地/远程连接通常使用非 headless 模式
            headless = params.get("headless", False)
        else:
            # 验证浏览器类型
            valid_types = ["chromium", "firefox", "webkit"]
            if browser_type not in valid_types:
                return {
                    "success": False,
                    "error": f"无效的浏览器类型: {browser_type}，支持的类型: {', '.join(valid_types)}"
                }

        try:
            # 构建新配置
            new_config = {
                "browser_type": browser_type,
                "headless": headless
            }

            # 添加可选配置
            if use_local:
                new_config["use_local"] = True
                logger.info("启用本地浏览器连接")

            if remote_url:
                new_config["remote_url"] = remote_url
                logger.info(f"使用远程浏览器: {remote_url}")

            if viewport:
                new_config["viewport"] = viewport

            if timeout:
                new_config["timeout"] = timeout

            # 如果浏览器已启动，检查是否需要重启
            if self.browser_manager.is_started():
                current_type = self.browser_manager.browser_type
                current_headless = self.browser_manager.headless
                current_local = getattr(self.browser_manager, 'use_local', False)
                current_remote = getattr(self.browser_manager, 'remote_url', None)

                # 检查配置是否相同
                config_changed = (
                    current_type != browser_type or
                    current_headless != headless or
                    current_local != use_local or
                    current_remote != remote_url
                )

                if not config_changed:
                    logger.info(f"浏览器已运行: {browser_type} (headless={headless})")
                    return {
                        "success": True,
                        "message": f"浏览器已在运行: {browser_type}",
                        "browser_type": browser_type,
                        "headless": headless,
                        "use_local": use_local,
                        "remote_url": remote_url
                    }

                # 配置不同，重启浏览器
                logger.info(f"浏览器配置已更改，重启浏览器")
                await self.browser_manager.restart_with_config(new_config)
            else:
                # 浏览器未启动，先更新配置再启动
                self.browser_manager.config.update(new_config)
                if "browser_type" in new_config:
                    self.browser_manager.browser_type = new_config["browser_type"]
                if "headless" in new_config:
                    self.browser_manager.headless = new_config["headless"]
                if "use_local" in new_config:
                    self.browser_manager.use_local = new_config["use_local"]
                if "remote_url" in new_config:
                    self.browser_manager.remote_url = new_config["remote_url"]
                if "viewport" in new_config:
                    self.browser_manager.viewport = new_config["viewport"]
                if "timeout" in new_config:
                    self.browser_manager.timeout = new_config["timeout"]

                await self.browser_manager.start_browser()

            # 构建返回消息
            connection_info = f"{browser_type} (headless={headless})"
            if use_local:
                connection_info = f"本地浏览器 ({connection_info})"
            elif remote_url:
                connection_info = f"远程浏览器 {remote_url} ({connection_info})"

            logger.info(f"浏览器已启动: {connection_info}")

            return {
                "success": True,
                "message": f"已启动浏览器: {connection_info}",
                "browser_type": browser_type,
                "headless": headless,
                "use_local": use_local,
                "remote_url": remote_url
            }

        except Exception as e:
            logger.error(f"打开浏览器失败: {e}")
            return {
                "success": False,
                "error": f"打开浏览器失败: {str(e)}"
            }

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
        """点击页面元素（自动等待元素存在，智能处理不可见元素）"""
        selector = params.get("selector")
        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        timeout = params.get("timeout", 5000)
        force = params.get("force", False)
        click_count = params.get("click_count", 1)

        try:
            page = await self.browser_manager.get_page()

            # 自动等待元素存在（attached）
            wait_result = await self.browser_manager.wait_for_element(
                selector=selector,
                state="attached",
                timeout=timeout
            )
            if not wait_result["success"]:
                return wait_result

            # 尝试点击元素（多次尝试）
            for attempt in range(click_count):
                try:
                    # 第一次尝试：正常点击
                    await page.click(selector, force=force, timeout=timeout)
                except Exception as click_error:
                    error_str = str(click_error)

                    # 如果是元素不可见错误，尝试强制点击
                    if "not visible" in error_str:
                        logger.warning(f"元素不可见，尝试强制点击: {selector}")
                        try:
                            await page.click(selector, force=True, timeout=timeout)
                        except Exception:
                            # 强制点击也失败，使用 JavaScript 点击
                            logger.warning(f"强制点击失败，使用 JavaScript 点击: {selector}")
                            await page.evaluate(f'document.querySelector("{selector}").click()')
                    else:
                        # 其他错误直接抛出
                        raise

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
        """在输入框中输入文本（自动等待输入框存在）"""
        selector = params.get("selector")
        text = params.get("text", "")
        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        clear_first = params.get("clear_first", True)
        timeout = params.get("timeout", 5000)

        try:
            page = await self.browser_manager.get_page()

            # 自动等待输入框存在（attached），让 Playwright 处理可编辑性检查
            wait_result = await self.browser_manager.wait_for_element(
                selector=selector,
                state="attached",
                timeout=timeout
            )
            if not wait_result["success"]:
                return wait_result

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

    # ========== 扩展 UI 关键字 ==========

    async def _select(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """选择下拉框选项（自动等待下拉框存在）"""
        selector = params.get("selector")
        value = params.get("value")
        text = params.get("text")
        timeout = params.get("timeout", 5000)

        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        if not value and not text:
            return {"success": False, "error": "需要提供 value 或 text 参数"}

        try:
            page = await self.browser_manager.get_page()

            # 自动等待下拉框存在（attached）
            wait_result = await self.browser_manager.wait_for_element(
                selector=selector,
                state="attached",
                timeout=timeout
            )
            if not wait_result["success"]:
                return wait_result

            # 获取 select 元素
            select_element = page.locator(f"select{selector}")

            # 根据选择方式
            if value:
                await select_element.select_option(value=value)
                logger.info(f"SELECT 成功: {selector} -> {value}")
            else:
                await select_element.select_option(label=text)
                logger.info(f"SELECT 成功: {selector} -> '{text}'")

            return {
                "success": True,
                "message": f"已选择下拉选项: {selector}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"选择失败: {str(e)}"
            }

    async def _checkbox(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """勾选/取消勾选复选框（自动等待复选框存在）"""
        selector = params.get("selector")
        checked = params.get("checked")
        timeout = params.get("timeout", 5000)

        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        if checked is None:
            return {"success": False, "error": "缺少必需参数: checked"}

        try:
            page = await self.browser_manager.get_page()

            # 自动等待复选框存在（attached）
            wait_result = await self.browser_manager.wait_for_element(
                selector=selector,
                state="attached",
                timeout=timeout
            )
            if not wait_result["success"]:
                return wait_result

            checkbox = page.locator(f"input[type=\"checkbox\"]{selector}")

            # 设置复选框状态
            if checked:
                await checkbox.check()
                logger.info(f"CHECKBOX 勾选成功: {selector}")
            else:
                await checkbox.uncheck()
                logger.info(f"CHECKBOX 取消勾选: {selector}")

            return {
                "success": True,
                "message": f"{'已勾选' if checked else '已取消勾选'}: {selector}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"复选框操作失败: {str(e)}"
            }

    async def _hover(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """鼠标悬停（自动等待元素存在）"""
        selector = params.get("selector")
        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        timeout = params.get("timeout", 5000)

        try:
            page = await self.browser_manager.get_page()

            # 自动等待元素存在（attached）
            wait_result = await self.browser_manager.wait_for_element(
                selector=selector,
                state="attached",
                timeout=timeout
            )
            if not wait_result["success"]:
                return wait_result

            await page.hover(selector)

            logger.info(f"HOVER 成功: {selector}")

            return {
                "success": True,
                "message": f"已悬停在: {selector}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"悬停失败: {str(e)}"
            }

    async def _assert_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言文本存在（增强版：支持正则表达式）"""
        text = params.get("text")
        if not text:
            return {"success": False, "error": "缺少必需参数: text"}

        selector = params.get("selector")
        mode = params.get("mode", "contains")  # contains, equals, regex, not_contains
        timeout = params.get("timeout", 10000)
        case_sensitive = params.get("case_sensitive", False)

        try:
            page = await self.browser_manager.get_page()
            page.set_default_timeout(timeout)

            # 获取内容
            if selector:
                # 等待元素存在
                wait_result = await self.browser_manager.wait_for_element(
                    selector=selector,
                    state="attached",
                    timeout=timeout
                )
                if not wait_result["success"]:
                    return wait_result

                element = page.locator(selector)
                content = await element.inner_text()
            else:
                # 在整个页面中查找文本
                content = await page.inner_text("body")

            # 根据模式判断
            if mode == "regex":
                # 正则表达式匹配
                flags = 0 if case_sensitive else re.IGNORECASE
                passed = bool(re.search(text, content, flags))
                match_desc = f"正则: {text}"
            elif mode == "equals":
                # 完全匹配
                if case_sensitive:
                    passed = content.strip() == text.strip()
                else:
                    passed = content.strip().lower() == text.strip().lower()
                match_desc = f"等于: '{text}'"
            elif mode == "not_contains":
                # 不包含
                if case_sensitive:
                    passed = text not in content
                else:
                    passed = text.lower() not in content.lower()
                match_desc = f"不包含: '{text}'"
            else:  # contains (default)
                # 包含
                if case_sensitive:
                    passed = text in content
                else:
                    passed = text.lower() in content.lower()
                match_desc = f"包含: '{text}'"

            # 返回结果
            if passed:
                logger.info(f"ASSERT_TEXT 通过: {match_desc}")
                return {
                    "success": True,
                    "passed": True,
                    "message": f"文本断言通过: {match_desc}"
                }
            else:
                logger.warning(f"ASSERT_TEXT 失败: {match_desc}")
                return {
                    "success": True,
                    "passed": False,
                    "message": f"文本断言失败: {match_desc}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"文本断言失败: {str(e)}"
            }

    async def _assert_visible(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言元素可见"""
        selector = params.get("selector")
        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        visible = params.get("visible", True)  # True=断言可见, False=断言不可见
        timeout = params.get("timeout", 10000)

        try:
            page = await self.browser_manager.get_page()

            # 等待元素达到指定状态
            state = "visible" if visible else "hidden"
            wait_result = await self.browser_manager.wait_for_element(
                selector=selector,
                state=state,
                timeout=timeout
            )

            passed = wait_result["success"]

            if passed:
                logger.info(f"ASSERT_VISIBLE 通过: {selector} 是 {state}")
                return {
                    "success": True,
                    "passed": True,
                    "message": f"元素可见性断言通过: {selector} 是 {state}"
                }
            else:
                logger.warning(f"ASSERT_VISIBLE 失败: {selector} 不是 {state}")
                return {
                    "success": True,
                    "passed": False,
                    "message": f"元素可见性断言失败: {selector} 不是 {state}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"可见性断言失败: {str(e)}"
            }

    async def _assert_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言当前 URL"""
        url = params.get("url")
        if not url:
            return {"success": False, "error": "缺少必需参数: url"}

        mode = params.get("mode", "contains")  # contains, equals, regex
        timeout = params.get("timeout", 10000)

        try:
            page = await self.browser_manager.get_page()

            # 立即检查当前 URL
            current_url = page.url
            passed = False

            if mode == "equals":
                passed = current_url == url
            elif mode == "regex":
                passed = bool(re.search(url, current_url))
            else:  # contains
                passed = url in current_url

            if passed:
                logger.info(f"ASSERT_URL 通过: {url}")
                return {
                    "success": True,
                    "passed": True,
                    "message": f"URL 断言通过: {url}"
                }
            else:
                logger.warning(f"ASSERT_URL 失败: 期望 '{url}', 实际 '{current_url}'")
                return {
                    "success": True,
                    "passed": False,
                    "message": f"URL 断言失败: 期望 '{url}', 实际 '{current_url}'"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"URL 断言失败: {str(e)}"
            }

    async def _assert_title(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言页面标题"""
        title = params.get("title")
        if not title:
            return {"success": False, "error": "缺少必需参数: title"}

        mode = params.get("mode", "contains")  # contains, equals, regex
        timeout = params.get("timeout", 10000)

        try:
            page = await self.browser_manager.get_page()

            # 立即检查当前标题
            current_title = await page.title()
            passed = False

            if mode == "equals":
                passed = current_title == title
            elif mode == "regex":
                passed = bool(re.search(title, current_title))
            else:  # contains
                passed = title in current_title

            if passed:
                logger.info(f"ASSERT_TITLE 通过: {title}")
                return {
                    "success": True,
                    "passed": True,
                    "message": f"标题断言通过: {title}"
                }
            else:
                logger.warning(f"ASSERT_TITLE 失败: 期望 '{title}', 实际 '{current_title}'")
                return {
                    "success": True,
                    "passed": False,
                    "message": f"标题断言失败: 期望 '{title}', 实际 '{current_title}'"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"标题断言失败: {str(e)}"
            }

    async def _assert_element_count(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言元素数量"""
        selector = params.get("selector")
        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        operator = params.get("operator", "==")  # ==, !=, >, <, >=, <=
        expected_count = params.get("count")
        if expected_count is None:
            return {"success": False, "error": "缺少必需参数: count"}

        timeout = params.get("timeout", 10000)

        try:
            page = await self.browser_manager.get_page()

            # 立即计算元素数量
            elements = await page.query_selector_all(selector)
            actual_count = len(elements)

            # 比较数量
            if operator == "==":
                passed = actual_count == expected_count
            elif operator == "!=":
                passed = actual_count != expected_count
            elif operator == ">":
                passed = actual_count > expected_count
            elif operator == "<":
                passed = actual_count < expected_count
            elif operator == ">=":
                passed = actual_count >= expected_count
            elif operator == "<=":
                passed = actual_count <= expected_count
            else:
                return {
                    "success": False,
                    "error": f"不支持的比较符: {operator}"
                }

            if passed:
                logger.info(f"ASSERT_ELEMENT_COUNT 通过: {selector} 数量 {operator} {expected_count}")
                return {
                    "success": True,
                    "passed": True,
                    "message": f"元素数量断言通过: {selector} 数量 {operator} {expected_count} (实际: {actual_count})"
                }
            else:
                logger.warning(f"ASSERT_ELEMENT_COUNT 失败: {selector} 数量 {operator} {expected_count} (实际: {actual_count})")
                return {
                    "success": True,
                    "passed": False,
                    "message": f"元素数量断言失败: {selector} 数量 {operator} {expected_count} (实际: {actual_count})"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"元素数量断言失败: {str(e)}"
            }

    async def _get_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """提取元素文本"""
        selector = params.get("selector")
        attribute = params.get("attribute")
        timeout = params.get("timeout", 5000)

        if not selector:
            return {"success": False, "error": "缺少必需参数: selector"}

        try:
            page = await self.browser_manager.get_page()
            page.set_default_timeout(timeout)

            element = page.locator(selector)

            if attribute:
                # 提取属性值
                value = await element.get_attribute(attribute)
                logger.info(f"GET_TEXT 成功: {selector}[@{attribute}] = '{value}'")
                return {
                    "success": True,
                    "text": value,
                    "message": f"已提取属性: {attribute} = '{value}'"
                }
            else:
                # 提取文本内容
                text = await element.inner_text()
                logger.info(f"GET_TEXT 成功: {selector} = '{text[:50]}...'")

                return {
                    "success": True,
                    "text": text,
                    "message": f"已提取文本: {len(text)} 字符"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"提取文本失败: {str(e)}"
            }

    async def _scroll(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """滚动页面"""
        direction = params.get("direction", "down")
        pixels = params.get("pixels", 500)
        selector = params.get("selector")
        timeout = params.get("timeout", 5000)

        try:
            page = await self.browser_manager.get_page()
            page.set_default_timeout(timeout)

            if selector:
                # 滚动到元素
                element = page.locator(selector)
                await element.scroll_into_view_if_needed()
                logger.info(f"SCROLL 成功: 滚动到元素 {selector}")
            else:
                # 按方向滚动页面
                if direction == "down":
                    await page.evaluate(f"window.scrollBy(0, {pixels})")
                elif direction == "up":
                    await page.evaluate(f"window.scrollBy(0, -{pixels})")
                elif direction == "left":
                    await page.evaluate(f"window.scrollBy(-{pixels}, 0)")
                elif direction == "right":
                    await page.evaluate(f"window.scrollBy({pixels}, 0)")
                else:
                    return {
                        "success": False,
                        "error": f"无效的滚动方向: {direction}"
                    }

                logger.info(f"SCROLL 成功: {direction} {pixels}px")

            return {
                "success": True,
                "message": f"已滚动: {direction} {pixels}px"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"滚动失败: {str(e)}"
            }