"""
测试新增的 UI 关键字
"""
import sys
import os
import asyncio

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.playwright_browser import PlaywrightBrowser
from app.services.keyword_engine import KeywordEngine


async def test_close_browser():
    """测试 CLOSE_BROWSER 关键字"""
    print("\n=== 测试 CLOSE_BROWSER ===")

    browser_manager = PlaywrightBrowser()
    keyword_engine = KeywordEngine(browser_manager)

    # 打开浏览器
    await browser_manager.start()
    print("✓ 浏览器已启动")

    # 关闭浏览器
    result = await keyword_engine.execute(
        keyword_def={"name": "CLOSE_BROWSER", "category": "ui"},
        parameters={},
        context={}
    )

    print(f"结果: {result}")
    assert result["success"] == True
    print("✓ CLOSE_BROWSER 测试通过")


async def test_switch_tab():
    """测试 SWITCH_TAB 关键字"""
    print("\n=== 测试 SWITCH_TAB ===")

    browser_manager = PlaywrightBrowser()
    keyword_engine = KeywordEngine(browser_manager)

    async with browser_manager:
        page = await browser_manager.get_page()

        # 打开多个标签页
        await page.goto("https://www.baidu.com")
        await page.wait_for_load_state("networkidle")

        # 新建标签页
        new_page = await page.context.new_page()
        await new_page.goto("https://www.example.com")
        await new_page.wait_for_load_state("networkidle")

        print(f"当前标签页数: {len(page.context.pages)}")

        # 切换到第一个标签页
        result = await keyword_engine.execute(
            keyword_def={"name": "SWITCH_TAB", "category": "ui"},
            parameters={"index": 0},
            context={}
        )

        print(f"结果: {result}")
        assert result["success"] == True
        print("✓ SWITCH_TAB 测试通过")


async def test_go_back():
    """测试 GO_BACK 关键字"""
    print("\n=== 测试 GO_BACK ===")

    browser_manager = PlaywrightBrowser()
    keyword_engine = KeywordEngine(browser_manager)

    async with browser_manager:
        page = await browser_manager.get_page()

        # 导航到百度
        await page.goto("https://www.baidu.com")
        await page.wait_for_load_state("networkidle")
        print(f"当前 URL: {page.url}")

        # 导航到 example.com
        await page.goto("https://www.example.com")
        await page.wait_for_load_state("networkidle")
        print(f"当前 URL: {page.url}")

        # 后退
        result = await keyword_engine.execute(
            keyword_def={"name": "GO_BACK", "category": "ui"},
            parameters={},
            context={}
        )

        print(f"结果: {result}")
        assert result["success"] == True
        assert "baidu.com" in result.get("url", "")
        print("✓ GO_BACK 测试通过")


async def test_refresh():
    """测试 REFRESH 关键字"""
    print("\n=== 测试 REFRESH ===")

    browser_manager = PlaywrightBrowser()
    keyword_engine = KeywordEngine(browser_manager)

    async with browser_manager:
        page = await browser_manager.get_page()

        # 导航到 example.com
        await page.goto("https://www.example.com")
        await page.wait_for_load_state("networkidle")
        print(f"当前 URL: {page.url}")

        # 刷新
        result = await keyword_engine.execute(
            keyword_def={"name": "REFRESH", "category": "ui"},
            parameters={},
            context={}
        )

        print(f"结果: {result}")
        assert result["success"] == True
        assert "example.com" in result.get("url", "")
        print("✓ REFRESH 测试通过")


async def test_double_click():
    """测试 DOUBLE_CLICK 关键字"""
    print("\n=== 测试 DOUBLE_CLICK ===")

    browser_manager = PlaywrightBrowser()
    keyword_engine = KeywordEngine(browser_manager)

    async with browser_manager:
        page = await browser_manager.get_page()

        # 导航到 example.com
        await page.goto("https://www.example.com")
        await page.wait_for_load_state("networkidle")

        # 双击 h1 元素
        result = await keyword_engine.execute(
            keyword_def={"name": "DOUBLE_CLICK", "category": "ui"},
            parameters={"selector": "h1"},
            context={}
        )

        print(f"结果: {result}")
        assert result["success"] == True
        print("✓ DOUBLE_CLICK 测试通过")


async def main():
    """运行所有测试"""
    print("=" * 50)
    print("测试新增 UI 关键字")
    print("=" * 50)

    try:
        # 依次运行测试
        await test_close_browser()
        await test_switch_tab()
        await test_go_back()
        await test_refresh()
        await test_double_click()

        print("\n" + "=" * 50)
        print("✅ 所有测试通过!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 简单测试模式
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        asyncio.run(test_refresh())
    else:
        asyncio.run(main())
