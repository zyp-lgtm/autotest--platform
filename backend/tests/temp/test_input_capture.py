"""
测试输入事件捕获
专门验证输入操作是否能被正确捕获
"""
import asyncio
from playwright.async_api import async_playwright


async def test_input_capture():
    """测试输入事件捕获"""
    print("🎯 测试输入事件捕获...\n")

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
            action_type = action_data['action_type']
            if action_type == 'input':
                print(f"   📝 后端捕获输入: {action_data.get('selector')} = '{action_data.get('value')}'")
            else:
                print(f"   📝 后端捕获: {action_type}")

        await context.expose_function("captureActionToBackend", capture_action)

        # 3. 注入录制脚本（包含输入事件监听）
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

                    // 🔥 立即传递到后端
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

            // 🔥 监听输入事件 - 基于防抖
            window.__recording.inputDebounceTimers = {};

            document.addEventListener('input', function(e) {
                var selector = window.__recording.getSelector(e.target);
                var inputId = selector;

                console.log('[输入事件] 检测到输入:', selector, '当前值:', e.target.value);

                // 清除之前的定时器
                if (window.__recording.inputDebounceTimers[inputId]) {
                    clearTimeout(window.__recording.inputDebounceTimers[inputId]);
                    console.log('[输入防抖] 清除之前的定时器');
                }

                // 设置新的定时器，500ms 后记录最终值
                window.__recording.inputDebounceTimers[inputId] = setTimeout(function() {
                    console.log('[输入防抖] 500ms 到期，记录输入:', selector, '=>', e.target.value);
                    window.__recording.captureAction({
                        action_type: 'input',
                        selector: selector,
                        value: e.target.value,
                        element_tag: e.target.tagName,
                        element_text: e.target.placeholder,
                        element_name: e.target.name,
                        page_url: window.location.href,
                        page_title: document.title
                    });

                    // 记录后清除定时器引用
                    delete window.__recording.inputDebounceTimers[inputId];
                    console.log('[输入防抖] 输入记录完成');
                }, 500);
            }, true);

            console.log('[录制] ✅ 录制脚本已加载（包含输入事件监听）');
        })();
        """

        await context.add_init_script(recording_script)

        # 4. 创建页面并导航
        print("3️⃣ 导航到测试页面...")
        page = await context.new_page()
        await page.goto("https://www.wikipedia.org/")
        await asyncio.sleep(1)

        # 5. 点击搜索框
        print("\n4️⃣ 点击搜索框...")
        search_input = await page.query_selector("#searchInput")
        if search_input:
            await search_input.click()
            await asyncio.sleep(0.5)

        # 6. 慢慢输入文字
        print("\n5️⃣ 在搜索框输入 'test search'...")
        if search_input:
            # 逐字输入，模拟真实用户输入
            await search_input.type("t", delay=100)
            await asyncio.sleep(0.2)

            await search_input.type("e", delay=100)
            await asyncio.sleep(0.2)

            await search_input.type("s", delay=100)
            await asyncio.sleep(0.2)

            await search_input.type("t", delay=100)
            print("   输入: 'test'")

            # 等待足够长的时间让防抖完成
            print("\n6️⃣ 等待防抖完成（600ms）...")
            await asyncio.sleep(0.6)

            # 继续输入
            await search_input.type(" search", delay=100)
            print("   输入: ' search'")

            # 再次等待防抖
            print("\n7️⃣ 等待防抖完成（600ms）...")
            await asyncio.sleep(0.6)

        # 8. 最终验证
        print("\n8️⃣ 验证结果:")
        print(f"   后端存储的操作总数: {len(backend_storage)}")

        input_actions = [a for a in backend_storage if a['action_type'] == 'input']
        print(f"   其中输入操作数: {len(input_actions)}")

        if len(input_actions) > 0:
            print(f"\n   ✅ 成功！捕获了 {len(input_actions)} 个输入操作")
            print(f"\n📋 输入操作详情:")
            for i, action in enumerate(input_actions):
                print(f"   {i+1}. 输入: {action['selector']} = '{action.get('value', '')}'")
        else:
            print(f"   ❌ 失败！没有捕获到任何输入操作")

        print(f"\n📋 所有操作:")
        for i, action in enumerate(backend_storage):
            action_type = action['action_type']
            if action_type == 'input':
                print(f"   {i+1}. {action_type}: {action['selector']} = '{action.get('value', '')}'")
            else:
                print(f"   {i+1}. {action_type}: {action.get('selector', action.get('page_url', 'N/A'))}")

        # 保持浏览器打开
        print("\n⏳ 浏览器将保持打开 3 秒...")
        await asyncio.sleep(3)

        await browser.close()
        print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_input_capture())
