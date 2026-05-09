"""
改进的百度搜索测试（使用日志记录）

处理动态加载和更可靠的元素定位
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def test_baidu_improved():
    """改进的百度搜索测试"""

    logger.info("=" * 70)
    logger.info("百度搜索测试（改进版）")
    logger.info("=" * 70)

    # 使用 headless=False 以便观察
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

        # 等待页面完全加载
        logger.info("等待页面加载完成...")
        await asyncio.sleep(3)

        # 尝试多个可能的选择器
        logger.info("尝试定位搜索框...")

        page = await browser.get_page()

        # 检查搜索框是否存在
        selectors_to_try = [
            "#kw",
            'input[name="wd"]',
            ".s_ipt",
            'input[id="kw"]'
        ]

        input_found = False
        for selector in selectors_to_try:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"✅ 找到搜索框，使用选择器: {selector}")

                    result = await engine.execute(
                        keyword_def={"name": "INPUT", "category": "ui"},
                        parameters={
                            "selector": selector,
                            "text": "Playwright 自动化测试",
                            "clear_first": True,
                            "timeout": 10000
                        },
                        context={}
                    )

                    if result["success"]:
                        logger.info(f"✅ 输入成功: {result['message']}")
                        input_found = True
                        break
                    else:
                        logger.warning(f"输入失败: {result.get('error')}")
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue

        if not input_found:
            logger.error("未找到搜索框，页面可能结构不同")
            await browser.take_screenshot(path="./screenshots/baidu_debug.png")
            logger.info("📸 已保存调试截图")
            return

        await asyncio.sleep(1)

        # 尝试查找搜索按钮
        logger.info("尝试定位搜索按钮...")

        button_selectors = [
            "#su",
            'input[type="submit"]',
            ".s_btn",
            'input[value="百度一下"]'
        ]

        button_found = False
        for selector in button_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"✅ 找到搜索按钮，使用选择器: {selector}")

                    result = await engine.execute(
                        keyword_def={"name": "CLICK", "category": "ui"},
                        parameters={
                            "selector": selector,
                            "timeout": 5000
                        },
                        context={}
                    )

                    if result["success"]:
                        logger.info(f"✅ 点击成功: {result['message']}")
                        button_found = True
                        break
                    else:
                        logger.warning(f"点击失败: {result.get('error')}")
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue

        if not button_found:
            logger.error("未找到搜索按钮")
            await browser.take_screenshot(path="./screenshots/baidu_after_input.png")
            logger.info("📸 已保存输入后的截图")
            return

        logger.info("等待搜索结果加载...")
        await asyncio.sleep(3)

        logger.info("检查搜索结果...")

        result_selectors = [
            ".content_left",
            "#content_left",
            ".c-container",
            "[data-tools]"
        ]

        results_found = False
        for selector in result_selectors:
            try:
                result = await engine.execute(
                    keyword_def={"name": "WAIT_FOR_ELEMENT", "category": "ui"},
                    parameters={
                        "selector": selector,
                        "state": "visible",
                        "timeout": 5000
                    },
                    context={}
                )

                if result["success"]:
                    logger.info(f"✅ 找到搜索结果，使用选择器: {selector}")
                    results_found = True
                    break
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue

        if not results_found:
            logger.warning("搜索结果容器未找到，但可能有其他显示")

        logger.info("保存最终截图...")
        screenshot_path = await browser.take_screenshot(
            path="./screenshots/baidu_final.png",
            full_page=False
        )
        logger.info(f"✅ 截图保存: {screenshot_path}")

        logger.info("=" * 70)
        logger.info("✅ 百度搜索测试完成！")
        logger.info("=" * 70)

        logger.info("浏览器将保持打开 3 秒以便观察...")
        await asyncio.sleep(3)

    except Exception as e:
        logger.error(f"测试过程出错: {e}", exc_info=True)

    finally:
        logger.info("关闭浏览器...")
        await browser.close()
        logger.info("✅ 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(test_baidu_improved())
