"""
测试 "打开浏览器" 关键字
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.playwright_browser import PlaywrightBrowser
from app.services.keyword_engine import KeywordEngine


async def test_open_browser_chromium():
    """测试打开 Chromium 浏览器"""
    print("\n=== 测试 1: 打开 Chromium 浏览器 (headless=True) ===")

    browser = PlaywrightBrowser(config={"browser_type": "chromium", "headless": True})
    engine = KeywordEngine(browser_manager=browser)

    # 模拟关键字定义
    keyword_def = {
        "name": "打开浏览器",
        "category": "ui",
        "keyword_type": "system"
    }

    # 执行关键字
    result = await engine.execute(
        keyword_def=keyword_def,
        parameters={
            "browser_type": "chromium",
            "headless": True
        },
        context={}
    )

    print(f"结果: {result}")
    assert result["success"] == True
    assert result["browser_type"] == "chromium"

    # 清理
    await browser.close()
    print("✓ 测试 1 通过\n")


async def test_open_browser_firefox():
    """测试打开 Firefox 浏览器"""
    print("=== 测试 2: 打开 Firefox 浏览器 (headless=True) ===")

    browser = PlaywrightBrowser(config={"browser_type": "firefox", "headless": True})
    engine = KeywordEngine(browser_manager=browser)

    keyword_def = {
        "name": "打开浏览器",
        "category": "ui",
        "keyword_type": "system"
    }

    result = await engine.execute(
        keyword_def=keyword_def,
        parameters={
            "browser_type": "firefox",
            "headless": True
        },
        context={}
    )

    print(f"结果: {result}")
    assert result["success"] == True
    assert result["browser_type"] == "firefox"

    await browser.close()
    print("✓ 测试 2 通过\n")


async def test_switch_browser():
    """测试切换浏览器类型"""
    print("=== 测试 3: 切换浏览器类型 ===")

    browser = PlaywrightBrowser(config={"browser_type": "chromium", "headless": True})
    engine = KeywordEngine(browser_manager=browser)

    keyword_def = {
        "name": "打开浏览器",
        "category": "ui",
        "keyword_type": "system"
    }

    # 先打开 Chromium
    result1 = await engine.execute(
        keyword_def=keyword_def,
        parameters={"browser_type": "chromium", "headless": True},
        context={}
    )
    print(f"第一次打开: {result1}")
    assert result1["success"] == True
    assert result1["browser_type"] == "chromium"

    # 切换到 Firefox
    result2 = await engine.execute(
        keyword_def=keyword_def,
        parameters={"browser_type": "firefox", "headless": True},
        context={}
    )
    print(f"切换到 Firefox: {result2}")
    assert result2["success"] == True
    assert result2["browser_type"] == "firefox"

    await browser.close()
    print("✓ 测试 3 通过\n")


async def test_invalid_browser_type():
    """测试无效的浏览器类型"""
    print("=== 测试 4: 无效的浏览器类型 ===")

    browser = PlaywrightBrowser(config={})
    engine = KeywordEngine(browser_manager=browser)

    keyword_def = {
        "name": "打开浏览器",
        "category": "ui",
        "keyword_type": "system"
    }

    result = await engine.execute(
        keyword_def=keyword_def,
        parameters={"browser_type": "invalid_type", "headless": True},
        context={}
    )

    print(f"结果: {result}")
    assert result["success"] == False
    assert "无效的浏览器类型" in result["error"]

    print("✓ 测试 4 通过\n")


async def test_no_restart_same_config():
    """测试相同配置不重启"""
    print("=== 测试 5: 相同配置不重启 ===")

    browser = PlaywrightBrowser(config={"browser_type": "chromium", "headless": True})
    engine = KeywordEngine(browser_manager=browser)

    keyword_def = {
        "name": "打开浏览器",
        "category": "ui",
        "keyword_type": "system"
    }

    # 第一次打开
    result1 = await engine.execute(
        keyword_def=keyword_def,
        parameters={"browser_type": "chromium", "headless": True},
        context={}
    )
    print(f"第一次: {result1}")

    # 第二次使用相同配置
    result2 = await engine.execute(
        keyword_def=keyword_def,
        parameters={"browser_type": "chromium", "headless": True},
        context={}
    )
    print(f"第二次 (相同配置): {result2}")

    assert result2["success"] == True
    assert "已在运行" in result2["message"]

    await browser.close()
    print("✓ 测试 5 通过\n")


async def main():
    """运行所有测试"""
    print("\n" + "="*50)
    print("测试 '打开浏览器' 关键字")
    print("="*50)

    tests = [
        test_open_browser_chromium,
        test_open_browser_firefox,
        test_switch_browser,
        test_invalid_browser_type,
        test_no_restart_same_config
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"✗ 测试失败: {e}\n")
            failed += 1

    print("="*50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*50 + "\n")


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        test_func = {
            "chromium": test_open_browser_chromium,
            "firefox": test_open_browser_firefox,
            "switch": test_switch_browser,
            "invalid": test_invalid_browser_type,
            "no_restart": test_no_restart_same_config
        }.get(test_name)

        if test_func:
            asyncio.run(test_func())
        else:
            print(f"未知的测试名称: {test_name}")
            print("可用测试: chromium, firefox, switch, invalid, no_restart")
    else:
        asyncio.run(main())
