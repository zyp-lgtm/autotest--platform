"""
录制器服务 - 浏览器录制核心功能
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import json


@dataclass
class CapturedAction:
    """捕获的操作"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = 0.0
    action_type: str = ""  # click, input, navigate, select, etc.
    selector: str = ""
    selector_strategy: str = "css"  # css, xpath, text
    value: Optional[str] = None

    # 元素信息
    element_tag: str = ""
    element_text: Optional[str] = None
    element_attributes: Dict[str, str] = field(default_factory=dict)

    # 页面信息
    page_url: str = ""
    page_title: str = ""


@dataclass
class RecordingSession:
    """录制会话"""
    id: str
    project_id: str
    scenario_name: str
    status: str = "preparing"  # preparing, recording, paused, processing, completed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Playwright 对象
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None

    # 捕获的数据
    captured_actions: List[CapturedAction] = field(default_factory=list)

    # 提取的数据模式
    data_patterns: List[Dict[str, Any]] = field(default_factory=list)

    # 🔥 新增：录制配置
    config: Dict[str, Any] = field(default_factory=lambda: {
        "enableSmartWait": True,
        "autoExtractVariables": True,
        "mergeContinuousInputs": True
    })


class BrowserRecorder:
    """浏览器录制器"""

    def __init__(self):
        self.sessions: Dict[str, RecordingSession] = {}
        self._recording_script = """
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
                    // 生成CSS选择器
                    return element.tagName.toLowerCase();
                },

                // 捕获页面导航
                captureNavigation: function() {
                    var currentUrl = window.location.href;

                    // 避免重复捕获相同的URL
                    if (window.__recording.lastCapturedUrl === currentUrl) {
                        return;
                    }

                    // 跳过 about:blank 页面
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

            // 立即捕获当前页面（如果不是 about:blank）
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
            }, true);

            // 监听输入事件 - 🔥 输入去重：基于500ms防抖
            window.__recording.inputDebounceTimers = {};

            document.addEventListener('input', function(e) {
                var selector = window.__recording.getSelector(e.target);
                var inputId = selector; // 使用选择器作为唯一标识

                // 清除之前的定时器
                if (window.__recording.inputDebounceTimers[inputId]) {
                    clearTimeout(window.__recording.inputDebounceTimers[inputId]);
                }

                // 设置新的定时器，500ms 后记录最终值
                window.__recording.inputDebounceTimers[inputId] = setTimeout(function() {
                    window.__recording.captureAction({
                        action_type: 'input',
                        selector: selector,
                        value: e.target.value,  // 最终值
                        element_tag: e.target.tagName,
                        element_text: e.target.placeholder,
                        element_name: e.target.name,  // 新增：name 属性
                        page_url: window.location.href,
                        page_title: document.title
                    });

                    // 记录后清除定时器引用
                    delete window.__recording.inputDebounceTimers[inputId];
                    console.log('[录制] 输入去重完成:', selector, '=>', e.target.value);
                }, 500);  // 500ms 防抖
            }, true);

            // 监听导航事件（使用多种方法确保不遗漏）

            // 方法1: 使用 popstate 监听浏览器前进后退
            window.addEventListener('popstate', function() {
                setTimeout(function() {
                    window.__recording.captureNavigation();
                }, 100);
            });

            // 方法2: 监听 hash 变化
            window.addEventListener('hashchange', function() {
                window.__recording.captureNavigation();
            });

            // 方法3: 使用 MutationObserver 监听 URL 变化
            let lastUrl = location.href;
            new MutationObserver(function(mutations) {
                if (location.href !== lastUrl) {
                    lastUrl = location.href;
                    setTimeout(function() {
                        window.__recording.captureNavigation();
                    }, 200);
                }
            }).observe(document, { subtree: true, childList: true });

            // 方法4: 拦截 pushState 和 replaceState
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

            console.log('[录制] 录制脚本已加载，包含增强的导航捕获');
        })();
        """

    async def start_session(
        self,
        project_id: str,
        scenario_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """启动录制会话"""
        session_id = str(uuid.uuid4())

        try:
            # 启动 Playwright
            self.playwright = await async_playwright().start()

            # 启动浏览器（非无头模式，便于用户操作）
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--auto-open-devtools-for-tabs',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )

            # 创建浏览器上下文
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )

            # ⚠️ 关键修复：在 context 级别注入脚本，确保所有页面都有效
            await context.add_init_script(self._recording_script)

            # 创建新页面
            page = await context.new_page()

            # 创建录制会话
            session = RecordingSession(
                id=session_id,
                project_id=project_id,
                scenario_name=scenario_name,
                status="recording",
                started_at=datetime.now(),
                browser=self.browser,
                context=context,
                page=page,
                config=config or {
                    "enableSmartWait": True,
                    "autoExtractVariables": True,
                    "mergeContinuousInputs": True
                }
            )

            self.sessions[session_id] = session

            # 打开一个空白页面开始
            await page.goto("about:blank")
            await page.evaluate(f"""
                document.body.innerHTML = `
                    <div style="font-family: Arial; padding: 40px; text-align: center;">
                        <h1>🎬 测试录制已启动</h1>
                        <p style="font-size: 16px; color: #666; margin: 20px 0;">
                            请在地址栏输入您要测试的网页URL
                        </p>
                        <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; display: inline-block; margin: 20px 0;">
                            <p style="margin: 10px 0; color: #2e7d32; font-weight: bold;">
                                ✅ 录制脚本已加载
                            </p>
                            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                                Session ID: {session_id}
                            </p>
                        </div>
                        <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; display: inline-block;">
                            <p style="margin: 10px 0; color: #666;">
                                <strong>💡 使用提示：</strong>
                            </p>
                            <ul style="text-align: left; color: #666;">
                                <li>1. 在浏览器中执行您的测试操作</li>
                                <li>2. 系统会自动捕获点击、输入等操作</li>
                                <li>3. 完成后回到此页面，在控制台查看</li>
                                <li>4. 输入 <code>stopRecording()</code> 停止录制</li>
                            </ul>
                        </div>
                        <p style="margin-top: 20px; color: #999;">
                            已捕获 <span id="action-count" style="font-size: 24px; font-weight: bold; color: #2e7d32;">0</span> 个操作
                        </p>
                        <button onclick="testCapture()" style="margin-top: 20px; padding: 10px 20px; background: #2e7d32; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🧪 测试捕获功能
                        </button>
                        <p id="test-result" style="margin-top: 10px; color: #666;"></p>
                    </div>
                `;

                // 添加测试捕获功能
                window.testCapture = function() {{
                    const testEl = document.getElementById('test-result');
                    if (window.__recording) {{
                        const beforeCount = window.__recording.actions.length;
                        window.__recording.captureAction({{
                            action_type: 'test',
                            selector: '#test-button',
                            page_url: window.location.href,
                            page_title: document.title
                        }});
                        const afterCount = window.__recording.actions.length;
                        testEl.innerHTML = '<span style="color: #2e7d32;">✅ 测试成功！捕获功能正常工作</span>';
                        testEl.style.fontWeight = 'bold';
                    }} else {{
                        testEl.innerHTML = '<span style="color: #c62828;">❌ 测试失败！录制脚本未加载</span>';
                        testEl.style.fontWeight = 'bold';
                    }}
                }};

                // 添加停止录制的全局函数
                window.stopRecording = function() {{
                    fetch('/api/recording/stop', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ session_id: '{session_id}' }})
                    }});
                }};

                // 🔥 关键修复：监控 URL 变化，确保首次导航被捕获
                let currentUrl = window.location.href;
                let checkCount = 0;
                let maxChecks = 50; // 最多检查5秒

                const urlCheckInterval = setInterval(() => {{
                    checkCount++;
                    const newUrl = window.location.href;

                    // 如果 URL 发生变化且不是 about:blank，捕获导航
                    if (newUrl !== currentUrl && newUrl !== 'about:blank') {{
                        currentUrl = newUrl;

                        // 延迟一下，确保页面加载完成
                        setTimeout(() => {{
                            if (window.__recording && !window.__recording.initialized) {{
                                window.__recording.captureNavigation();
                                window.__recording.initialized = true;
                                console.log('[录制] ✅ 捕获初始导航:', newUrl);
                            }}
                        }}, 500);

                        clearInterval(urlCheckInterval);
                    }}

                    // 超过最大检查次数，停止检查
                    if (checkCount >= maxChecks) {{
                        clearInterval(urlCheckInterval);
                    }}
                }}, 100);

                // 定期更新操作计数
                setInterval(() => {{
                    const count = window.__recording ? window.__recording.actions.length : 0;
                    const countEl = document.getElementById('action-count');
                    if (countEl) countEl.textContent = count;
                }}, 1000);

                // 立即检查录制脚本状态
                setTimeout(() => {{
                    const statusEl = document.getElementById('test-result');
                    if (window.__recording) {{
                        console.log('[录制] ✅ 录制脚本已正确加载');
                        console.log('[录制] 🔍 监控首次导航中...');
                    }} else {{
                        console.error('[录制] ❌ 录制脚本未加载！');
                        if (statusEl) {{
                            statusEl.innerHTML = '<span style="color: #c62828;">⚠️ 警告：录制脚本未加载</span>';
                        }}
                    }}
                }}, 500);
            """)

            print(f"✅ 录制会话已启动: {session_id}")
            return session_id

        except Exception as e:
            print(f"❌ 启动录制失败: {e}")
            raise

    async def stop_session(self, session_id: str) -> Dict[str, Any]:
        """停止录制会话"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"录制会话不存在: {session_id}")

        try:
            # 获取捕获的操作
            actions_data = await session.page.evaluate("""
                window.__recording ? window.__recording.actions : []
            """)

            print(f"📊 从浏览器获取到 {len(actions_data)} 个原始操作")

            # 解析操作
            session.captured_actions = []
            for action_data in actions_data:
                try:
                    action = CapturedAction(**action_data)
                    session.captured_actions.append(action)
                    # 🔍 调试信息：打印每个操作
                    print(f"  - {action.action_type}: {action.page_url or action.selector}")
                except Exception as e:
                    print(f"⚠️ 解析操作失败: {e}, 数据: {action_data}")

            # 🔍 调试信息：检查是否有 navigate 操作
            navigate_actions = [a for a in session.captured_actions if a.action_type == 'navigate']
            if navigate_actions:
                print(f"✅ 捕获到 {len(navigate_actions)} 个导航操作")
                for nav in navigate_actions:
                    print(f"  - 导航到: {nav.page_url}")
            else:
                print(f"⚠️ 警告：没有捕获到导航操作！")

            # 更新会话状态
            session.status = "processing"
            session.completed_at = datetime.now()

            print(f"📹 录制已完成，成功捕获 {len(session.captured_actions)} 个操作")

            # 关闭浏览器
            if session.browser:
                await session.browser.close()

            return {
                "session_id": session_id,
                "actions_count": len(session.captured_actions),
                "actions": [self._serialize_action(action) for action in session.captured_actions],
                "scenario_name": session.scenario_name,
                "project_id": session.project_id
            }

        except Exception as e:
            print(f"❌ 停止录制失败: {e}")
            import traceback
            traceback.print_exc()
            session.status = "error"
            raise

    async def get_captured_actions(self, session_id: str) -> List[Dict[str, Any]]:
        """获取已捕获的操作"""
        session = self.sessions.get(session_id)
        if not session:
            return []

        try:
            # 获取当前捕获的操作（实时）
            actions_data = await session.page.evaluate("""
                window.__recording ? window.__recording.actions : []
            """)

            return [
                self._serialize_action(CapturedAction(**action))
                for action in actions_data
            ]
        except Exception as e:
            print(f"⚠️  获取操作失败: {e}")
            return []

    def _serialize_action(self, action: CapturedAction) -> Dict[str, Any]:
        """序列化操作对象"""
        return {
            "id": action.id,
            "timestamp": action.timestamp,
            "action_type": action.action_type,
            "selector": action.selector,
            "value": action.value,
            "element_tag": action.element_tag,
            "element_text": action.element_text,
            "page_url": action.page_url,
            "page_title": action.page_title
        }

    async def close_session(self, session_id: str):
        """关闭录制会话（清理资源）"""
        session = self.sessions.get(session_id)
        if session and session.browser:
            try:
                await session.browser.close()
            except Exception as e:
                print(f"⚠️  关闭浏览器失败: {e}")

        if session_id in self.sessions:
            del self.sessions[session_id]


# 全局录制器实例
browser_recorder = BrowserRecorder()