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
                - headless: 是否无头模式（默认 True）
                - timeout: 默认超时时间（毫秒，默认 30000）
                - viewport: 视口大小（默认 {"width": 1920, "height": 1080}）
                - user_agent: 用户代理字符串
                - screenshot_dir: 截图保存目录
                - remote_url: 远程浏览器URL（如 ws://localhost:9222）
                - use_local: 使用本地浏览器（连接到 host.docker.internal）
        """
        self.config = config or {}
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

    async def start_browser(self) -> None:
        """启动浏览器或连接到远程浏览器"""
        if self._is_started:
            logger.warning("浏览器已经启动")
            return

        try:
            self.playwright = await async_playwright().start()

            # 支持连接到远程浏览器（本地或远程CDP）
            if self.remote_url:
                # 连接到远程浏览器
                logger.info(f"连接到远程浏览器: {self.remote_url}")
                self.browser = await self.playwright.chromium.connect(self.remote_url)
            elif self.use_local:
                # 连接到本地浏览器（Docker访问宿主机）
                local_url = "ws://host.docker.internal:9222"
                logger.info(f"连接到本地浏览器: {local_url}")
                try:
                    self.browser = await self.playwright.chromium.connect(local_url)
                except Exception as e:
                    logger.warning(f"无法连接到本地浏览器 ({e})，将启动容器内浏览器")
                    self.browser = await self.playwright.chromium.launch(
                        headless=self.headless,
                        args=['--no-sandbox', '--disable-setuid-sandbox']
                    )
            else:
                # 在容器内启动浏览器
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

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

    def is_started(self) -> bool:
        """检查浏览器是否已启动"""
        return self._is_started

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
