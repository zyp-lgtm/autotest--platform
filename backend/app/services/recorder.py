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


class BrowserRecorder:
    """浏览器录制器"""

    def __init__(self):
        self.sessions: Dict[str, RecordingSession] = {}
        self._recording_script = """
        (function() {
            window.__recording = {
                actions: [],
                startTime: Date.now(),

                captureAction: function(action) {
                    action.timestamp = Date.now() - window.__recording.startTime;
                    window.__recording.actions.push(action);
                    console.log('[录制]', action.type, action.selector);
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
                }
            };

            // 监听点击事件
            document.addEventListener('click', function(e) {
                var selector = window.__recording.getSelector(e.target);
                window.__recording.captureAction({
                    type: 'click',
                    selector: selector,
                    element_tag: e.target.tagName,
                    element_text: e.target.textContent ? e.target.textContent.trim().substring(0, 50) : null,
                    page_url: window.location.href,
                    page_title: document.title
                });
            }, true);

            // 监听输入事件
            document.addEventListener('input', function(e) {
                var selector = window.__recording.getSelector(e.target);
                window.__recording.captureAction({
                    type: 'input',
                    selector: selector,
                    value: e.target.value,
                    element_tag: e.target.tagName,
                    element_text: e.target.placeholder,
                    page_url: window.location.href,
                    page_title: document.title
                });
            }, true);

            // 监听导航事件
            let lastUrl = location.href;
            new MutationObserver(function(mutations) {
                if (location.href !== lastUrl) {
                    lastUrl = location.href;
                    window.__recording.captureAction({
                        type: 'navigate',
                        selector: '',
                        page_url: location.href,
                        page_title: document.title
                    });
                }
            }).observe(document, { subtree: true, childList: true });

            console.log('[录制] 录制脚本已加载');
        })();
        """

    async def start_session(self, project_id: str, scenario_name: str) -> str:
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

            # 创建新页面
            page = await context.new_page()

            # 注入录制脚本
            await page.add_init_script(self._recording_script)

            # 创建录制会话
            session = RecordingSession(
                id=session_id,
                project_id=project_id,
                scenario_name=scenario_name,
                status="recording",
                started_at=datetime.now(),
                browser=self.browser,
                context=context,
                page=page
            )

            self.sessions[session_id] = session

            # 打开一个空白页面开始
            await page.goto("about:blank")
            await page.evaluate("""
                document.body.innerHTML = `
                    <div style="font-family: Arial; padding: 40px; text-align: center;">
                        <h1>🎬 测试录制已启动</h1>
                        <p style="font-size: 16px; color: #666; margin: 20px 0;">
                            请在地址栏输入您要测试的网页URL
                        </p>
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
                            已捕获 <span id="action-count">0</span> 个操作
                        </p>
                    </div>
                `;

                // 添加停止录制的全局函数
                window.stopRecording = function() {
                    fetch('/api/recording/stop', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_id: '${session_id}' })
                    });
                };

                // 定期更新操作计数
                setInterval(() => {
                    const count = window.__recording ? window.__recording.actions.length : 0;
                    const countEl = document.getElementById('action-count');
                    if (countEl) countEl.textContent = count;
                }, 1000);
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

            # 解析操作
            session.captured_actions = [
                CapturedAction(**action) for action in actions_data
            ]

            # 更新会话状态
            session.status = "processing"
            session.completed_at = datetime.now()

            print(f"📹 录制已完成，捕获 {len(session.captured_actions)} 个操作")

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