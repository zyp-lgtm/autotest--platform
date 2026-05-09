"""
完整录制流程测试 - 模拟真实使用场景
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def test_real_recording_scenario():
    """测试真实的录制场景，包括防抖和所有操作"""
    print("🎬 测试真实录制场景...\n")

    # 模拟后端存储
    backend_storage = []

    async with async_playwright() as p:
        # 1. 启动浏览器
        print("1️⃣ 启动浏览器和上下文...")
        browser = await p.chromium.launch(headless=False, slow_mo=100)  # 慢速模式，更接近真实操作
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})

        # 2. 定义后端捕获函数
        async def capture_action(action_data):
            """后端接收操作"""
            backend_storage.append(action_data)
            action_type = action_data['action_type']
            if action_type == 'input':
                print(f"   ✓ 后端捕获输入: {action_data.get('selector', 'N/A')} = '{action_data.get('value', 'N/A')}'")
            else:
                print(f"   ✓ 后端捕获: {action_type}")

        await context.expose_function("captureActionToBackend", capture_action)

        # 3. 注入完整的录制脚本
        print("2️⃣ 注入完整录制脚本...")
        recording_script = """
        (function() {
            window.__recording = {
                actions: [],
                startTime: Date.now(),
                lastCapturedUrl: '',

                captureAction: function(action) {
                    action.timestamp = Date.now() - window.__recording.startTime;
                    window.__recording.actions.push(action);
                    console.log('[录制]', action.action_type, action.selector || action.page_url);

                    // 立即传递到后端
                    if (window.captureActionToBackend) {
                        try {
                            window.captureActionToBackend(action);
                        } catch(e) {
                            console.error('[录制] 传递到后端失败:', e);
                        }
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

            // 立即捕获当前页面
            if (window.location.href !== 'about:blank') {
                setTimeout(function() {
                    window.__recording.captureNavigation();
                }, 100);
            }

            // 监听点击事件
            document.addEventListener('click', function(e) {
                var selector = window.__recording.getSelector(e.target);
                window.__recording.captureAction({
                    action_type: 'click',
                    selector: selector,
                    element_tag: e.target.tagName,
                    element_text: e.target.textContent ? e.target.textContent.trim().substring(0, 50) : null,
                    page_url: window.location.href,
                    page_title: document.title
                });
                console.log('[事件] 捕获点击:', selector);
            }, true);

            // 监听输入事件 - 带防抖
            window.__recording.inputDebounceTimers = {};

            document.addEventListener('input', function(e) {
                var selector = window.__recording.getSelector(e.target);
                var inputId = selector;

                console.log('[事件] 检测到输入事件:', selector, '值:', e.target.value);

                // 清除之前的定时器
                if (window.__recording.inputDebounceTimers[inputId]) {
                    clearTimeout(window.__recording.inputDebounceTimers[inputId]);
                    console.log('[防抖] 清除之前的定时器');
                }

                // 设置新的定时器，300ms 后记录
                window.__recording.inputDebounceTimers[inputId] = setTimeout(function() {
                    console.log('[防抖] 300ms到期，记录输入:', selector, '=>', e.target.value);
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
                    console.log('[防抖] 输入记录完成，定时器已删除');
                }, 300);
            }, true);

            // 监听导航
            window.addEventListener('popstate', function() {
                setTimeout(function() {
                    window.__recording.captureNavigation();
                }, 100);
            });

            window.addEventListener('hashchange', function() {
                window.__recording.captureNavigation();
            });

            let lastUrl = location.href;
            new MutationObserver(function(mutations) {
                if (location.href !== lastUrl) {
                    lastUrl = location.href;
                    setTimeout(function() {
                        window.__recording.captureNavigation();
                    }, 200);
                }
            }).observe(document, { subtree: true, childList: true });

            (function() {
                var originalPushState = history.pushState;
                var originalReplaceState = history.replaceState;

                history.pushState = function() {
                    originalPushState.apply(this, arguments);
                    setTimeout(function() {
                        window.__recording.captureNavigation();
                    }, 100);
                };

                history.replaceState = function() {
                    originalReplaceState.apply(this, arguments);
                    setTimeout(function() {
                        window.__recording.captureNavigation();
                    }, 100);
                };
            })();

            console.log('[录制] ✅ 录制脚本已加载（包含输入监听，300ms防抖）');
        })();
        """

        await context.add_init_script(recording_script)

        # 4. 创建页面
        print("3️⃣ 创建页面并导航...")
        page = await context.new_page()

        # 5. 导航到Wikipedia
        print("\n4️⃣ 导航到 Wikipedia...")
        await page.goto("https://www.wikipedia.org/")
        await asyncio.sleep(2)  # 等待页面完全加载

        # 6. 点击搜索框
        print("\n5️⃣ 点击搜索框...")
        search_input = await page.query_selector("#searchInput")
        if search_input:
            await search_input.click()
            await asyncio.sleep(0.5)
            print("   ✓ 已点击搜索框")

        # 7. 输入文字（模拟真实用户输入）
        print("\n6️⃣ 输入 'hello world'...")
        if search_input:
            # 逐字符输入，模拟真实用户
            await search_input.type("h", delay=50)
            await asyncio.sleep(0.1)

            await search_input.type("e", delay=50)
            await asyncio.sleep(0.1)

            await search_input.type("l", delay=50)
            await asyncio.sleep(0.1)

            await search_input.type("l", delay=50)
            await asyncio.sleep(0.1)

            await search_input.type("o", delay=50)
            print("   ✓ 已输入: 'hello'")

            # 重要：等待足够时间让防抖完成
            print("\n7️⃣ 等待防抖完成（400ms）...")
            await asyncio.sleep(0.4)  # 300ms防抖 + 100ms缓冲

            # 继续输入
            await search_input.type(" world", delay=50)
            print("   ✓ 已输入: ' world'")

            # 再次等待防抖
            print("\n8️⃣ 再次等待防抖（400ms）...")
            await asyncio.sleep(0.4)

        # 9. 点击搜索按钮
        print("\n9️⃣ 点击搜索按钮...")
        search_button = await page.query_selector("button[type='submit']")
        if search_button:
            await search_button.click()
            await asyncio.sleep(1)

        # 10. 最终检查
        print("\n🔟 检查浏览器控制台...")
        try:
            browser_actions = await page.evaluate("window.__recording ? window.__recording.actions : []")
            print(f"   浏览器本地操作数: {len(browser_actions)}")
        except:
            print("   浏览器本地无法访问（跨页面）")

        print(f"\n   后端存储操作数: {len(backend_storage)}")

        # 11. 详细分析
        print("\n📊 详细分析:")
        input_actions = [a for a in backend_storage if a['action_type'] == 'input']
        click_actions = [a for a in backend_storage if a['action_type'] == 'click']
        navigate_actions = [a for a in backend_storage if a['action_type'] == 'navigate']

        print(f"   导航操作: {len(navigate_actions)} 个")
        print(f"   点击操作: {len(click_actions)} 个")
        print(f"   输入操作: {len(input_actions)} 个")

        if len(input_actions) > 0:
            print(f"\n   ✅ 成功！捕获了 {len(input_actions)} 个输入操作")
            print(f"\n📋 输入操作详情:")
            for i, action in enumerate(input_actions):
                print(f"      {i+1}. {action['selector']} = '{action.get('value', 'N/A')}'")
        else:
            print(f"\n   ❌ 问题：没有捕获到任何输入操作")
            print(f"\n🔍 可能原因:")
            print(f"   1. 输入事件监听器未正确加载")
            print(f"   2. 防抖时间设置有问题")
            print(f"   3. expose_function 未正常工作")

        print(f"\n📋 所有捕获的操作:")
        for i, action in enumerate(backend_storage):
            action_type = action['action_type']
            if action_type == 'input':
                print(f"   {i+1}. {action_type}: {action['selector']} = '{action.get('value', 'N/A')}'")
            elif action_type == 'navigate':
                print(f"   {i+1}. {action_type}: {action.get('page_url', 'N/A')}")
            else:
                print(f"   {i+1}. {action_type}: {action.get('selector', 'N/A')}")

        # 保持浏览器打开以便观察
        print("\n⏳ 浏览器将保持打开 5 秒，请查看控制台日志...")
        await asyncio.sleep(5)

        await browser.close()
        print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_real_recording_scenario())
