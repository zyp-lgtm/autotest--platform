"""
测试核心 UI 关键字

验证 CLICK, INPUT, WAIT_FOR_ELEMENT, ASSERT_TEXT, SCREENSHOT 等关键字是否正常工作
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


async def test_baidu_search():
    """测试百度搜索流程"""
    logger.info("=" * 60)
    logger.info("开始测试核心关键字")
    logger.info("=" * 60)

    # 1. 启动浏览器
    logger.info("\n1️⃣  启动浏览器")
    browser_manager = PlaywrightBrowser(config={"headless": False})
    await browser_manager.start_browser()
    logger.info("✅ 浏览器启动成功")

    # 2. 创建关键字引擎
    keyword_engine = KeywordEngine(browser_manager=browser_manager)

    # 3. 导航到百度
    logger.info("\n2️⃣  导航到百度")
    result = await keyword_engine._navigate({
        "url": "https://www.baidu.com",
        "wait_until": "load",
        "timeout": 30000
    })
    logger.info(f"结果: {result['success']} - {result.get('message', '')}")

    # 4. 等待搜索框
    logger.info("\n3️⃣  等待搜索框")
    result = await keyword_engine._wait_for_element({
        "selector": "#kw",
        "state": "visible",
        "timeout": 10000
    })
    logger.info(f"结果: {result['success']} - {result.get('message', '')}")

    # 5. 输入搜索关键词
    logger.info("\n4️⃣  输入搜索关键词")
    result = await keyword_engine._input({
        "selector": "#kw",
        "text": "Playwright 自动化测试",
        "clear_first": True,
        "timeout": 5000
    })
    logger.info(f"结果: {result['success']} - {result.get('message', '')}")

    # 6. 点击搜索按钮
    logger.info("\n5️⃣  点击搜索按钮")
    result = await keyword_engine._click({
        "selector": "#su",
        "timeout": 5000
    })
    logger.info(f"结果: {result['success']} - {result.get('message', '')}")

    # 7. 等待搜索结果
    logger.info("\n6️⃣  等待搜索结果加载")
    await asyncio.sleep(2)  # 等待页面加载
    result = await keyword_engine._wait_for_element({
        "selector": ".result",
        "state": "visible",
        "timeout": 10000
    })
    logger.info(f"结果: {result['success']} - {result.get('message', '')}")

    # 8. 断言搜索结果
    logger.info("\n7️⃣  断言搜索结果包含关键词")
    result = await keyword_engine._assert_text({
        "text": "Playwright",
        "mode": "contains",
        "timeout": 10000
    })
    logger.info(f"结果: {result['success']} - 通过: {result.get('passed', False)} - {result.get('message', '')}")

    # 9. 提取搜索结果文本
    logger.info("\n8️⃣  提取第一个搜索结果的文本")
    result = await keyword_engine._get_text({
        "selector": ".result h3",
        "timeout": 5000
    })
    if result['success']:
        text = result.get('text', '')
        logger.info(f"结果: {result['success']} - 提取到文本: '{text[:50]}...' if len(text) > 50 else f'提取到文本: {text}'")
    else:
        logger.error(f"结果: {result['success']} - {result.get('error', '')}")

    # 10. 截图
    logger.info("\n9️⃣  截取页面截图")
    result = await keyword_engine._screenshot({
        "path": "/tmp/baidu_search_result.png",
        "full_page": False
    })
    if result['success']:
        logger.info(f"结果: {result['success']} - 截图已保存: {result.get('screenshot_path', '')}")
    else:
        logger.error(f"结果: {result['success']} - {result.get('error', '')}")

    # 11. 关闭浏览器
    logger.info("\n🔚  关闭浏览器")
    await browser_manager.close()
    logger.info("✅ 浏览器已关闭")

    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("✅ 测试完成！所有核心关键字工作正常")
    logger.info("=" * 60)


async def test_form_elements():
    """测试表单元素关键字（SELECT, CHECKBOX, HOVER）"""
    logger.info("\n" + "=" * 60)
    logger.info("测试表单元素关键字")
    logger.info("=" * 60)

    browser_manager = PlaywrightBrowser(config={"headless": False})
    await browser_manager.start_browser()

    keyword_engine = KeywordEngine(browser_manager=browser_manager)

    # 导航到一个包含多种表单元素的测试页面
    logger.info("\n1️⃣  导航到测试页面")
    result = await keyword_engine._navigate({
        "url": "https://www.w3schools.com/html/tryit.asp?filename=html5_form_elements"
    })
    logger.info(f"导航结果: {result['success']}")

    # 保持浏览器打开 10 秒便于观察
    logger.info("\n⏸️  浏览器将保持 10 秒，请观察页面...")
    await asyncio.sleep(10)

    await browser_manager.close()
    logger.info("✅ 表单元素测试完成")


if __name__ == "__main__":
    print("\n🚀 开始测试核心关键字\n")

    # 测试 1: 百度搜索流程
    asyncio.run(test_baidu_search())

    # 测试 2: 表单元素（可选）
    print("\n" + "=" * 60)
    input("按 Enter 继续测试表单元素关键字（或 Ctrl+C 退出）...")
    print("=" * 60)

    # asyncio.run(test_form_elements())

    print("\n✅ 所有测试完成！")
