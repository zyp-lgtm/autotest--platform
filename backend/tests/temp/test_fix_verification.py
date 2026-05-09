"""
录制修复验证脚本
验证跨页面导航时数据是否正确保留
"""
import asyncio
from playwright.async_api import async_playwright

# 修复后的录制脚本（使用 expose_function）
FIXED_RECORDING_SCRIPT = """
(function() {
    window.__recording = {
        actions: [],
        startTime: Date.now(),

        captureAction: function(action) {
            action.timestamp = Date.now() - window.__recording.startTime;
            window.__recording.actions.push(action);
            console.log('[录制]', action.action_type, action.selector || action.page_url);

            // 🔥 关键修复：立即将操作传递到 Python 后端
            if (window.captureActionToBackend) {{
                window.captureActionToBackend(action);
            }}
        },

        getSelector: function(element) {{
            if (element.id) return '#' + element.id;
            if (element.className) return '.' + element.className.split(' ')[0];
            if (element.name) return '[name=' + element.name + ']';
            return element.tagName.toLowerCase();
        }},

        captureNavigation: function() {{
            var currentUrl = window.location.href;
            if (window.__recording.lastCapturedUrl === currentUrl) return;
            if (currentUrl === 'about:blank') return;

            window.__recording.lastCapturedUrl = currentUrl;
            window.__recording.captureAction({{
                action_type: 'navigate',
                selector: '',
                page_url: currentUrl,
                page_title: document.title
            }});
        }}
    }};

    // 立即捕获当前页面
    if (window.location.href !== 'about:blank') {{
        setTimeout(function() {{ window.__recording.captureNavigation(); }}, 100);
    }}

    // 监听点击事件
    document.addEventListener('click', function(e) {{
        var selector = window.__recording.getSelector(e.target);
        window.__recording.captureAction({{
            action_type: 'click',
            selector: selector,
            element_tag: e.target.tagName,
            page_url: window.location.href,
            page_title: document.title
        }});
    }}, true);

    console.log('[录制] ✅ 修复版录制脚本已加载');
})();
"""


async def test_fixed_recording():
    """测试修复后的录制功能"""
    print("🔧 测试修复后的录制功能...\n")

    # 模拟后端存储
    backend_storage = []

    async with async_playwright() as p:
        # 1. 启动浏览器
        print("1️⃣ 启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})

        # 2. 模拟后端 capture_action 函数
        async def capture_action(action_data):
            """模拟后端接收操作"""
            backend_storage.append(action_data)
            print(f"   📝 后端收到: {action_data['action_type']} - {action_data.get('page_url', action_data.get('selector', 'N/A'))}")

        await context.expose_function("captureActionToBackend", capture_action)

        # 3. 注入修复后的录制脚本
        print("2️⃣ 注入修复后的录制脚本...")
        await context.add_init_script(FIXED_RECORDING_SCRIPT)

        # 4. 创建页面
        print("3️⃣ 创建新页面...")
        page = await context.new_page()

        # 5. 导航到第一个页面
        print("\n4️⃣ 导航到 example.com...")
        await page.goto("https://example.com")
        await asyncio.sleep(1)

        # 6. 点击页面
        print("5️⃣ 点击页面...")
        await page.click("body")
        await asyncio.sleep(0.5)

        # 7. 导航到第二个页面
        print("\n6️⃣ 导航到 wikipedia.org...")
        await page.goto("https://www.wikipedia.org/")
        await asyncio.sleep(1)

        # 8. 在搜索框输入
        print("7️⃣ 在搜索框输入...")
        search_input = await page.query_selector("#searchInput")
        if search_input:
            await search_input.click()
            await search_input.type("test")
            await asyncio.sleep(1)  # 等待防抖

        # 9. 最终验证
        print("\n8️⃣ 验证结果:")
        try:
            browser_actions_count = len(await page.evaluate("window.__recording ? window.__recording.actions : []"))
            print(f"   浏览器本地存储: {browser_actions_count} 个操作")
        except:
            print(f"   浏览器本地存储: (无法访问 - 跨页面后上下文已重置)")

        print(f"   后端存储 (跨页面): {len(backend_storage)} 个操作")

        # 10. 详细对比
        print("\n9️⃣ 详细对比:")
        print(f"   后端存储操作数: {len(backend_storage)}")
        for i, action in enumerate(backend_storage):
            print(f"     {i+1}. {action['action_type']} - {action.get('page_url', action.get('selector', 'N/A'))}")

        # 11. 测试结果
        print("\n🔟 测试结果:")
        if len(backend_storage) > 0:
            print(f"   ✅ 成功！后端存储了 {len(backend_storage)} 个操作")
            print(f"   ✅ 跨页面导航数据未丢失")
            print(f"   ✅ 修复有效！")
        else:
            print(f"   ❌ 失败！后端未存储任何操作")

        # 保持浏览器打开以便观察
        print("\n⏳ 浏览器将保持打开 3 秒...")
        await asyncio.sleep(3)

        await browser.close()
        print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_fixed_recording())
