"""
录制功能调试脚本
测试 Playwright 录制脚本是否正常工作
"""
import asyncio
from playwright.async_api import async_playwright

# 录制脚本（从 recorder.py 复制）
RECORDING_SCRIPT = """
(function() {
    window.__recording = {
        actions: [],
        startTime: Date.now(),
        initialized: false,

        captureAction: function(action) {
            action.timestamp = Date.now() - window.__recording.startTime;
            window.__recording.actions.push(action);
            console.log('[录制]', action.action_type, action.selector || action.page_url);
        },

        getSelector: function(element) {
            if (element.id) {
                return '#' + element.id;
            }
            if (element.className) {
                return '.' + element.className.split(' ')[0];
            }
            if (element.name) {
                return '[name=' + element.name + ']';
            }
            return element.tagName.toLowerCase();
        },

        captureNavigation: function() {
            var currentUrl = window.location.href;
            if (window.__recording.lastCapturedUrl === currentUrl) {
                return;
            }
            if (currentUrl === 'about:blank') {
                return;
            }
            window.__recording.lastCapturedUrl = currentUrl;
            window.__recording.captureAction({
                action_type: 'navigate',
                selector: '',
                page_url: currentUrl,
                page_title: document.title
            });
        }
    };

    // 捕获点击
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

    // 捕获输入
    document.addEventListener('input', function(e) {
        var selector = window.__recording.getSelector(e.target);
        window.__recording.captureAction({
            action_type: 'input',
            selector: selector,
            value: e.target.value,
            element_tag: e.target.tagName,
            page_url: window.location.href,
            page_title: document.title
        });
    }, true);

    console.log('[录制] ✅ 录制脚本已加载');
})();
"""


async def test_recording():
    """测试录制功能"""
    print("🎬 开始测试录制功能...\n")

    async with async_playwright() as p:
        # 1. 启动浏览器
        print("1️⃣ 启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})

        # 2. 注入录制脚本
        print("2️⃣ 注入录制脚本...")
        await context.add_init_script(RECORDING_SCRIPT)

        # 3. 创建页面
        print("3️⃣ 创建新页面...")
        page = await context.new_page()

        # 4. 检查脚本是否加载
        print("4️⃣ 检查录制脚本状态...")
        is_loaded = await page.evaluate("window.__recording ? true : false")
        print(f"   录制脚本已加载: {is_loaded}")

        if not is_loaded:
            print("   ❌ 录制脚本未加载!")
            await browser.close()
            return

        actions_count = await page.evaluate("window.__recording.actions.length")
        print(f"   当前操作数: {actions_count}")

        # 5. 导航到测试页面
        print("\n5️⃣ 导航到测试页面...")
        await page.goto("https://example.com")
        await asyncio.sleep(1)  # 等待页面加载

        # 6. 检查是否捕获了导航
        print("6️⃣ 检查捕获的操作...")
        actions = await page.evaluate("window.__recording.actions")
        print(f"   捕获的操作数: {len(actions)}")

        for i, action in enumerate(actions):
            print(f"   操作 {i+1}: {action['action_type']} - {action.get('page_url', action.get('selector', 'N/A'))}")

        # 7. 模拟用户操作
        print("\n7️⃣ 模拟用户操作...")
        print("   点击页面...")

        # 点击页面主体
        await page.click("body")
        await asyncio.sleep(0.5)

        # 检查捕获的操作
        actions = await page.evaluate("window.__recording.actions")
        print(f"   捕获的操作数: {len(actions)}")

        for i, action in enumerate(actions):
            print(f"   操作 {i+1}: {action['action_type']} - {action.get('page_url', action.get('selector', 'N/A'))}")

        # 8. 导航到另一个页面
        print("\n8️⃣ 导航到另一个页面...")
        await page.goto("https://www.wikipedia.org/")
        await asyncio.sleep(1)

        actions = await page.evaluate("window.__recording.actions")
        print(f"   捕获的操作数: {len(actions)}")

        for i, action in enumerate(actions):
            print(f"   操作 {i+1}: {action['action_type']} - {action.get('page_url', action.get('selector', 'N/A'))}")

        # 9. 在输入框输入文字
        print("\n9️⃣ 在搜索框输入文字...")
        try:
            # Wikipedia 搜索框
            search_input = await page.query_selector("#searchInput")
            if search_input:
                await search_input.click()
                await search_input.type("test search")
                await asyncio.sleep(1)  # 等待防抖

                actions = await page.evaluate("window.__recording.actions")
                print(f"   捕获的操作数: {len(actions)}")

                for i, action in enumerate(actions):
                    print(f"   操作 {i+1}: {action['action_type']} - {action.get('page_url', action.get('selector', 'N/A'))}")
            else:
                print("   ⚠️ 未找到搜索框")
        except Exception as e:
            print(f"   ⚠️ 输入操作失败: {e}")

        # 10. 最终总结
        print("\n🔟 最终总结:")
        final_actions = await page.evaluate("window.__recording.actions")
        print(f"   总共捕获: {len(final_actions)} 个操作")

        print("\n操作详情:")
        for i, action in enumerate(final_actions):
            action_type = action['action_type']
            if action_type == 'navigate':
                print(f"   {i+1}. 导航到: {action['page_url']}")
            elif action_type == 'click':
                print(f"   {i+1}. 点击: {action['selector']}")
            elif action_type == 'input':
                print(f"   {i+1}. 输入: {action['selector']} = {action.get('value', '')}")

        # 保持浏览器打开一段时间以便观察
        print("\n⏳ 浏览器将保持打开 5 秒以便观察...")
        await asyncio.sleep(5)

        await browser.close()
        print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_recording())
