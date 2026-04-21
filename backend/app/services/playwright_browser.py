"""
Playwright 浏览器管理器

负责管理 Playwright 浏览器和页面的生命周期，提供截图等辅助功能。
"""
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class PlaywrightBrowser:
    """Playwright 浏览器管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化浏览器管理器

        Args:
            config: 浏览器配置
                - browser_type: 浏览器类型（chromium/firefox/webkit，默认 chromium）
                - headless: 是否无头模式（默认 True）
                - timeout: 默认超时时间（毫秒，默认 30000）
                - viewport: 视口大小（默认 {"width": 1920, "height": 1080}）
                - user_agent: 用户代理字符串
                - screenshot_dir: 截图保存目录
                - remote_url: 远程浏览器URL（如 ws://localhost:9222）
                - use_local: 使用本地浏览器（连接到 host.docker.internal）
        """
        self.config = config or {}
        self.browser_type = self.config.get("browser_type", "chromium")
        self.headless = self.config.get("headless", True)
        self.timeout = self.config.get("timeout", 30000)
        self.viewport = self.config.get("viewport", {"width": 1920, "height": 1080})
        self.user_agent = self.config.get("user_agent")
        self.screenshot_dir = self.config.get("screenshot_dir", "./screenshots")
        self.remote_url = self.config.get("remote_url")
        self.use_local = self.config.get("use_local", False)

        # 确保截图目录存在
        os.makedirs(self.screenshot_dir, exist_ok=True)

        # Playwright 实例
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self._is_started = False

        # 调试信息收集
        self.console_messages = []
        self.network_requests = []

    async def start_browser(self) -> None:
        """启动浏览器或连接到远程浏览器"""
        if self._is_started:
            logger.warning("浏览器已经启动")
            return

        try:
            self.playwright = await async_playwright().start()

            # 获取浏览器对象（根据 browser_type）
            browser_map = {
                "chromium": self.playwright.chromium,
                "firefox": self.playwright.firefox,
                "webkit": self.playwright.webkit
            }
            browser_engine = browser_map.get(self.browser_type, self.playwright.chromium)

            # 支持连接到远程浏览器（本地或远程CDP）
            if self.remote_url:
                # 连接到远程浏览器（仅支持 Chromium）
                if self.browser_type != "chromium":
                    logger.warning(f"远程连接仅支持 Chromium，当前类型: {self.browser_type}")
                    browser_engine = self.playwright.chromium
                logger.info(f"连接到远程浏览器: {self.remote_url}")
                self.browser = await browser_engine.connect(self.remote_url)
            elif self.use_local:
                # 连接到本地浏览器（Docker访问宿主机，仅支持 Chromium）
                if self.browser_type != "chromium":
                    logger.warning(f"本地连接仅支持 Chromium，当前类型: {self.browser_type}")
                    browser_engine = self.playwright.chromium
                local_url = "ws://host.docker.internal:9222"
                logger.info(f"连接到本地浏览器: {local_url}")
                try:
                    self.browser = await browser_engine.connect(local_url)
                except Exception as e:
                    # 本地浏览器连接失败，给出详细提示
                    error_msg = (
                        f"无法连接到本地浏览器: {e}\n"
                        f"\n"
                        f"请确保本地浏览器服务已启动：\n"
                        f"  1. 在项目根目录运行: ./scripts/start-local-browser.sh\n"
                        f"  2. 或手动启动: open -a 'Google Chrome' --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug\n"
                        f"\n"
                        f"检查状态: ./scripts/browser-daemon.sh status\n"
                        f"停止服务: ./scripts/browser-daemon.sh stop\n"
                    )
                    logger.error(error_msg)
                    raise ConnectionError(
                        "无法连接到本地浏览器。请确保已运行 ./scripts/start-local-browser.sh"
                    ) from e
            else:
                # 在容器内启动浏览器
                launch_args = {
                    "headless": self.headless
                }

                # Firefox 和 Webkit 不支持 --no-sandbox 参数
                if self.browser_type == "chromium":
                    launch_args["args"] = ['--no-sandbox', '--disable-setuid-sandbox']

                logger.info(f"启动 {self.browser_type} 浏览器 (headless={self.headless})")
                self.browser = await browser_engine.launch(**launch_args)

            # 创建浏览器上下文
            context_options = {
                "viewport": self.viewport,
                "ignore_https_errors": True,
            }

            if self.user_agent:
                context_options["user_agent"] = self.user_agent

            self.context = await self.browser.new_context(**context_options)

            # 设置默认超时
            self.context.set_default_timeout(self.timeout)

            # 创建第一个页面
            self.page = await self.context.new_page()

            self._is_started = True
            logger.info(f"浏览器启动成功 (headless={self.headless})")

        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            await self.close()
            raise

    async def get_page(self) -> Page:
        """
        获取或创建页面

        Returns:
            Page: Playwright 页面对象
        """
        if not self._is_started:
            await self.start_browser()

        if self.page is None or self.page.is_closed():
            self.page = await self.context.new_page()

        return self.page

    async def new_page(self) -> Page:
        """
        创建新页面

        Returns:
            Page: 新的 Playwright 页面对象
        """
        if not self._is_started:
            await self.start_browser()

        return await self.context.new_page()

    async def close_page(self, page: Optional[Page] = None) -> None:
        """
        关闭页面

        Args:
            page: 要关闭的页面，如果为 None 则关闭当前页面
        """
        target_page = page or self.page

        if target_page and not target_page.is_closed():
            await target_page.close()
            logger.debug("页面已关闭")

        if target_page == self.page:
            self.page = None

    async def take_screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False,
        page: Optional[Page] = None
    ) -> str:
        """
        截取页面截图

        Args:
            path: 保存路径（如果为 None，自动生成）
            full_page: 是否截取整个页面
            page: 要截图的页面（如果为 None，使用当前页面）

        Returns:
            str: 截图文件路径
        """
        target_page = page or await self.get_page()

        try:
            # 生成文件名
            if path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")

            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # 截图
            await target_page.screenshot(path=path, full_page=full_page)

            logger.info(f"截图已保存: {path}")
            return path

        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise

    # ============ 调试增强功能 ============

    async def setup_listeners(self, page: Optional[Page] = None) -> None:
        """
        设置监听器，收集调试信息

        Args:
            page: 要监听的页面，如果为 None 则使用当前页面
        """
        target_page = page or await self.get_page()

        # 清空之前的日志
        self.console_messages.clear()
        self.network_requests.clear()

        # 监听控制台消息
        def on_console(msg):
            self.console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": datetime.now().isoformat()
            })
            logger.debug(f"Console [{msg.type}]: {msg.text}")

        target_page.on("console", on_console)

        # 监听网络请求
        def on_request(request):
            self.network_requests.append({
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "timestamp": datetime.now().isoformat()
            })
            logger.debug(f"Request [{request.method}]: {request.url}")

        target_page.on("request", on_request)

        logger.info("调试监听器已设置")

    async def get_page_snapshot(self, page: Optional[Page] = None) -> Dict[str, Any]:
        """
        获取页面快照

        Args:
            page: 目标页面，如果为 None 则使用当前页面

        Returns:
            包含 URL、标题、HTML 等信息的字典
        """
        target_page = page or await self.get_page()

        try:
            snapshot = {
                "url": target_page.url,
                "title": await target_page.title(),
                "html_length": len(await target_page.content()),
                "timestamp": datetime.now().isoformat()
            }

            # 如果 HTML 不太大，包含完整内容
            html_content = await target_page.content()
            if len(html_content) < 100000:  # 小于 100KB
                snapshot["html"] = html_content
            else:
                snapshot["html"] = f"<html trimmed ({len(html_content)} chars)>"

            return snapshot

        except Exception as e:
            logger.error(f"获取页面快照失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_console_logs(self) -> list:
        """
        获取控制台日志

        Returns:
            控制台消息列表
        """
        return self.console_messages.copy()

    async def get_network_requests(self, limit: int = 10) -> list:
        """
        获取网络请求

        Args:
            limit: 返回最近 N 个请求

        Returns:
            网络请求列表
        """
        return self.network_requests[-limit:] if self.network_requests else []

    async def get_debug_info(self, page: Optional[Page] = None) -> Dict[str, Any]:
        """
        获取完整的调试信息

        Args:
            page: 目标页面

        Returns:
            包含页面快照、控制台日志、网络请求的完整调试信息
        """
        return {
            "page_snapshot": await self.get_page_snapshot(page),
            "console_logs": await self.get_console_logs(),
            "network_requests": await self.get_network_requests(limit=10),
            "timestamp": datetime.now().isoformat()
        }

    async def close(self) -> None:
        """关闭浏览器和清理资源"""
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self._is_started = False
            logger.info("浏览器已关闭")

        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")

    async def restart_with_config(self, config: Dict[str, Any]) -> None:
        """
        使用新配置重启浏览器

        Args:
            config: 新的浏览器配置
        """
        # 如果浏览器已启动，先关闭
        if self._is_started:
            await self.close()

        # 更新配置
        self.config.update(config)
        if "browser_type" in config:
            self.browser_type = config["browser_type"]
        if "headless" in config:
            self.headless = config["headless"]
        if "viewport" in config:
            self.viewport = config["viewport"]
        if "user_agent" in config:
            self.user_agent = config["user_agent"]
        if "timeout" in config:
            self.timeout = config["timeout"]
        if "screenshot_dir" in config:
            self.screenshot_dir = config["screenshot_dir"]
        if "remote_url" in config:
            self.remote_url = config["remote_url"]
        if "use_local" in config:
            self.use_local = config["use_local"]

        # 重新启动浏览器
        await self.start_browser()

    def is_started(self) -> bool:
        """检查浏览器是否已启动"""
        return self._is_started

    async def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[int] = None,
        page: Optional[Page] = None
    ) -> Dict[str, Any]:
        """
        等待元素达到指定状态

        Args:
            selector: CSS 选择器
            state: 等待状态，支持：
                - attached: 元素已附加到 DOM
                - detached: 元素已从 DOM 分离
                - visible: 元素可见
                - hidden: 元素隐藏
                - editable: 元素可编辑
            timeout: 超时时间（毫秒），默认使用配置的 timeout
            page: 目标页面，默认使用当前页面

        Returns:
            Dict: {"success": bool, "message": str, "element": ElementHandle}

        Raises:
            TimeoutError: 元素在超时时间内未达到指定状态
        """
        target_page = page or await self.get_page()
        timeout = timeout or self.timeout

        try:
            logger.debug(f"等待元素: {selector}, 状态: {state}, 超时: {timeout}ms")

            # 状态映射
            state_map = {
                "attached": "attached",
                "detached": "detached",
                "visible": "visible",
                "hidden": "hidden",
            }

            # editable 需要特殊处理
            if state == "editable":
                # 等待元素可见且可编辑
                await target_page.wait_for_selector(
                    selector,
                    state="visible",
                    timeout=timeout
                )
                # 额外检查元素是否可编辑
                element = await target_page.query_selector(selector)
                if element:
                    is_editable = await element.is_editable()
                    if not is_editable:
                        return {
                            "success": False,
                            "message": f"元素可见但不可编辑: {selector}",
                            "element": None
                        }
            elif state in state_map:
                # 标准状态
                await target_page.wait_for_selector(
                    selector,
                    state=state_map[state],
                    timeout=timeout
                )
            else:
                return {
                    "success": False,
                    "message": f"不支持的等待状态: {state}",
                    "element": None
                }

            # 获取元素
            element = await target_page.query_selector(selector)

            logger.info(f"元素已就绪: {selector} (状态: {state})")
            return {
                "success": True,
                "message": f"元素已就绪: {selector}",
                "element": element
            }

        except Exception as e:
            error_msg = f"等待元素超时: {selector} (状态: {state}, 超时: {timeout}ms) - {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "element": None
            }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
