"""
测试 Playwright UI 关键字

运行方式:
    python test_ui_keywords.py
"""
import asyncio
import sys
import os

# 添加路径以导入模块
sys.path.insert(0, os.path.dirname(__file__))

from app.services.playwright_browser import PlaywrightBrowser
from app.services.keyword_engine import KeywordEngine


async def test_baidu_search():
    """测试百度搜索场景"""

    print("=" * 60)
    print("开始测试 Playwright UI 关键字")
    print("=" * 60)

    # 初始化
    browser = PlaywrightBrowser(headless=False)  # 使用有头模式以便观察
    engine = KeywordEngine(browser_manager=browser)

    try:
        # 1. 启动浏览器
        print("\n[1] 启动浏览器...")
        await browser.start_browser()
        print("✅ 浏览器启动成功")

        # 2. 导航到百度
        print("\n[2] 导航到百度首页...")
        result = await engine.execute(
            keyword_def={"name": "NAVIGATE", "category": "ui"},
            parameters={"url": "https://www.baidu.com"},
            context={}
        )
        if result["success"]:
            print(f"✅ 导航成功: {result['title']}")
        else:
            print(f"❌ 导航失败: {result.get('error')}")
            return

        # 3. 在搜索框输入文本
        print("\n[3] 在搜索框输入 'Playwright 自动化测试'...")
        result = await engine.execute(
            keyword_def={"name": "INPUT", "category": "ui"},
            parameters={
                "selector": "#kw",
                "text": "Playwright 自动化测试",
                "clear_first": True
            },
            context={}
        )
        if result["success"]:
            print(f"✅ 输入成功: {result['message']}")
        else:
            print(f"❌ 输入失败: {result.get('error')}")

        # 4. 点击搜索按钮
        print("\n[4] 点击搜索按钮...")
        result = await engine.execute(
            keyword_def={"name": "CLICK", "category": "ui"},
            parameters={"selector": "#su"},
            context={}
        )
        if result["success"]:
            print(f"✅ 点击成功: {result['message']}")
        else:
            print(f"❌ 点击失败: {result.get('error')}")

        # 5. 等待搜索结果
        print("\n[5] 等待搜索结果出现...")
        result = await engine.execute(
            keyword_def={"name": "WAIT_FOR_ELEMENT", "category": "ui"},
            parameters={
                "selector": ".content_left",
                "state": "visible",
                "timeout": 10000
            },
            context={}
        )
        if result["success"]:
            print(f"✅ 等待成功: {result['message']}")
        else:
            print(f"❌ 等待失败: {result.get('error')}")

        # 6. 截图保存
        print("\n[6] 截图保存...")
        result = await engine.execute(
            keyword_def={"name": "SCREENSHOT", "category": "ui"},
            parameters={
                "path": "./screenshots/baidu_search_result.png",
                "full_page": False
            },
            context={}
        )
        if result["success"]:
            print(f"✅ 截图成功: {result['screenshot_path']}")
        else:
            print(f"❌ 截图失败: {result.get('error')}")

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭浏览器
        print("\n关闭浏览器...")
        await browser.close()
        print("✅ 浏览器已关闭")


async def test_simple():
    """简单测试：访问 example.com"""
    print("\n" + "=" * 60)
    print("简单测试：访问 example.com")
    print("=" * 60)

    browser = PlaywrightBrowser(headless=False)
    engine = KeywordEngine(browser_manager=browser)

    try:
        await browser.start_browser()
        print("✅ 浏览器启动")

        result = await engine.execute(
            keyword_def={"name": "NAVIGATE", "category": "ui"},
            parameters={"url": "http://example.com"},
            context={}
        )

        if result["success"]:
            print(f"✅ 访问成功: {result['title']}")
            print(f"   URL: {result['url']}")
        else:
            print(f"❌ 访问失败: {result.get('error')}")

        # 等待 3 秒观察
        await asyncio.sleep(3)

    finally:
        await browser.close()


if __name__ == "__main__":
    # 选择测试场景
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        asyncio.run(test_simple())
    else:
        asyncio.run(test_baidu_search())
