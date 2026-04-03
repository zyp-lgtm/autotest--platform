"""
百度搜索测试（使用 Enter 键提交）

简化版本，直接使用 Enter 键提交搜索
"""
import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

from app.services.playwright_browser import PlaywrightBrowser
from app.services.keyword_engine import KeywordEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_baidu_enter():
    """百度搜索测试 - 使用 Enter 键提交"""

    logger.info("=" * 70)
    logger.info("百度搜索测试 - Enter 键提交")
    logger.info("=" * 70)

    browser = PlaywrightBrowser(config={"headless": False})
    engine = KeywordEngine(browser_manager=browser)

    try:
        logger.info("启动浏览器...")
        await browser.start_browser()
        logger.info("✅ 浏览器启动成功")

        # 导航到百度
        logger.info("导航到百度首页...")
        result = await engine.execute(
            keyword_def={"name": "NAVIGATE", "category": "ui"},
            parameters={
                "url": "https://www.baidu.com",
                "wait_until": "networkidle",
                "timeout": 30000
            },
            context={}
        )

        if not result["success"]:
            logger.error(f"导航失败: {result.get('error')}")
            return

        logger.info(f"✅ 导航成功: {result['title']}")
        logger.info("等待页面加载...")
        await asyncio.sleep(3)

        # 直接使用 Playwright API 输入
        logger.info("在搜索框输入文本...")
        page = await browser.get_page()

        try:
            # 定位搜索框并输入
            search_box = page.locator("#kw")
            await search_box.click()
            await search_box.type("Playwright 自动化测试", delay=100)
            logger.info("✅ 输入成功")
        except Exception as e:
            logger.error(f"输入失败: {e}")
            return

        logger.info("按 Enter 键提交搜索...")
        await asyncio.sleep(1)

        try:
            await page.keyboard.press("Enter")
            logger.info("✅ Enter 键按下")
        except Exception as e:
            logger.error(f"按键失败: {e}")
            return

        logger.info("等待搜索结果加载...")
        await asyncio.sleep(5)

        # 检查是否有结果
        logger.info("检查搜索结果...")

        # 获取页面标题
        title = await page.title()
        logger.info(f"当前页面标题: {title}")

        # 保存截图
        logger.info("保存截图...")
        screenshot_path = await browser.take_screenshot(
            path="./screenshots/baidu_success.png",
            full_page=False
        )
        logger.info(f"✅ 截图保存: {screenshot_path}")

        logger.info("=" * 70)
        logger.info("✅ 百度搜索测试成功完成！")
        logger.info("=" * 70)

        logger.info("浏览器保持打开 5 秒...")
        await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"测试过程出错: {e}", exc_info=True)

    finally:
        logger.info("关闭浏览器...")
        await browser.close()
        logger.info("✅ 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(test_baidu_enter())
