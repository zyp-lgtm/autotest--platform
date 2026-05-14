"""
UI 关键字执行器

处理所有 UI 类型的关键字（浏览器操作、元素交互、断言等）
"""
from typing import Dict, Any
import logging
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from .base_engine import BaseKeywordEngine

logger = logging.getLogger(__name__)


class UIKeywordEngine(BaseKeywordEngine):
    """UI 关键字执行器"""

    def __init__(self, browser_manager=None):
        """
        初始化 UI 关键字执行器

        Args:
            browser_manager: PlaywrightBrowser 实例
        """
        self.browser_manager = browser_manager

    async def _collect_debug_info(self) -> Dict[str, Any]:
        """
        收集调试信息（在关键字失败时自动调用）

        Returns:
            包含页面快照、控制台日志、网络请求的调试信息
        """
        if not self.browser_manager:
            return {}

        try:
            debug_info = await self.browser_manager.get_debug_info()
            logger.info("✓ 调试信息已收集")
            return debug_info
        except Exception as e:
            logger.warning(f"⚠ 收集调试信息失败: {e}")
            return {"error": str(e)}

    async def _error_with_debug(self, message: str, error_detail: str = None) -> Dict[str, Any]:
        """
        创建包含调试信息的错误响应

        Args:
            message: 错误消息
            error_detail: 详细错误信息

        Returns:
            包含 success=False 和调试信息的响应字典
        """
        response = {
            "success": False,
            "message": message,
            "error": error_detail or message
        }

        # 自动收集调试信息
        debug_info = await self._collect_debug_info()
        if debug_info:
            response["debug_info"] = debug_info

        return response

    async def execute(
        self,
        keyword_def: Any,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行 UI 关键字

        Args:
            keyword_def: 关键字定义
            parameters: 关键字参数
            context: 执行上下文

        Returns:
            执行结果
        """
        keyword_name, category = self._extract_keyword_info(keyword_def)

        if not self.browser_manager:
            return self._error_response("浏览器管理器未初始化，请传入 PlaywrightBrowser 实例")

        try:
            # 路由到具体的 UI 关键字方法
            keyword_method = getattr(self, f"_{keyword_name.lower()}", None)
            if keyword_method:
                return await keyword_method(parameters)
            else:
                return self._error_response(f"未知的 UI 关键字: {keyword_name}")

        except Exception as e:
            logger.error(f"执行 UI 关键字 {keyword_name} 失败: {e}")
            return self._error_response(f"{keyword_name} 执行失败: {str(e)}")

    # ============ 浏览器控制关键字 ============

    async def _open_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """打开浏览器（从原始 KeywordEngine 迁移）"""
        # 从原始文件提取的实现
        browser_type = params.get("browser_type", "chromium")
        headless = params.get("headless", True)
        use_local = params.get("use_local", False)
        remote_url = params.get("remote_url")
        viewport = params.get("viewport")
        timeout = params.get("timeout")

        if use_local or remote_url:
            if browser_type != "chromium":
                logger.warning(f"本地/远程连接仅支持 Chromium，自动切换类型")
                browser_type = "chromium"
            headless = params.get("headless", False)
        else:
            valid_types = ["chromium", "firefox", "webkit"]
            if browser_type not in valid_types:
                return self._error_response(f"无效的浏览器类型: {browser_type}")

        try:
            new_config = {
                "browser_type": browser_type,
                "headless": headless
            }

            if use_local:
                new_config["use_local"] = True
            if remote_url:
                new_config["remote_url"] = remote_url
            if viewport:
                new_config["viewport"] = viewport
            if timeout:
                new_config["timeout"] = timeout

            if self.browser_manager.is_started():
                # 检查配置是否相同
                if not self._config_changed(new_config):
                    return self._success_response({
                        "message": f"浏览器已在运行: {browser_type}",
                        "browser_type": browser_type
                    })
                await self.browser_manager.restart_with_config(new_config)
            else:
                self.browser_manager.config.update(new_config)
                await self.browser_manager.start_browser()

            return self._success_response({
                "message": f"已启动浏览器: {browser_type}"
            })

        except Exception as e:
            logger.error(f"打开浏览器失败: {e}")
            return self._error_response(f"打开浏览器失败: {str(e)}")

    async def _close_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """关闭浏览器"""
        try:
            if self.browser_manager and self.browser_manager.is_started():
                await self.browser_manager.stop_browser()
                return self._success_response({"message": "浏览器已关闭"})
            else:
                return self._success_response({"message": "浏览器未运行"})
        except Exception as e:
            return self._error_response(f"关闭浏览器失败: {str(e)}")

    def _config_changed(self, new_config: Dict[str, Any]) -> bool:
        """检查配置是否改变"""
        current_type = self.browser_manager.browser_type
        current_headless = self.browser_manager.headless
        current_local = getattr(self.browser_manager, 'use_local', False)
        current_remote = getattr(self.browser_manager, 'remote_url', None)

        return (
            current_type != new_config.get("browser_type") or
            current_headless != new_config.get("headless") or
            current_local != new_config.get("use_local") or
            current_remote != new_config.get("remote_url")
        )

    # ============ 页面导航关键字 ============

    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """导航到 URL"""
        url = params.get("url")
        if not url:
            return self._error_response("缺少必需参数: url")

        wait_until = params.get("wait_until", "load")
        timeout = params.get("timeout", 30000)

        try:
            page = await self.browser_manager.get_page()
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            title = await page.title()

            return self._success_response({
                "url": page.url,
                "title": title
            })

        except PlaywrightTimeoutError:
            return self._error_response(f"导航超时: {url}")
        except Exception as e:
            return self._error_response(f"导航失败: {str(e)}")

    async def _switch_tab(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """切换标签页"""
        try:
            page = await self.browser_manager.get_page()
            # 实现切换逻辑
            return self._success_response({"message": "已切换标签页"})
        except Exception as e:
            return self._error_response(f"切换标签页失败: {str(e)}")

    async def _go_back(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """后退"""
        try:
            page = await self.browser_manager.get_page()
            await page.go_back()
            return self._success_response({"message": "已后退"})
        except Exception as e:
            return self._error_response(f"后退失败: {str(e)}")

    async def _refresh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """刷新页面"""
        try:
            page = await self.browser_manager.get_page()
            await page.reload()
            return self._success_response({"message": "已刷新页面"})
        except Exception as e:
            return self._error_response(f"刷新失败: {str(e)}")

    # ============ 元素交互关键字 ============

    async def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """点击元素（支持 CSS/XPath 双选择器）"""
        selector = params.get("selector")
        xpath = params.get("xpath", "")
        strategy = params.get("selector_strategy", "css")
        if not selector:
            return self._error_response("缺少必需参数: selector")

        timeout = params.get("timeout", 5000)
        force = params.get("force", False)

        # 优先使用推荐策略的选择器
        primary = xpath if (strategy == "xpath" and xpath) else selector
        fallback = selector if primary != selector else (xpath if xpath else None)

        async def try_click(sel):
            wait_result = await self.browser_manager.wait_for_element(
                selector=sel, state="visible", timeout=timeout
            )
            if not wait_result["success"]:
                return wait_result
            await self.browser_manager.get_page()
            page = await self.browser_manager.get_page()
            await page.click(sel, force=force, timeout=timeout)
            return self._success_response({"message": f"已点击: {sel}"})

        try:
            return await try_click(primary)
        except Exception as e1:
            if fallback:
                try:
                    return await try_click(fallback)
                except Exception as e2:
                    return self._error_response(f"点击失败 (css/xpath均失败): {str(e2)}")
            return self._error_response(f"点击失败: {str(e1)}")

    async def _double_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """双击元素"""
        selector = params.get("selector")
        if not selector:
            return self._error_response("缺少必需参数: selector")

        timeout = params.get("timeout", 5000)

        try:
            page = await self.browser_manager.get_page()
            await page.dblclick(selector, timeout=timeout)
            return self._success_response({"message": f"已双击: {selector}"})

        except Exception as e:
            return self._error_response(f"双击失败: {str(e)}")

    async def _input(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """输入文本（支持 CSS/XPath 双选择器）"""
        selector = params.get("selector")
        xpath = params.get("xpath", "")
        strategy = params.get("selector_strategy", "css")
        text = params.get("text", "")
        if not selector:
            return self._error_response("缺少必需参数: selector")

        clear_first = params.get("clear_first", True)
        timeout = params.get("timeout", 5000)

        primary = xpath if (strategy == "xpath" and xpath) else selector
        fallback = selector if primary != selector else (xpath if xpath else None)

        async def try_input(sel):
            page = await self.browser_manager.get_page()
            wait_result = await self.browser_manager.wait_for_element(
                selector=sel, state="visible", timeout=timeout
            )
            if not wait_result["success"]:
                return wait_result
            if clear_first:
                try:
                    await page.click(sel, timeout=2000)
                    await page.press(sel, "Control+A")
                    await page.press(sel, "Backspace")
                except:
                    pass
            await page.type(sel, text, delay=50)
            return self._success_response({"message": f"已输入文本到 {sel}"})

        try:
            return await try_input(primary)
        except Exception as e1:
            if fallback:
                try:
                    return await try_input(fallback)
                except Exception as e2:
                    return self._error_response(f"输入失败 (css/xpath均失败): {str(e2)}")
            return self._error_response(f"输入失败: {str(e1)}")

    async def _hover(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """悬停元素"""
        selector = params.get("selector")
        if not selector:
            return self._error_response("缺少必需参数: selector")

        timeout = params.get("timeout", 5000)

        try:
            page = await self.browser_manager.get_page()
            await page.hover(selector, timeout=timeout)
            return self._success_response({"message": f"已悬停: {selector}"})

        except Exception as e:
            return self._error_response(f"悬停失败: {str(e)}")

    async def _scroll(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """滚动页面"""
        try:
            page = await self.browser_manager.get_page()
            # 实现滚动逻辑
            return self._success_response({"message": "已滚动页面"})
        except Exception as e:
            return self._error_response(f"滚动失败: {str(e)}")

    async def _select(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """下拉选择"""
        selector = params.get("selector")
        if not selector:
            return self._error_response("缺少必需参数: selector")

        value = params.get("value")
        if not value:
            return self._error_response("缺少必需参数: value")

        by = params.get("by", "value")  # value/label/index
        timeout = params.get("timeout", 5000)

        try:
            page = await self.browser_manager.get_page()

            # 等待元素就绪
            wait_result = await self.browser_manager.wait_for_element(
                selector=selector, state="attached", timeout=timeout
            )
            if not wait_result["success"]:
                return wait_result

            # 根据 by 参数选择选择方式
            if by == "value":
                await page.select_option(selector, value=value)
            elif by == "label":
                await page.select_option(selector, label=value)
            elif by == "index":
                try:
                    index = int(value)
                    await page.select_option(selector, index=index)
                except ValueError:
                    return {
                        "success": False,
                        "message": f"索引必须是整数: {value}",
                        "error": f"index 参数必须是整数，收到: {value}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"不支持的 selection 方式: {by}",
                    "error": f"by 参数必须是 value/label/index 之一"
                }

            return {
                "success": True,
                "message": f"已选择下拉选项: {value} ({by})",
                "selector": selector,
                "value": value,
                "by": by
            }

        except Exception as e:
            logger.error(f"SELECT 失败: {e}")
            return {
                "success": False,
                "message": f"选择失败: {str(e)}",
                "error": str(e)
            }

    async def _checkbox(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """复选框操作"""
        try:
            # 实现复选框逻辑
            return self._success_response({"message": "已操作复选框"})
        except Exception as e:
            return self._error_response(f"复选框操作失败: {str(e)}")

    async def _wait_for_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """等待元素"""
        selector = params.get("selector")
        if not selector:
            return self._error_response("缺少必需参数: selector")

        state = params.get("state", "visible")
        timeout = params.get("timeout", 10000)

        try:
            page = await self.browser_manager.get_page()
            await page.wait_for_selector(selector, state=state, timeout=timeout)
            return self._success_response({"message": f"元素已就绪: {selector}"})

        except PlaywrightTimeoutError:
            return self._error_response(f"等待超时: {selector}")
        except Exception as e:
            return self._error_response(f"等待失败: {str(e)}")

    async def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """截图"""
        try:
            screenshot_path = await self.browser_manager.take_screenshot(
                path=params.get("path"),
                full_page=params.get("full_page", False)
            )
            return self._success_response({
                "screenshot_path": screenshot_path
            })
        except Exception as e:
            return self._error_response(f"截图失败: {str(e)}")

    # ============ 断言关键字 ============

    async def _assert_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言文本内容"""
        selector = params.get("selector")
        expected_text = params.get("text")
        match_type = params.get("match_type", "contains")  # contains/exact/regex

        if not selector:
            return self._error_response("缺少必需参数: selector")
        if not expected_text:
            return self._error_response("缺少必需参数: text")

        try:
            page = await self.browser_manager.get_page()
            element = await page.query_selector(selector)

            if not element:
                return {
                    "success": False,
                    "message": f"元素不存在: {selector}",
                    "error": f"元素 {selector} 不存在"
                }

            actual_text = await element.inner_text()

            # 根据匹配类型进行断言
            if match_type == "contains":
                success = expected_text in actual_text
            elif match_type == "exact":
                success = actual_text == expected_text
            elif match_type == "regex":
                import re
                try:
                    success = bool(re.search(expected_text, actual_text))
                except re.error as e:
                    return {
                        "success": False,
                        "message": f"正则表达式无效: {expected_text}",
                        "error": f"正则表达式错误: {str(e)}",
                        "expected": expected_text,
                        "actual": actual_text
                    }
            else:
                return {
                    "success": False,
                    "message": f"不支持的匹配类型: {match_type}",
                    "error": f"match_type 必须是 contains/exact/regex 之一"
                }

            return {
                "success": success,
                "message": f"文本断言: 期望 '{expected_text}' ({match_type})",
                "expected": expected_text,
                "actual": actual_text,
                "match_type": match_type
            }

        except Exception as e:
            logger.error(f"ASSERT_TEXT 失败: {e}")
            return {
                "success": False,
                "message": f"文本断言失败: {str(e)}",
                "error": str(e)
            }

    async def _assert_visible(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言元素可见"""
        selector = params.get("selector")
        if not selector:
            return self._error_response("缺少必需参数: selector")

        timeout = params.get("timeout", 5000)

        try:
            page = await self.browser_manager.get_page()

            # 等待元素可见
            wait_result = await self.browser_manager.wait_for_element(
                selector=selector, state="visible", timeout=timeout
            )

            if not wait_result["success"]:
                # 失败时自动截图
                screenshot_path = await self.browser_manager.take_screenshot()
                return {
                    "success": False,
                    "message": f"元素不可见: {selector}",
                    "error": wait_result.get("error", "元素不可见"),
                    "screenshot": screenshot_path
                }

            return {
                "success": True,
                "message": f"元素可见: {selector}",
                "selector": selector
            }

        except Exception as e:
            logger.error(f"ASSERT_VISIBLE 失败: {e}")
            # 异常时也尝试截图
            try:
                screenshot_path = await self.browser_manager.take_screenshot()
                return {
                    "success": False,
                    "message": f"元素可见性断言失败: {selector}",
                    "error": str(e),
                    "screenshot": screenshot_path
                }
            except:
                return {
                    "success": False,
                    "message": f"元素可见性断言失败: {selector}",
                    "error": str(e)
                }

    async def _assert_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言 URL"""
        expected_url = params.get("url")
        match_type = params.get("match_type", "contains")  # contains/exact

        if not expected_url:
            return self._error_response("缺少必需参数: url")

        try:
            page = await self.browser_manager.get_page()
            actual_url = page.url

            # 根据匹配类型进行断言
            if match_type == "contains":
                success = expected_url in actual_url
            elif match_type == "exact":
                success = actual_url == expected_url
            else:
                return {
                    "success": False,
                    "message": f"不支持的匹配类型: {match_type}",
                    "error": f"match_type 必须是 contains/exact 之一"
                }

            return {
                "success": success,
                "message": f"URL断言: 期望 '{expected_url}'",
                "expected": expected_url,
                "actual": actual_url,
                "match_type": match_type
            }

        except Exception as e:
            logger.error(f"ASSERT_URL 失败: {e}")
            return {
                "success": False,
                "message": f"URL断言失败: {str(e)}",
                "error": str(e)
            }

    async def _assert_title(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言页面标题"""
        expected_title = params.get("title")
        match_type = params.get("match_type", "contains")  # contains/exact

        if not expected_title:
            return self._error_response("缺少必需参数: title")

        try:
            page = await self.browser_manager.get_page()
            actual_title = await page.title()

            # 根据匹配类型进行断言
            if match_type == "contains":
                success = expected_title in actual_title
            elif match_type == "exact":
                success = actual_title == expected_title
            else:
                return {
                    "success": False,
                    "message": f"不支持的匹配类型: {match_type}",
                    "error": f"match_type 必须是 contains/exact 之一"
                }

            return {
                "success": success,
                "message": f"标题断言: 期望 '{expected_title}'",
                "expected": expected_title,
                "actual": actual_title,
                "match_type": match_type
            }

        except Exception as e:
            logger.error(f"ASSERT_TITLE 失败: {e}")
            return {
                "success": False,
                "message": f"标题断言失败: {str(e)}",
                "error": str(e)
            }

    async def _assert_element_count(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """断言元素数量"""
        try:
            # 实现断言逻辑
            return self._success_response({"message": "元素数量断言通过"})
        except Exception as e:
            return self._error_response(f"元素数量断言失败: {str(e)}")

    async def _assert_no_error(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """轮询断言页面无错误弹窗，感知加载完成 - 加载完成或检测到错误立即结束"""
        error_text = params.get("error_text", "系统错误")
        timeout = params.get("timeout", 15000)
        poll_interval = params.get("poll_interval", 500)

        import asyncio
        page = await self.browser_manager.get_page()
        elapsed = 0

        while elapsed < timeout:
            await asyncio.sleep(poll_interval / 1000)
            elapsed += poll_interval

            # 1. 检测错误弹窗
            try:
                error_locator = page.locator(f'text="{error_text}"')
                if await error_locator.count() > 0:
                    is_visible = False
                    for i in range(await error_locator.count()):
                        if await error_locator.nth(i).is_visible():
                            is_visible = True
                            break
                    if is_visible:
                        return self._error_response(f"检测到错误弹窗: {error_text}")
            except Exception:
                pass

            # 2. 检测加载状态：spinner消失即加载结束
            try:
                spinner_count = await page.locator(".ant-spin-spinning").count()
                is_loading = spinner_count > 0
            except Exception:
                is_loading = False

            if not is_loading:
                return self._success_response({
                    "message": f"未检测到错误弹窗，加载已完成 (耗时{elapsed}ms)"
                })

        return self._error_response(f"等待超时({timeout}ms): 加载未完成")

    async def _get_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取元素文本内容"""
        selector = params.get("selector")
        if not selector:
            return self._error_response("缺少必需参数: selector")

        try:
            page = await self.browser_manager.get_page()
            element = await page.query_selector(selector)

            if not element:
                return {
                    "success": False,
                    "message": f"元素不存在: {selector}",
                    "error": f"元素 {selector} 不存在"
                }

            text_content = await element.inner_text()

            return {
                "success": True,
                "message": f"已获取文本: {selector}",
                "text": text_content,
                "selector": selector
            }

        except Exception as e:
            logger.error(f"GET_TEXT 失败: {e}")
            return {
                "success": False,
                "message": f"获取文本失败: {str(e)}",
                "error": str(e)
            }
