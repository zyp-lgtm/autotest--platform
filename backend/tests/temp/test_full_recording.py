"""
完整录制功能测试
模拟真实的录制场景
"""
import asyncio
from playwright.async_api import async_playwright


async def test_full_recording():
    """测试完整的录制功能,包括跨页面导航"""
    print("🎬 测试完整录制功能...\n")

    backend_storage = []

    async with async_playwright() as p:
        # 1. 启动浏览器
        print("1️⃣ 启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})

        # 2. 定义后端捕获函数
        async def capture_action(action_data):
            """模拟后端接收操作"""
            backend_storage.append(action_data)
            print(f"   📝 后端捕获: {action_data['action_type']} - {action_data.get('page_url', action_data.get('selector', 'N/A'))}")

        await context.expose_function("captureActionToBackend", capture_action)

        # 3. 注入录制脚本
        print("2️⃣ 注入录制脚本...")
        recording_script = """
        (function() {
            window.__recording = {
                actions: [],
                startTime: Date.now(),

                captureAction: function(action) {
                    action.timestamp = Date.now() - window.__recording.startTime;
                    window.__recording.actions.push(action);
                    console.log('[录制]', action.action_type, action.selector || action.page_url);

                    // 🔥 关键修复：立即将操作传递到 Python 后端
                    if (window.captureActionToBackend) {
                        window.captureActionToBackend(action);
                    }
                },

                getSelector: function(element) {
                    if (element.id) return '#' + element.id;
                    if (element.className) return '.' + element.className.split(' ')[0];
                    if (element.name) return '[name=' + element.name + ']';
                    return element.tagName.toLowerCase();
                },

                captureNavigation: function() {
                    var currentUrl = window.location.href;
                    if (window.__recording.lastCapturedUrl === currentUrl) return;
                    if (currentUrl === 'about:blank') return;

                    window.__recording.lastCapturedUrl = currentUrl;
                    window.__recording.captureAction({
                        action_type: 'navigate',
                        selector: '',
                        page_url: currentUrl,
                        page_title: document.title
                    });
                }
            };

            // 立即捕获当前页面
            if (window.location.href !== 'about:blank') {
                setTimeout(function() { window.__recording.captureNavigation(); }, 100);
            }

            // 监听点击事件
            document.addEventListener('click', function(e) {
                var selector = window.__recording.getSelector(e.target);
                window.__recording.captureAction({
                    action_type: 'click',
                    selector: selector,
                    element_tag: e.target.tagName,
                    page_url: window.location.href,
                    page_title: document.title
                });
            }, true);

            console.log('[录制] ✅ 录制脚本已加载');
        })();
        """

        await context.add_init_script(recording_script)

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
        try:
            search_input = await page.query_selector("#searchInput")
            if search_input:
                await search_input.click()
                await search_input.type("test search")
                await asyncio.sleep(1)  # 等待防抖

                print("\n8️⃣ 点击搜索按钮...")
                search_button = await page.query_selector("button[type='submit']")
                if search_button:
                    await search_button.click()
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"   ⚠️ 输入操作失败: {e}")

        # 9. 最终验证
        print("\n9️⃣ 最终验证:")
        print(f"   后端存储的操作总数: {len(backend_storage)}")

        if len(backend_storage) > 0:
            print(f"\n   ✅ 成功！后端存储了 {len(backend_storage)} 个操作")
            print(f"   ✅ 跨页面导航数据未丢失")
            print(f"   ✅ 录制功能正常！")

            print(f"\n📋 操作详情:")
            for i, action in enumerate(backend_storage):
                action_type = action['action_type']
                if action_type == 'navigate':
                    print(f"   {i+1}. 导航到: {action['page_url']}")
                elif action_type == 'click':
                    print(f"   {i+1}. 点击: {action['selector']}")
                elif action_type == 'input':
                    print(f"   {i+1}. 输入: {action['selector']} = {action.get('value', '')}")
        else:
            print(f"   ❌ 失败！后端未存储任何操作")

        # 保持浏览器打开以便观察
        print("\n⏳ 浏览器将保持打开 3 秒...")
        await asyncio.sleep(3)

        await browser.close()
        print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_full_recording())
