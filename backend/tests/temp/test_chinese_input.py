"""
测试中文输入法支持
验证 compositionend 事件是否正常工作
"""
import asyncio
from playwright.async_api import async_playwright


async def test_chinese_input():
    """测试中文输入法"""
    print("🇨🇳 测试中文输入法支持...\n")

    backend_storage = []

    async with async_playwright() as p:
        print("1️⃣ 启动浏览器...")
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})

        async def capture_action(action_data):
            backend_storage.append(action_data)
            action_type = action_data['action_type']
            if action_type == 'input':
                print(f"   ✅ 捕获输入: {action_data.get('selector')} = '{action_data.get('value')}'")
            else:
                print(f"   ✅ 捕获: {action_type}")

        await context.expose_function("captureActionToBackend", capture_action)

        print("2️⃣ 注入录制脚本（包含中文输入法支持）...")
        recording_script = """
        (function() {
            window.__recording = {
                actions: [],
                startTime: Date.now(),

                captureAction: function(action) {
                    action.timestamp = Date.now() - window.__recording.startTime;
                    window.__recording.actions.push(action);
                    console.log('[录制]', action.action_type, action.selector || action.page_url);

                    if (window.captureActionToBackend) {
                        window.captureActionToBackend(action);
                    }
                },

                getSelector: function(element) {
                    if (element.id) return '#' + element.id;
                    if (element.className && element.className.length > 0) {
                        return '.' + element.className.split(' ')[0];
                    }
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

            // 导航事件
            if (window.location.href !== 'about:blank') {
                setTimeout(function() { window.__recording.captureNavigation(); }, 100);
            }

            // 点击事件
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

            // 🔥 中文输入法支持：compositionend 事件
            window.__recording.inputDebounceTimers = {};

            document.addEventListener('compositionend', function(e) {
                var selector = window.__recording.getSelector(e.target);
                console.log('[录制] 检测到中文输入完成:', selector, '=>', e.target.value);

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
            }, true);

            // 英文输入：input 事件（检查 isComposing）
            document.addEventListener('input', function(e) {
                var selector = window.__recording.getSelector(e.target);

                if (e.target.isComposing) {
                    console.log('[录制] 正在使用中文输入法，等待 compositionend');
                    return;
                }

                // 防抖处理
                var inputId = selector;
                if (window.__recording.inputDebounceTimers[inputId]) {
                    clearTimeout(window.__recording.inputDebounceTimers[inputId]);
                }

                window.__recording.inputDebounceTimers[inputId] = setTimeout(function() {
                    console.log('[录制] 英文输入:', selector, '=>', e.target.value);
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
                    delete window.__recording.inputDebounceTimers[inputId];
                }, 300);
            }, true);

            console.log('[录制] ✅ 录制脚本已加载（支持中文输入法）');
        })();
        """

        await context.add_init_script(recording_script)

        print("3️⃣ 创建页面并导航...")
        page = await context.new_page()
        await page.goto("https://www.wikipedia.org/")
        await asyncio.sleep(2)

        print("\n4️⃣ 点击搜索框...")
        search_input = await page.query_selector("#searchInput")
        if search_input:
            await search_input.click()
            await asyncio.sleep(0.5)

        print("\n5️⃣ 测试中文输入...")
        print("   提示：请手动在搜索框中输入中文（例如：测试）")
        print("   然后按回车或点击搜索按钮")

        # 等待用户手动输入
        print("\n   等待用户输入（15秒）...")
        await asyncio.sleep(15)

        print("\n6️⃣ 检查结果...")
        print(f"   后端存储的操作总数: {len(backend_storage)}")

        input_actions = [a for a in backend_storage if a['action_type'] == 'input']
        print(f"   输入操作数: {len(input_actions)}")

        if len(input_actions) > 0:
            print(f"\n   ✅ 成功！捕获了 {len(input_actions)} 个输入操作")
            print(f"\n📋 输入详情:")
            for i, action in enumerate(input_actions):
                print(f"   {i+1}. {action['selector']} = '{action.get('value', 'N/A')}'")
        else:
            print(f"\n   ❌ 未捕获到输入操作")
            print(f"\n💡 提示：请确保使用中文输入法并完成了输入（compositionend）")

        print(f"\n📋 所有操作:")
        for i, action in enumerate(backend_storage):
            action_type = action['action_type']
            if action_type == 'input':
                print(f"   {i+1}. {action_type}: {action['selector']} = '{action.get('value', 'N/A')}'")
            elif action_type == 'navigate':
                print(f"   {i+1}. {action_type}: {action.get('page_url', 'N/A')}")
            else:
                print(f"   {i+1}. {action_type}: {action.get('selector', 'N/A')}")

        print("\n⏳ 浏览器将保持打开 5 秒...")
        await asyncio.sleep(5)

        await browser.close()
        print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_chinese_input())
