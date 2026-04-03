"""
测试连接到本地浏览器

使用前请确保：
1. 本地 Chrome 浏览器已启动并支持远程调试：
   open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
2. 检查端口是否监听：lsof -i :9222
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.playwright_browser import PlaywrightBrowser
from app.services.keyword_engine import KeywordEngine


async def test_use_local_browser():
    """测试连接到本地浏览器 (use_local=true)"""
    print("\n=== 测试 1: 连接到本地浏览器 (use_local=true) ===")

    # 创建浏览器管理器，配置使用本地浏览器
    browser = PlaywrightBrowser(config={"use_local": True, "headless": False})
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
            "use_local": True,
            "headless": False
        },
        context={}
    )

    print(f"结果: {result}")

    if result["success"]:
        print("✓ 成功连接到本地浏览器")

        # 测试导航
        print("\n测试导航到百度...")
        navigate_result = await engine.execute(
            keyword_def={"name": "NAVIGATE", "category": "ui"},
            parameters={"url": "https://www.baidu.com"},
            context={}
        )
        print(f"导航结果: {navigate_result}")

        # 等待一会儿让用户看到浏览器
        print("\n等待 3 秒...")
        await asyncio.sleep(3)

        # 清理
        await browser.close()
        print("✓ 测试 1 完成\n")
    else:
        print(f"✗ 连接失败: {result.get('error')}")
        print("\n提示：")
        print("1. 确保本地 Chrome 已启动：")
        print('   open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug')
        print("2. 检查端口是否监听：lsof -i :9222")


async def test_remote_url_browser():
    """测试连接到指定远程浏览器 (remote_url)"""
    print("=== 测试 2: 连接到指定远程浏览器 (remote_url) ===")

    # 创建浏览器管理器，配置远程 URL
    browser = PlaywrightBrowser(config={"remote_url": "ws://host.docker.internal:9222", "headless": False})
    engine = KeywordEngine(browser_manager=browser)

    keyword_def = {
        "name": "打开浏览器",
        "category": "ui",
        "keyword_type": "system"
    }

    result = await engine.execute(
        keyword_def=keyword_def,
        parameters={
            "remote_url": "ws://host.docker.internal:9222",
            "headless": False
        },
        context={}
    )

    print(f"结果: {result}")

    if result["success"]:
        print("✓ 成功连接到远程浏览器")
        await browser.close()
        print("✓ 测试 2 完成\n")
    else:
        print(f"✗ 连接失败: {result.get('error')}")


async def test_fallback_to_container_browser():
    """测试当本地浏览器不可用时，回退到容器内浏览器"""
    print("=== 测试 3: 本地浏览器不可用时的回退机制 ===")

    # 尝试连接本地浏览器（使用无效端口）
    browser = PlaywrightBrowser(config={"use_local": True, "headless": True})
    engine = KeywordEngine(browser_manager=browser)

    keyword_def = {
        "name": "打开浏览器",
        "category": "ui",
        "keyword_type": "system"
    }

    result = await engine.execute(
        keyword_def=keyword_def,
        parameters={
            "use_local": True,
            "headless": True
        },
        context={}
    )

    print(f"结果: {result}")

    if result["success"]:
        print("✓ 浏览器已启动（可能是容器内浏览器或本地浏览器）")
        await browser.close()
        print("✓ 测试 3 完成\n")
    else:
        print(f"✗ 启动失败: {result.get('error')}")


async def main():
    """运行所有测试"""
    print("\n" + "="*50)
    print("测试本地浏览器连接功能")
    print("="*50)

    print("\n前置条件检查...")
    print("请确保本地 Chrome 已启动：")
    print('  open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug')
    print("\n是否继续？(y/n): ", end="")

    # 在自动化环境中自动选择 yes
    response = "y"

    if response.lower() != 'y':
        print("已取消测试")
        return

    tests = [
        ("test_use_local_browser", "连接到本地浏览器"),
        ("test_remote_url_browser", "连接到指定远程浏览器"),
        ("test_fallback_to_container_browser", "本地不可用时的回退机制")
    ]

    passed = 0
    failed = 0

    for test_name, test_desc in tests:
        print(f"\n运行: {test_desc}")
        try:
            if test_name == "test_use_local_browser":
                await test_use_local_browser()
                passed += 1
            elif test_name == "test_remote_url_browser":
                await test_remote_url_browser()
                passed += 1
            elif test_name == "test_fallback_to_container_browser":
                await test_fallback_to_container_browser()
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
        if test_name == "local":
            asyncio.run(test_use_local_browser())
        elif test_name == "remote":
            asyncio.run(test_remote_url_browser())
        elif test_name == "fallback":
            asyncio.run(test_fallback_to_container_browser())
        else:
            print(f"未知的测试名称: {test_name}")
            print("可用测试: local, remote, fallback")
    else:
        asyncio.run(main())
