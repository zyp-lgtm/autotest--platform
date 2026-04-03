"""
扩展关键字测试（使用本地测试页面）

测试所有新增的 UI 关键字
"""
import asyncio
import sys
import os
import logging
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from app.services.playwright_browser import PlaywrightBrowser
from app.services.keyword_engine import KeywordEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_extended_keywords_local():
    """使用本地页面测试扩展关键字"""

    # 获取测试页面路径
    test_page_path = Path(__file__).parent / "test_page.html"
    test_page_url = f"file://{test_page_path.absolute()}"

    logger.info("=" * 70)
    logger.info("扩展 UI 关键字测试（本地页面）")
    logger.info("=" * 70)

    browser = PlaywrightBrowser(config={"headless": False})
    engine = KeywordEngine(browser_manager=browser)

    test_results = []

    try:
        logger.info("启动浏览器...")
        await browser.start_browser()
        logger.info("✅ 浏览器启动成功")

        # 导航到测试页面
        logger.info(f"\n导航到测试页面: {test_page_url}")
        result = await engine.execute(
            keyword_def={"name": "NAVIGATE", "category": "ui"},
            parameters={"url": test_page_url},
            context={}
        )

        if not result["success"]:
            logger.error(f"导航失败: {result.get('error')}")
            return

        logger.info(f"✅ 导航成功: {result['title']}")
        test_results.append(("NAVIGATE", True))

        await asyncio.sleep(2)

        # 测试 1: GET_TEXT - 提取标题
        logger.info("\n[测试 1] GET_TEXT - 提取页面 h1")
        result = await engine.execute(
            keyword_def={"name": "GET_TEXT", "category": "ui"},
            parameters={"selector": "h1"},
            context={}
        )

        if result["success"]:
            logger.info(f"✅ GET_TEXT: {result['message']}")
            logger.info(f"   提取的文本: {result.get('text', '')}")
            test_results.append(("GET_TEXT", True))
        else:
            logger.error(f"❌ GET_TEXT 失败: {result.get('error')}")
            test_results.append(("GET_TEXT", False))

        # 测试 2: GET_TEXT - 提取链接 href
        logger.info("\n[测试 2] GET_TEXT - 提取链接 href 属性")
        result = await engine.execute(
            keyword_def={"name": "GET_TEXT", "category": "ui"},
            parameters={
                "selector": "#link-test",
                "attribute": "href"
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ GET_TEXT: {result['message']}")
            test_results.append(("GET_TEXT 属性", True))
        else:
            logger.error(f"❌ GET_TEXT 失败: {result.get('error')}")
            test_results.append(("GET_TEXT 属性", False))

        await asyncio.sleep(1)

        # 测试 3: SCROLL - 向下滚动
        logger.info("\n[测试 3] SCROLL - 向下滚动 300px")
        result = await engine.execute(
            keyword_def={"name": "SCROLL", "category": "ui"},
            parameters={
                "direction": "down",
                "pixels": 300
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ SCROLL: {result['message']}")
            test_results.append(("SCROLL", True))
        else:
            logger.warning(f"⚠️  SCROLL: {result.get('error')}")
            test_results.append(("SCROLL", False))

        await asyncio.sleep(1)

        # 测试 4: ASSERT_TEXT - 验证页面包含"UI 关键字测试"
        logger.info("\n[测试 4] ASSERT_TEXT - 验证包含'UI 关键字测试'")
        result = await engine.execute(
            keyword_def={"name": "ASSERT_TEXT", "category": "ui"},
            parameters={
                "text": "UI 关键字测试",
                "mode": "contains"
            },
            context={}
        )

        if result["success"]:
            status = "✅ 通过" if result.get("passed") else "❌ 失败"
            logger.info(f"{status}: {result['message']}")
            test_results.append(("ASSERT_TEXT", result.get("passed", False)))
        else:
            logger.error(f"❌ ASSERT_TEXT 失败: {result.get('error')}")
            test_results.append(("ASSERT_TEXT", False))

        await asyncio.sleep(1)

        # 测试 5: HOVER - 悬停在悬停区域
        logger.info("\n[测试 5] HOVER - 悬停在测试区域")
        result = await engine.execute(
            keyword_def={"name": "HOVER", "category": "ui"},
            parameters={
                "selector": "#hover-area",
                "timeout": 5000
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ HOVER: {result['message']}")
            test_results.append(("HOVER", True))
        else:
            logger.warning(f"⚠️  HOVER: {result.get('error')}")
            test_results.append(("HOVER", False))

        await asyncio.sleep(1)

        # 测试 6: SELECT - 选择下拉选项
        logger.info("\n[测试 6] SELECT - 选择'选项二'")
        result = await engine.execute(
            keyword_def={"name": "SELECT", "category": "ui"},
            parameters={
                "selector": "#dropdown",
                "value": "option2"
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ SELECT: {result['message']}")
            test_results.append(("SELECT", True))
        else:
            logger.error(f"❌ SELECT 失败: {result.get('error')}")
            test_results.append(("SELECT", False))

        await asyncio.sleep(1)

        # 测试 7: CHECKBOX - 勾选复选框
        logger.info("\n[测试 7] CHECKBOX - 勾选复选框")
        result = await engine.execute(
            keyword_def={"name": "CHECKBOX", "category": "ui"},
            parameters={
                "selector": "#checkbox1",
                "checked": True
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ CHECKBOX: {result['message']}")
            test_results.append(("CHECKBOX", True))
        else:
            logger.error(f"❌ CHECKBOX 失败: {result.get('error')}")
            test_results.append(("CHECKBOX", False))

        await asyncio.sleep(1)

        # 测试 8: INPUT - 在输入框输入文本
        logger.info("\n[测试 8] INPUT - 在输入框输入'测试成功'")
        result = await engine.execute(
            keyword_def={"name": "INPUT", "category": "ui"},
            parameters={
                "selector": "#input1",
                "text": "测试成功",
                "clear_first": True
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ INPUT: {result['message']}")
            test_results.append(("INPUT", True))
        else:
            logger.error(f"❌ INPUT 失败: {result.get('error')}")
            test_results.append(("INPUT", False))

        await asyncio.sleep(1)

        # 最终截图
        logger.info("\n[测试 9] SCREENSHOT - 保存最终状态")
        result = await engine.execute(
            keyword_def={"name": "SCREENSHOT", "category": "ui"},
            parameters={
                "path": "./screenshots/extended_keywords_test.png"
            },
            context={}
        )

        if result["success"]:
            logger.info(f"✅ SCREENSHOT: {result['screenshot_path']}")
            test_results.append(("SCREENSHOT", True))
        else:
            logger.error(f"❌ SCREENSHOT 失败: {result.get('error')}")
            test_results.append(("SCREENSHOT", False))

        # 统计结果
        logger.info("\n" + "=" * 70)
        logger.info("测试结果汇总")
        logger.info("=" * 70)

        passed = sum(1 for _, success in test_results if success)
        total = len(test_results)

        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"{status} - {test_name}")

        logger.info(f"\n总计: {passed}/{total} 测试通过 ({passed*100//total}%)")

        if passed == total:
            logger.info("\n🎉 所有扩展关键字测试通过！")
        else:
            logger.info(f"\n⚠️  {total - passed} 个测试失败")

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
    asyncio.run(test_extended_keywords_local())
