"""
基础关键字功能测试

测试所有 Playwright UI 关键字的基本功能
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.playwright_browser import PlaywrightBrowser
from app.services.keyword_engine import KeywordEngine


async def test_all_keywords():
    """测试所有关键字的基本功能"""

    print("=" * 70)
    print("Playwright UI 关键字功能测试")
    print("=" * 70)

    browser = PlaywrightBrowser(config={"headless": True})
    engine = KeywordEngine(browser_manager=browser)

    test_results = []

    try:
        print("\n[1] 启动浏览器...")
        await browser.start_browser()
        print("✅ 浏览器启动成功")
        test_results.append(("浏览器启动", True))

        # 测试 1: NAVIGATE
        print("\n[测试 1] NAVIGATE - 导航到 example.com")
        result = await engine.execute(
            keyword_def={"name": "NAVIGATE", "category": "ui"},
            parameters={"url": "http://example.com"},
            context={}
        )
        if result["success"]:
            print(f"✅ NAVIGATE 成功: {result['title']}")
            print(f"   URL: {result['url']}")
            test_results.append(("NAVIGATE", True))
        else:
            print(f"❌ NAVIGATE 失败: {result.get('error')}")
            test_results.append(("NAVIGATE", False))

        # 测试 2: WAIT_FOR_ELEMENT
        print("\n[测试 2] WAIT_FOR_ELEMENT - 等待 h1 元素")
        result = await engine.execute(
            keyword_def={"name": "WAIT_FOR_ELEMENT", "category": "ui"},
            parameters={
                "selector": "h1",
                "state": "visible",
                "timeout": 5000
            },
            context={}
        )
        if result["success"]:
            print(f"✅ WAIT_FOR_ELEMENT 成功: {result['message']}")
            test_results.append(("WAIT_FOR_ELEMENT", True))
        else:
            print(f"❌ WAIT_FOR_ELEMENT 失败: {result.get('error')}")
            test_results.append(("WAIT_FOR_ELEMENT", False))

        # 测试 3: SCREENSHOT
        print("\n[测试 3] SCREENSHOT - 截取页面")
        result = await engine.execute(
            keyword_def={"name": "SCREENSHOT", "category": "ui"},
            parameters={
                "path": "./screenshots/test_result.png",
                "full_page": False
            },
            context={}
        )
        if result["success"]:
            print(f"✅ SCREENSHOT 成功: {result['screenshot_path']}")
            test_results.append(("SCREENSHOT", True))
        else:
            print(f"❌ SCREENSHOT 失败: {result.get('error')}")
            test_results.append(("SCREENSHOT", False))

        # 测试 4: NAVIGATE 到表单页面
        print("\n[测试 4] NAVIGATE - 导航到表单测试页面")
        result = await engine.execute(
            keyword_def={"name": "NAVIGATE", "category": "ui"},
            parameters={"url": "https://www.selenium.dev/selenium/web/webdriver.html"},
            context={}
        )
        if result["success"]:
            print(f"✅ NAVIGATE 成功: {result['title']}")
            test_results.append(("NAVIGATE 表单页", True))
        else:
            print(f"❌ NAVIGATE 失败: {result.get('error')}")
            test_results.append(("NAVIGATE 表单页", False))

        # 等待页面加载
        await asyncio.sleep(2)

        # 测试 5: INPUT - 输入文本
        print("\n[测试 5] INPUT - 在搜索框输入文本")
        result = await engine.execute(
            keyword_def={"name": "INPUT", "category": "ui"},
            parameters={
                "selector": "#searchInput",
                "text": "Playwright",
                "clear_first": True,
                "timeout": 10000
            },
            context={}
        )
        if result["success"]:
            print(f"✅ INPUT 成功: {result['message']}")
            test_results.append(("INPUT", True))
        else:
            print(f"❌ INPUT 失败: {result.get('error')}")
            test_results.append(("INPUT", False))

        # 测试 6: CLICK - 点击搜索按钮
        print("\n[测试 6] CLICK - 点击搜索按钮")
        result = await engine.execute(
            keyword_def={"name": "CLICK", "category": "ui"},
            parameters={
                "selector": "#searchButton",
                "timeout": 5000
            },
            context={}
        )
        if result["success"]:
            print(f"✅ CLICK 成功: {result['message']}")
            test_results.append(("CLICK", True))
        else:
            print(f"❌ CLICK 失败: {result.get('error')}")
            test_results.append(("CLICK", False))

        # 等待搜索结果
        await asyncio.sleep(2)

        # 测试 7: 最终截图
        print("\n[测试 7] SCREENSHOT - 搜索结果截图")
        result = await engine.execute(
            keyword_def={"name": "SCREENSHOT", "category": "ui"},
            parameters={
                "path": "./screenshots/search_result.png",
                "full_page": False
            },
            context={}
        )
        if result["success"]:
            print(f"✅ SCREENSHOT 成功: {result['screenshot_path']}")
            test_results.append(("最终截图", True))
        else:
            print(f"❌ SCREENSHOT 失败: {result.get('error')}")
            test_results.append(("最终截图", False))

        # 统计结果
        print("\n" + "=" * 70)
        print("测试结果汇总")
        print("=" * 70)

        passed = sum(1 for _, success in test_results if success)
        total = len(test_results)

        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {test_name}")

        print(f"\n总计: {passed}/{total} 测试通过 ({passed*100//total}%)")

        if passed == total:
            print("\n🎉 所有测试通过！Playwright UI 关键字功能正常！")
        else:
            print(f"\n⚠️  {total - passed} 个测试失败")

        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n关闭浏览器...")
        await browser.close()
        print("✅ 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(test_all_keywords())
