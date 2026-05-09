"""
测试 Playwright expose_function 功能
"""
import asyncio
from playwright.async_api import async_playwright


async def test_expose_function():
    """测试 expose_function 是否正常工作"""
    print("🧪 测试 Playwright expose_function...\n")

    backend_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # 定义要暴露的函数
        async def my_test_function(data):
            backend_calls.append(data)
            print(f"✅ 后端收到: {data}")

        # 暴露函数
        print("1️⃣ 暴露函数到浏览器...")
        await context.expose_function("myTestFunction", my_test_function)

        # 创建页面
        print("2️⃣ 创建页面...")
        page = await context.new_page()

        # 检查函数是否存在
        print("3️⃣ 检查函数是否可用...")
        is_available = await page.evaluate("typeof window.myTestFunction !== 'undefined'")
        print(f"   函数可用: {is_available}")

        if not is_available:
            print("   ❌ 函数不可用!")
            await browser.close()
            return

        # 调用函数
        print("\n4️⃣ 从浏览器调用函数...")
        await page.evaluate("window.myTestFunction('测试数据1')")

        await asyncio.sleep(0.5)

        print("\n5️⃣ 再次调用函数...")
        await page.evaluate("window.myTestFunction({name: '测试', value: 123})")

        await asyncio.sleep(0.5)

        # 检查结果
        print(f"\n6️⃣ 后端调用次数: {len(backend_calls)}")
        for i, call in enumerate(backend_calls):
            print(f"   调用 {i+1}: {call}")

        # 测试跨页面导航
        print("\n7️⃣ 测试跨页面导航...")
        await page.goto("https://example.com")
        await asyncio.sleep(1)

        # 检查函数是否仍然可用
        is_available_after = await page.evaluate("typeof window.myTestFunction !== 'undefined'")
        print(f"   导航后函数可用: {is_available_after}")

        if is_available_after:
            print("\n8️⃣ 导航后调用函数...")
            await page.evaluate("window.myTestFunction('导航后测试')")

            await asyncio.sleep(0.5)
            print(f"   后端调用次数: {len(backend_calls)}")

        await asyncio.sleep(2)
        await browser.close()

        print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_expose_function())
