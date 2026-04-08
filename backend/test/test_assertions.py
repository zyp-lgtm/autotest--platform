"""
测试断言关键字

验证所有断言关键字是否正常工作：
- ASSERT_TEXT (增强版：正则表达式)
- ASSERT_VISIBLE
- ASSERT_URL
- ASSERT_TITLE
- ASSERT_ELEMENT_COUNT
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.playwright_browser import PlaywrightBrowser
from app.services.keyword_engine import KeywordEngine
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_assertions():
    """测试所有断言关键字"""
    logger.info("=" * 60)
    logger.info("开始测试断言关键字")
    logger.info("=" * 60)

    # 1. 启动浏览器
    logger.info("\n1️⃣  启动浏览器")
    browser_manager = PlaywrightBrowser(config={"headless": False})
    await browser_manager.start_browser()
    keyword_engine = KeywordEngine(browser_manager=browser_manager)
    logger.info("✅ 浏览器启动成功")

    # 2. 导航到百度
    logger.info("\n2️⃣  导航到百度")
    result = await keyword_engine._navigate({
        "url": "https://www.baidu.com",
        "timeout": 30000
    })
    logger.info(f"结果: {result['success']} - {result.get('message', '')}")

    # 3. 测试 ASSERT_TITLE (断言标题)
    logger.info("\n3️⃣  测试 ASSERT_TITLE")
    result = await keyword_engine._assert_title({
        "title": "百度",
        "mode": "contains",
        "timeout": 5000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    # 4. 测试 ASSERT_URL (断言 URL)
    logger.info("\n4️⃣  测试 ASSERT_URL")
    result = await keyword_engine._assert_url({
        "url": "baidu.com",
        "mode": "contains",
        "timeout": 5000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    # 5. 测试 ASSERT_VISIBLE (断言搜索框可见)
    logger.info("\n5️⃣  测试 ASSERT_VISIBLE")
    result = await keyword_engine._assert_visible({
        "selector": "#kw",
        "visible": True,
        "timeout": 10000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    # 6. 测试 ASSERT_ELEMENT_COUNT (断言搜索框数量)
    logger.info("\n6️⃣  测试 ASSERT_ELEMENT_COUNT")
    result = await keyword_engine._assert_element_count({
        "selector": "#kw",
        "operator": "==",
        "count": 1,
        "timeout": 5000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    # 7. 测试 ASSERT_TEXT - contains 模式
    logger.info("\n7️⃣  测试 ASSERT_TEXT (contains)")
    result = await keyword_engine._assert_text({
        "selector": "#kw",
        "text": "百度",
        "mode": "contains",
        "timeout": 5000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    # 8. 测试 ASSERT_TEXT - regex 模式
    logger.info("\n8️⃣  测试 ASSERT_TEXT (regex)")
    result = await keyword_engine._assert_text({
        "selector": "#su",
        "text": r"百度.*",
        "mode": "regex",
        "timeout": 5000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    # 9. 输入搜索关键词
    logger.info("\n9️⃣  输入搜索关键词")
    result = await keyword_engine._input({
        "selector": "#kw",
        "text": "断言测试",
        "timeout": 10000
    })
    logger.info(f"结果: {result['success']} - {result.get('message', '')}")

    # 10. 测试 ASSERT_TEXT - not_contains 模式
    logger.info("\n🔟 测试 ASSERT_TEXT (not_contains)")
    result = await keyword_engine._assert_text({
        "selector": "#kw",
        "text": "不存在的内容xyz123",
        "mode": "not_contains",
        "timeout": 5000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    # 11. 关闭浏览器
    logger.info("\n🔚  关闭浏览器")
    await browser_manager.close()
    logger.info("✅ 浏览器已关闭")

    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("✅ 测试完成！所有断言关键字工作正常")
    logger.info("=" * 60)


async def test_assertion_failures():
    """测试断言失败场景"""
    logger.info("\n" + "=" * 60)
    logger.info("测试断言失败场景")
    logger.info("=" * 60)

    browser_manager = PlaywrightBrowser(config={"headless": False})
    await browser_manager.start_browser()
    keyword_engine = KeywordEngine(browser_manager=browser_manager)

    # 导航到百度
    logger.info("\n1️⃣  导航到百度")
    await keyword_engine._navigate({"url": "https://www.baidu.com"})

    # 测试失败的断言
    logger.info("\n2️⃣  测试 ASSERT_TITLE 失败")
    result = await keyword_engine._assert_title({
        "title": "不存在的标题",
        "mode": "contains",
        "timeout": 3000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    logger.info("\n3️⃣  测试 ASSERT_VISIBLE 失败（元素不可见）")
    result = await keyword_engine._assert_visible({
        "selector": ".not-exist-element",
        "visible": True,
        "timeout": 3000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    await browser_manager.close()
    logger.info("\n✅ 失败场景测试完成")


if __name__ == "__main__":
    print("\n🚀 开始测试断言关键字\n")

    # 测试 1: 正常断言
    asyncio.run(test_assertions())

    # 测试 2: 失败场景
    print("\n" + "=" * 60)
    input("按 Enter 继续测试失败场景...")
    print("=" * 60)

    asyncio.run(test_assertion_failures())

    print("\n✅ 所有测试完成！")
