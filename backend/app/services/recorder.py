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
        self._recording_script = """(function() {
    window.__recording = {
        actions: [],
        startTime: Date.now(),
        initialized: false,

        captureAction: function(action) {
            if (!action.timestamp) {
                action.timestamp = Date.now() - window.__recording.startTime;
            }
            window.__recording.actions.push(action);
            console.log('[录制] ' + action.action_type + ' @' + action.timestamp.toFixed(0) + 'ms: ' + (action.selector || action.page_url));
        },

        getSelector: function(element) {
            if (element.id) {
                return '#' + element.id;
            }
            if (element.name) {
                return '[name=' + element.name + ']';
            }
            if (element.className) {
                // 获取第一个类名
                var className = element.className.split(' ')[0];
                // 🔥 转义特殊字符（方括号、点等）
                return '.' + className.replace(/([\[\]\\.])/g, '\\$1');
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

    // 监听输入事件 - 立即捕获版本
    (function() {
        var isComposing = {};

        document.addEventListener('compositionstart', function(e) {
            var selector = window.__recording.getSelector(e.target);
            isComposing[selector] = true;
        }, true);

        document.addEventListener('compositionend', function(e) {
            var selector = window.__recording.getSelector(e.target);
            isComposing[selector] = false;
            window.__recording.captureAction({
                action_type: 'input',
                selector: selector,
                value: e.target.value,
                element_tag: e.target.tagName,
                element_text: e.target.placeholder,
                page_url: window.location.href,
                page_title: document.title
            });
        }, true);

        document.addEventListener('input', function(e) {
            var selector = window.__recording.getSelector(e.target);
            // 如果正在使用中文输入法，跳过
            if (isComposing[selector]) {
                return;
            }
            // 🔥 立即捕获输入，不延迟
            window.__recording.captureAction({
                action_type: 'input',
                selector: selector,
                value: e.target.value,
                element_tag: e.target.tagName,
                element_text: e.target.placeholder,
                page_url: window.location.href,
                page_title: document.title
            });
        }, true);
    })();

    console.log('[录制] 录制脚本已加载（立即捕获版本）');
})();"""

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

            # 🔥 关键修复：创建一个会话级别的操作列表，避免跨页面数据丢失
            session_actions = []

            # 🔥 暴露一个函数给浏览器上下文，用于实时传递操作数据
            async def capture_action(action_data):
                """接收从浏览器传递过来的操作数据"""
                try:
                    action = CapturedAction(**action_data)
                    session_actions.append(action)
                    print(f"📝 捕获操作: {action.action_type} - {action.page_url or action.selector}")
                except Exception as e:
                    print(f"⚠️ 捕获操作失败: {e}")

            await context.expose_function("captureActionToBackend", capture_action)

            # 修改录制脚本，使用 exposed function 而不是本地存储
            self._recording_script_with_backend = f"""
            (function() {{
                window.__recording = {{
                    actions: [],
                    startTime: Date.now(),
                    sessionId: '{session_id}',

                    captureAction: function(action) {{
                        action.timestamp = Date.now();
                        window.__recording.actions.push(action);
                        console.log('[录制]', action.action_type, action.selector || action.page_url);

                        // 🔥 关键修复：立即将操作传递到 Python 后端
                        if (window.captureActionToBackend) {{
                            window.captureActionToBackend(action);
                        }}
                    }},

                    getSelector: function(element) {{
                        if (element.id) {{
                            return '#' + CSS.escape(element.id);
                        }}
                        if (element.name) {{
                            return '[name="' + CSS.escape(element.name) + '"]';
                        }}
                        var tag = element.tagName.toLowerCase();
                        // 获取直接文本（不含子元素）
                        var ownText = '';
                        for (var c = element.firstChild; c; c = c.nextSibling) {{
                            if (c.nodeType === 3) ownText += c.textContent;
                        }}
                        ownText = ownText.trim();
                        // 如果无直接文本，用 aria-label/title
                        if (!ownText) {{
                            ownText = (element.getAttribute('aria-label') || element.getAttribute('title') || '').trim();
                        }}
                        ownText = ownText.substring(0, 30);
                        // 提取类名（最多3个，排除通用工具类）
                        var skipSet = {{'cursor-pointer':1,'flex':1,'block':1,'inline':1,
                            'relative':1,'absolute':1,'w-full':1,'h-full':1,
                            'line-clamp-1':1,'line-clamp-2':1,'truncate':1,
                            'flex-1':1,'flex-col':1,'flex-wrap':1,'flex-row':1,
                            'justify-start':1,'justify-between':1,'justify-center':1,
                            'items-center':1,'items-start':1,'items-end':1,
                            'rounded':1,'rounded-sm':1,'rounded-md':1,'rounded-lg':1,
                            'shadow':1,'shadow-sm':1,'shadow-md':1,
                            'p-1':1,'p-2':1,'p-3':1,'p-4':1,
                            'm-1':1,'m-2':1,'m-3':1,'m-4':1,
                            'px-1':1,'px-2':1,'px-3':1,'px-4':1,
                            'py-1':1,'py-2':1,'py-3':1,'py-4':1,
                            'text-sm':1,'text-xs':1,'text-lg':1,'text-base':1}};
                        var usefulClasses = [];
                        if (element.className && typeof element.className === 'string') {{
                            var classNames = element.className.trim().split(/\\s+/);
                            for (var i = 0; i < classNames.length && usefulClasses.length < 3; i++) {{
                                var cn = classNames[i];
                                if (cn && !skipSet[cn]) {{
                                    usefulClasses.push(CSS.escape(cn));
                                }}
                            }}
                        }}
                        // 🔥 策略1：input/textarea 用 placeholder 或 name
                        if (tag === 'input' || tag === 'textarea') {{
                            var placeholder = element.getAttribute('placeholder') || '';
                            if (placeholder) {{
                                return 'input[placeholder="' + placeholder.trim().substring(0, 30) + '"]';
                            }}
                            var inputType = element.getAttribute('type') || 'text';
                            if (usefulClasses.length > 0) {{
                                return 'input[type="' + inputType + '"].' + usefulClasses.join('.');
                            }}
                            return 'input[type="' + inputType + '"]';
                        }}
                        // 🔥 策略2：有直接文本 → tag.class:has-text("text")，必须有类名
                        if (ownText) {{
                            if (usefulClasses.length > 0) {{
                                return tag + '.' + usefulClasses[0] + ':has-text("' + ownText + '")';
                            }}
                            // 无类名但有兄弟上下文：尝试用父元素的类名
                            var parent = element.parentElement;
                            if (parent && parent.className && typeof parent.className === 'string') {{
                                var pClasses = parent.className.trim().split(/\\s+/);
                                for (var i = 0; i < pClasses.length; i++) {{
                                    if (pClasses[i] && !skipSet[pClasses[i]]) {{
                                        return tag + ':has-text("' + ownText + '")';
                                    }}
                                }}
                            }}
                            return tag + ':has-text("' + ownText + '")';
                        }}
                        // 🔥 策略3：无文本，用类名组合
                        if (usefulClasses.length > 0) {{
                            return tag + '.' + usefulClasses.join('.');
                        }}
                        return tag;
                    }},

                    captureNavigation: function() {{
                        var currentUrl = window.location.href;

                        // 避免重复捕获相同的URL
                        if (window.__recording.lastCapturedUrl === currentUrl) {{
                            return;
                        }}

                        // 跳过 about:blank 页面
                        if (currentUrl === 'about:blank') {{
                            return;
                        }}

                        window.__recording.lastCapturedUrl = currentUrl;

                        window.__recording.captureAction({{
                            action_type: 'navigate',
                            selector: '',
                            page_url: currentUrl,
                            page_title: document.title
                        }});
                    }}
                }};

                // 立即捕获当前页面（如果不是 about:blank）
                if (window.location.href !== 'about:blank') {{
                    setTimeout(function() {{
                        window.__recording.captureNavigation();
                    }}, 100);
                }}

                // 监听点击事件 - 智能目标识别
                document.addEventListener('click', function(e) {{
                    var target = e.target;
                    // 🔥 向上查找有意义的可交互元素
                    var skipTags = {{'svg':1,'path':1,'circle':1,'rect':1,'line':1,'polygon':1,'polyline':1,'ellipse':1,'g':1,'use':1}};
                    var skipClasses = {{'anticon':1}};  // Ant Design 图标包裹器
                    while (target && target !== document.body) {{
                        var t = target.tagName.toLowerCase();
                        // 跳过 SVG 元素和纯图标包裹器
                        if (skipTags[t]) {{ target = target.parentElement; continue; }}
                        // 跳过 anticon span（只含 SVG 图标的空壳）
                        if (t === 'span' && target.className && typeof target.className === 'string') {{
                            var cls = target.className;
                            var isIconOnly = /\\banticon\\b/.test(cls) || /\\bicon-\\b/.test(cls);
                            var hasText = target.textContent && target.textContent.trim().length > 2;
                            if (isIconOnly && !hasText) {{ target = target.parentElement; continue; }}
                        }}
                        break;
                    }}
                    if (!target || target === document.body) target = e.target;
                    var selector = window.__recording.getSelector(target);
                    window.__recording.captureAction({{
                        action_type: 'click',
                        selector: selector,
                        element_tag: target.tagName,
                        element_text: target.textContent ? target.textContent.trim().substring(0, 50) : null,
                        page_url: window.location.href,
                        page_title: document.title
                    }});
                }}, true);

                // 监听输入事件 - 中文输入法支持和立即捕获
                (function() {{
                    var isComposing = {{}};    // 跟踪每个输入框的中文输入状态

                    // 监听中文输入开始
                    document.addEventListener('compositionstart', function(e) {{
                        var selector = window.__recording.getSelector(e.target);
                        isComposing[selector] = true;
                    }}, true);

                    // 监听中文输入结束
                    document.addEventListener('compositionend', function(e) {{
                        var selector = window.__recording.getSelector(e.target);
                        isComposing[selector] = false;

                        // 中文输入完成，立即捕获
                        window.__recording.captureAction({{
                            action_type: 'input',
                            selector: selector,
                            value: e.target.value,
                            element_tag: e.target.tagName,
                            element_text: e.target.placeholder,
                            page_url: window.location.href,
                            page_title: document.title,
                            timestamp: Date.now()
                        }});
                    }}, true);

                    // 监听普通输入事件（英文等）- 🔥 立即捕获，无延迟
                    document.addEventListener('input', function(e) {{
                        var selector = window.__recording.getSelector(e.target);

                        // 如果正在使用中文输入法，跳过
                        if (isComposing[selector]) {{
                            return;
                        }}

                        // 🔥 立即捕获输入，不使用延迟
                        window.__recording.captureAction({{
                            action_type: 'input',
                            selector: selector,
                            value: e.target.value,
                            element_tag: e.target.tagName,
                            element_text: e.target.placeholder,
                            page_url: window.location.href,
                            page_title: document.title,
                            timestamp: Date.now()
                        }});
                    }}, true);
                }})();

                // 监听导航事件（使用多种方法确保不遗漏）

                // 方法1: 使用 popstate 监听浏览器前进后退
                window.addEventListener('popstate', function() {{
                    setTimeout(function() {{
                        window.__recording.captureNavigation();
                    }}, 100);
                }});

                // 方法2: 监听 hash 变化
                window.addEventListener('hashchange', function() {{
                    window.__recording.captureNavigation();
                }});

                // 方法3: 使用 MutationObserver 监听 URL 变化
                let lastUrl = location.href;
                new MutationObserver(function(mutations) {{
                    if (location.href !== lastUrl) {{
                        lastUrl = location.href;
                        setTimeout(function() {{
                            window.__recording.captureNavigation();
                        }}, 200);
                    }}
                }}).observe(document, {{ subtree: true, childList: true }});

                // 方法4: 拦截 pushState 和 replaceState
                (function() {{
                    var originalPushState = history.pushState;
                    var originalReplaceState = history.replaceState;

                    history.pushState = function() {{
                        originalPushState.apply(this, arguments);
                        setTimeout(function() {{
                            window.__recording.captureNavigation();
                        }}, 100);
                    }};

                    history.replaceState = function() {{
                        originalReplaceState.apply(this, arguments);
                        setTimeout(function() {{
                            window.__recording.captureNavigation();
                        }}, 100);
                    }};
                }})();

                console.log('[录制] ✅ 录制脚本已加载（增强版 - 实时传递到后端）');
            }})();
            """

            # ⚠️ 关键修复：在 context 级别注入脚本，确保所有页面都有效
            await context.add_init_script(self._recording_script_with_backend)

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

            # 🔥 将操作列表存储在会话中，避免跨页面丢失
            session.captured_actions = session_actions

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
            # 🔥 关键修复：使用存储在会话中的操作列表，而不是从浏览器获取
            # 这样可以避免跨页面导航导致的数据丢失
            captured_actions = session.captured_actions

            print(f"📊 从会话存储获取到 {len(captured_actions)} 个操作")

            # 🔥 去重和排序：先按时间戳排序，再合并重复输入
            captured_actions = sorted(captured_actions, key=lambda x: x.timestamp)
            captured_actions = self._merge_duplicate_inputs(captured_actions)
            print(f"📊 去重后剩余 {len(captured_actions)} 个操作")

            # 🔍 调试信息：打印每个操作
            for action in captured_actions:
                print(f"  - {action.action_type}: {action.page_url or action.selector}")

            # 🔍 调试信息：检查是否有 navigate 操作
            navigate_actions = [a for a in captured_actions if a.action_type == 'navigate']
            if navigate_actions:
                print(f"✅ 捕获到 {len(navigate_actions)} 个导航操作")
                for nav in navigate_actions:
                    print(f"  - 导航到: {nav.page_url}")
            else:
                print(f"⚠️ 警告：没有捕获到导航操作！")

            # 更新会话状态
            session.status = "processing"
            session.completed_at = datetime.now()

            print(f"📹 录制已完成，成功捕获 {len(captured_actions)} 个操作")

            # 关闭浏览器
            if session.browser:
                await session.browser.close()

            return {
                "session_id": session_id,
                "actions_count": len(captured_actions),
                "actions": [self._serialize_action(action) for action in captured_actions],
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
            # 🔥 关键修复：使用存储在会话中的操作列表
            # 这样可以避免跨页面导航导致的数据丢失
            captured_actions = session.captured_actions

            return [
                self._serialize_action(action)
                for action in captured_actions
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

    def _merge_duplicate_inputs(self, actions: List[CapturedAction]) -> List[CapturedAction]:
        """去重和合并输入操作（跨越等待步骤）"""
        if not actions:
            return actions

        # 按选择器分组所有输入操作
        input_groups = {}
        input_indices = set()

        for i, action in enumerate(actions):
            if action.action_type == 'input' and action.selector:
                if action.selector not in input_groups:
                    input_groups[action.selector] = []
                input_groups[action.selector].append((i, action))

        for selector, input_list in input_groups.items():
            if len(input_list) > 1:
                print(f"🔍 发现选择器 {selector} 有 {len(input_list)} 个输入操作")
                best_index, best_action = max(input_list, key=lambda x: len(x[1].value or ''))
                print(f"  ✓ 保留: '{best_action.value}'")
                for idx, action in input_list:
                    if idx != best_index:
                        print(f"  ✗ 移除: '{action.value}'")
                        input_indices.add(idx)
                        if idx > 0:
                            prev_idx = idx - 1
                            while prev_idx >= 0 and prev_idx in input_indices:
                                prev_idx -= 1
                            if prev_idx >= 0:
                                prev_action = actions[prev_idx]
                                if (prev_action.action_type == 'wait' and
                                    prev_action.selector == action.selector):
                                    input_indices.add(prev_idx)

        merged = [action for i, action in enumerate(actions) if i not in input_indices]
        removed_count = len(actions) - len(merged)
        if removed_count > 0:
            print(f"📊 去重完成: 移除了 {removed_count} 个重复操作")
        return merged

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