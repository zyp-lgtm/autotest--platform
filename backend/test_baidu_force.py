"""
百度搜索测试（强制模式）

使用 force 选项操作元素
"""
import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

from app.services.playwright_browser import PlaywrightBrowser
from playwright.async_api import async_playwright

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_baidu_force():
    """百度搜索测试 - 强制模式"""

    logger.info("=" * 70)
    logger.info("百度搜索测试 - 强制模式")
    logger.info("=" * 70)

    try:
        logger.info("启动 Playwright...")
        playwright = await async_playwright().start()

        logger.info("启动浏览器（有头模式）...")
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        logger.info("✅ 浏览器启动成功")

        # 导航
        logger.info("导航到百度...")
        await page.goto("https://www.baidu.com", wait_until="networkidle")
        logger.info(f"✅ 导航成功: {await page.title()}")

        logger.info("等待页面完全加载...")
        await asyncio.sleep(5)

        # 直接操作 DOM
        logger.info("尝试直接填充搜索框...")
        try:
            # 等待搜索框出现
            search_box = await page.wait_for_selector("#kw", timeout=10000)
            logger.info("✅ 找到搜索框")

            # 直接填充（不点击）
            await search_box.fill("Playwright 自动化测试")
            logger.info("✅ 输入成功")

        except Exception as e:
            logger.error(f"搜索框操作失败: {e}")

        await asyncio.sleep(2)

        # 按 Enter
        logger.info("按 Enter 键提交...")
        try:
            await page.keyboard.press("Enter")
            logger.info("✅ Enter 键按下")
        except Exception as e:
            logger.error(f"按键失败: {e}")

        # 等待结果
        logger.info("等待搜索结果...")
        await asyncio.sleep(5)

        # 获取状态
        title = await page.title()
        url = page.url
        logger.info(f"页面标题: {title}")
        logger.info(f"当前 URL: {url}")

        # 截图
        logger.info("保存截图...")
        await page.screenshot(path="./screenshots/baidu_force.png")
        logger.info("✅ 截图已保存")

        logger.info("=" * 70)
        logger.info("✅ 测试完成")
        logger.info("=" * 70)

        logger.info("浏览器保持打开 5 秒...")
        await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)

    finally:
        try:
            await browser.close()
            await playwright.stop()
            logger.info("✅ 浏览器已关闭")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(test_baidu_force())
