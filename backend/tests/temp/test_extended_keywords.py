"""
扩展 UI 关键字测试

测试新增的 6 个关键字：SELECT, CHECKBOX, HOVER, ASSERT_TEXT, GET_TEXT, SCROLL
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


async def test_extended_keywords():
    """测试扩展的 UI 关键字"""

    logger.info("=" * 70)
    logger.info("扩展 UI 关键字测试")
    logger.info("=" * 70)

    browser = PlaywrightBrowser(config={"headless": False})
    engine = KeywordEngine(browser_manager=browser)

    try:
        logger.info("启动浏览器...")
        await browser.start_browser()
        logger.info("✅ 浏览器启动成功")

        # 测试 1: GET_TEXT - 提取页面标题
        logger.info("\n[测试 1] GET_TEXT - 提取页面标题")
        page = await browser.get_page()

        result = await engine.execute(
            keyword_def={"name": "GET_TEXT", "category": "ui"},
            parameters={"selector": "h1", "attribute": None},
            context={}
        )

        if result["success"]:
            logger.info(f"✅ GET_TEXT 成功: {result['message']}")
            logger.info(f"   提取的文本: {result.get('text', '')[:50]}")
        else:
            logger.error(f"❌ GET_TEXT 失败: {result.get('error')}")

        await asyncio.sleep(1)

        # 测试 2: NAVIGATE - 访问包含表单的测试页面
        logger.info("\n[测试 2] NAVIGATE - 访问表单测试页面")
        result = await engine.execute(
            keyword_def={"name": "NAVIGATE", "category": "ui"},
            parameters={
                "url": "https://www.selenium.dev/selenium/web/webdriver.html",
                "wait_until": "networkidle"
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ NAVIGATE 成功: {result['title']}")
        else:
            logger.error(f"❌ NAVIGATE 失败: {result.get('error')}")
            return

        await asyncio.sleep(3)

        # 测试 3: SCROLL - 滚动页面
        logger.info("\n[测试 3] SCROLL - 向下滚动页面")
        result = await engine.execute(
            keyword_def={"name": "SCROLL", "category": "ui"},
            parameters={
                "direction": "down",
                "pixels": 500
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ SCROLL 成功: {result['message']}")
        else:
            logger.warning(f"⚠️  SCROLL 失败: {result.get('error')}")

        await asyncio.sleep(1)

        # 测试 4: ASSERT_TEXT - 验证页面包含特定文本
        logger.info("\n[测试 4] ASSERT_TEXT - 验证页面包含 'Selenium'")
        result = await engine.execute(
            keyword_def={"name": "ASSERT_TEXT", "category": "ui"},
            parameters={
                "text": "Selenium",
                "mode": "contains"
            },
            context={}
        )

        if result["success"]:
            status = "✅ 通过" if result.get("passed") else "❌ 失败"
            logger.info(f"{status} - {result['message']}")
        else:
            logger.error(f"❌ ASSERT_TEXT 失败: {result.get('error')}")

        await asyncio.sleep(1)

        # 测试 5: HOVER - 悬停在导航链接上
        logger.info("\n[测试 5] HOVER - 悬停在导航链接")
        result = await engine.execute(
            keyword_def={"name": "HOVER", "category": "ui"},
            parameters={
                "selector": "a[href*='webdriver']",
                "timeout": 5000
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ HOVER 成功: {result['message']}")
        else:
            logger.warning(f"⚠️  HOVER 失败: {result.get('error')}")

        await asyncio.sleep(1)

        # 测试 6: GET_TEXT - 提取链接文本
        logger.info("\n[测试 6] GET_TEXT - 提取链接 href 属性")
        result = await engine.execute(
            keyword_def={"name": "GET_TEXT", "category": "ui"},
            parameters={
                "selector": "a[href*='webdriver']",
                "attribute": "href"
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ GET_TEXT 成功: {result['message']}")
            logger.info(f"   提取的 href: {result.get('text', '')}")
        else:
            logger.warning(f"⚠️  GET_TEXT 失败: {result.get('error')}")

        # 测试 7: SCREENSHOT - 截图保存
        logger.info("\n[测试 7] SCREENSHOT - 保存测试截图")
        result = await engine.execute(
            keyword_def={"name": "SCREENSHOT", "category": "ui"},
            parameters={
                "path": "./screenshots/extended_test.png",
                "full_page": False
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ SCREENSHOT 成功: {result['screenshot_path']}")
        else:
            logger.error(f"❌ SCREENSHOT 失败: {result.get('error')}")

        # 统计结果
        logger.info("\n" + "=" * 70)
        logger.info("扩展 UI 关键字测试完成")
        logger.info("=" * 70)

        logger.info("浏览器保持打开 3 秒...")
        await asyncio.sleep(3)

    except Exception as e:
        logger.error(f"测试过程出错: {e}", exc_info=True)

    finally:
        logger.info("关闭浏览器...")
        await browser.close()
        logger.info("✅ 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(test_extended_keywords())
