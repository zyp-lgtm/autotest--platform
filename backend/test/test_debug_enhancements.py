"""
测试调试增强功能

验证：
- 控制台日志记录
- 网络请求记录
- 失败时自动截图
- HTML 快照保存
- 详细的执行日志
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.playwright_browser import PlaywrightBrowser
from app.services.keyword_engine import KeywordEngine
from app.services.debug_collector import DebugInfoCollector
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 显示所有级别的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_debug_features():
    """测试调试增强功能"""
    logger.info("=" * 80)
    logger.info("开始测试调试增强功能")
    logger.info("=" * 80)

    # 1. 启动浏览器
    logger.info("\n1️⃣  启动浏览器")
    browser_manager = PlaywrightBrowser(config={"headless": False})
    await browser_manager.start_browser()
    keyword_engine = KeywordEngine(browser_manager=browser_manager)

    # 2. 创建调试收集器
    logger.info("\n2️⃣  创建调试收集器")
    debug_collector = DebugInfoCollector(base_dir="./test_debug_output")
    debug_collector.start_session("test_session_001")

    # 3. 设置页面监听器
    logger.info("\n3️⃣  设置页面监听器")
    page = await browser_manager.get_page()
    await debug_collector.setup_page_listeners(page)
    logger.info("✅ 已设置控制台日志和网络请求监听")

    # 4. 导航到百度（会产生网络请求和控制台日志）
    logger.info("\n4️⃣  导航到百度")
    debug_collector.log_step_start(
        step_name="导航到百度",
        keyword="NAVIGATE",
        parameters={"url": "https://www.baidu.com"}
    )

    result = await keyword_engine._navigate({
        "url": "https://www.baidu.com",
        "timeout": 30000
    })

    debug_collector.log_step_complete(
        step_name="导航到百度",
        result=result,
        duration=1.5
    )
    logger.info(f"结果: {result['success']} - {result.get('message', '')}")

    # 等待一段时间让网络请求完成
    await asyncio.sleep(2)

    # 5. 输入搜索关键词（会触发控制台日志）
    logger.info("\n5️⃣  输入搜索关键词")
    debug_collector.log_step_start(
        step_name="输入搜索",
        keyword="INPUT",
        parameters={"selector": "#kw", "text": "调试测试"}
    )

    result = await keyword_engine._input({
        "selector": "#kw",
        "text": "调试测试",
        "timeout": 10000
    })

    debug_collector.log_step_complete(
        step_name="输入搜索",
        result=result,
        duration=0.5
    )

    # 6. 测试失败场景（触发自动截图和调试信息收集）
    logger.info("\n6️⃣  测试失败场景（故意使用错误的选择器）")
    debug_collector.log_step_start(
        step_name="点击不存在的元素",
        keyword="CLICK",
        parameters={"selector": ".non-existent-element-xyz123"}
    )

    result = await keyword_engine._click({
        "selector": ".non-existent-element-xyz123",
        "timeout": 5000
    })

    debug_collector.log_step_complete(
        step_name="点击不存在的元素",
        result=result,
        duration=5.0
    )

    # 如果失败，捕获调试信息
    if not result.get("success"):
        logger.info("捕获失败调试信息...")
        debug_info = await debug_collector.capture_failure_info(
            page=page,
            step_name="点击不存在的元素",
            error=result.get("error", "未知错误"),
            selector=".non-existent-element-xyz123"
        )

        logger.info(f"✅ 调试信息已保存:")
        logger.info(f"  - 截图: {debug_info.get('screenshot')}")
        logger.info(f"  - HTML: {debug_info.get('html_snapshot')}")
        logger.info(f"  - 报告: {debug_info.get('report_path')}")
        logger.info(f"  - 控制台日志数: {len(debug_info.get('console_logs', []))}")
        logger.info(f"  - 网络请求数: {len(debug_info.get('network_requests', []))}")

    # 7. 显示会话摘要
    logger.info("\n7️⃣  会话摘要")
    summary = debug_collector.get_session_summary()
    logger.info(f"  总步骤数: {summary['total_steps']}")
    logger.info(f"  控制台消息: {summary['console_messages']}")
    logger.info(f"  网络请求: {summary['network_requests']}")
    logger.info(f"  失败请求: {summary['failed_requests']}")

    # 8. 关闭浏览器
    logger.info("\n8️⃣  关闭浏览器")
    await browser_manager.close()

    # 9. 结束调试会话
    logger.info("\n9️⃣  结束调试会话")
    final_summary = debug_collector.end_session()
    logger.info(f"✅ 调试会话结束")

    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("✅ 调试增强功能测试完成")
    logger.info("=" * 80)
    logger.info(f"\n调试输出目录: ./test_debug_output/")
    logger.info("请查看以下文件:")
    logger.info("  - screenshots/: 失败截图")
    logger.info("  - html/: 页面快照")
    logger.info("  - logs/: 调试报告（JSON）")


async def test_console_logging():
    """测试控制台日志记录"""
    logger.info("\n" + "=" * 80)
    logger.info("测试控制台日志记录")
    logger.info("=" * 80)

    browser_manager = PlaywrightBrowser(config={"headless": False})
    await browser_manager.start_browser()
    debug_collector = DebugInfoCollector(base_dir="./test_debug_console")
    debug_collector.start_session("console_test")

    page = await browser_manager.get_page()
    await debug_collector.setup_page_listeners(page)

    # 导航到测试页面（会产生控制台日志）
    logger.info("\n导航到测试页面")
    await page.goto("https://www.baidu.com")

    # 在页面中执行 JavaScript 产生控制台日志
    logger.info("\n执行 JavaScript 产生控制台日志")
    await page.evaluate("""
        console.log("这是一条普通日志");
        console.warn("这是一条警告");
        console.error("这是一条错误");
        console.info("这是一条信息");
    """)

    # 等待日志被捕获
    await asyncio.sleep(1)

    # 显示捕获的控制台日志
    logger.info(f"\n捕获到 {len(debug_collector.console_messages)} 条控制台日志:")
    for i, msg in enumerate(debug_collector.console_messages, 1):
        logger.info(f"  {i}. [{msg['type']}] {msg['text']}")

    await browser_manager.close()
    logger.info("\n✅ 控制台日志测试完成")


if __name__ == "__main__":
    print("\n🚀 开始测试调试增强功能\n")

    # 测试 1: 完整调试功能
    asyncio.run(test_debug_features())

    # 测试 2: 控制台日志
    print("\n" + "=" * 80)
    input("按 Enter 继续测试控制台日志...")
    print("=" * 80)

    asyncio.run(test_console_logging())

    print("\n✅ 所有测试完成！")
