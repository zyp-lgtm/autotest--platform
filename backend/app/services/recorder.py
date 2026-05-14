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
    xpath: str = ""  # XPath 选择器（备用/精确匹配）
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
                    '--start-maximized',
                    '--auto-open-devtools-for-tabs',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )

            # 创建浏览器上下文（no_viewport 视口跟随窗口大小，最大化时即全屏）
            context = await self.browser.new_context(
                no_viewport=True,
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
                        // data-* 属性（测试专属 & 框架标识属性）
                        var dataAttrs = ['data-testid', 'data-test-id', 'data-cy', 'data-key', 'data-value', 'data-index', 'data-row-key', 'data-node-key'];
                        for (var di = 0; di < dataAttrs.length; di++) {{
                            var dv = element.getAttribute(dataAttrs[di]);
                            if (dv) return '[' + dataAttrs[di] + '="' + dv + '"]';
                        }}
                        var tag = element.tagName.toLowerCase();
                        // 提取类名（排除纯视觉工具类，保留语义化类名）
                        var skipSet = {{
                            // Tailwind 布局/间距/装饰类（无数值，完全无区分的）
                            'cursor-pointer':1,'flex':1,'block':1,'inline':1,'inline-block':1,
                            'relative':1,'absolute':1,'fixed':1,'sticky':1,
                            'w-full':1,'h-full':1,'w-screen':1,'h-screen':1,
                            'line-clamp-1':1,'line-clamp-2':1,'truncate':1,
                            'flex-1':1,'flex-col':1,'flex-wrap':1,'flex-row':1,'flex-shrink-0':1,'flex-grow':1,
                            'justify-start':1,'justify-between':1,'justify-center':1,'justify-end':1,
                            'items-center':1,'items-start':1,'items-end':1,'self-center':1,
                            'rounded':1,'rounded-sm':1,'rounded-md':1,'rounded-lg':1,'rounded-full':1,
                            'shadow':1,'shadow-sm':1,'shadow-md':1,'shadow-lg':1,
                            'p-1':1,'p-2':1,'p-3':1,'p-4':1,'p-5':1,'p-6':1,
                            'm-1':1,'m-2':1,'m-3':1,'m-4':1,'mx-auto':1,
                            'px-1':1,'px-2':1,'px-3':1,'px-4':1,'px-5':1,'px-6':1,
                            'py-1':1,'py-2':1,'py-3':1,'py-4':1,'py-5':1,'py-6':1,
                            'text-sm':1,'text-xs':1,'text-lg':1,'text-base':1,'text-xl':1,'text-2xl':1,
                            'font-bold':1,'font-medium':1,'font-normal':1,'font-semibold':1,
                            'overflow-hidden':1,'overflow-auto':1,'box-border':1,'box-content':1,
                            'text-left':1,'text-center':1,'text-right':1,
                            'gap-1':1,'gap-2':1,'gap-3':1,'gap-4':1,'space-x-1':1,'space-x-2':1,'space-y-1':1,'space-y-2':1,
                            'border':1,'border-t':1,'border-b':1,'border-l':1,'border-r':1,'border-0':1,
                            'bg-white':1,'bg-gray-50':1,'bg-gray-100':1,'bg-blue-50':1,'bg-transparent':1,
                            'text-white':1,'text-gray-500':1,'text-gray-600':1,'text-gray-700':1,'text-gray-900':1,'text-blue-500':1,'text-blue-600':1,
                            'hidden':1,'visible':1,'opacity-50':1,'opacity-0':1,'z-10':1,'z-20':1
                        }};
                        var twUtilRe = /(^|:)(p|pl|pr|pt|pb|px|py|m|ml|mr|mt|mb|mx|my|w|h|min-w|min-h|max-w|max-h|top|right|bottom|left|inset|text|font|leading|tracking|bg|border|rounded|flex|order|col|row|gap|space|shadow|opacity|z|object|overflow|grid|place|justify|items|self|ring|outline|rotate|scale|skew|translate|transition|duration|ease|delay|animate|aspect|backdrop|scroll|sr)-/;
                        function isUtilityClass(cls) {{
                            if (skipSet[cls]) return true;
                            return twUtilRe.test(cls);
                        }}
                        var usefulClasses = [];
                        if (element.className && typeof element.className === 'string') {{
                            var classNames = element.className.trim().split(/\\s+/);
                            for (var i = 0; i < classNames.length && usefulClasses.length < 3; i++) {{
                                var cn = classNames[i];
                                if (cn && !isUtilityClass(cn)) {{
                                    usefulClasses.push(CSS.escape(cn));
                                }}
                            }}
                        }}
                        // 获取元素文本：先读直接文本节点，再用 textContent 兜底
                        var ownText = '';
                        for (var c = element.firstChild; c; c = c.nextSibling) {{
                            if (c.nodeType === 3) ownText += c.textContent;
                        }}
                        ownText = ownText.trim();
                        if (!ownText) {{
                            ownText = (element.getAttribute('aria-label') || element.getAttribute('title') || '').trim();
                        }}
                        // 🔥 textContent 兜底只对交互元素使用，避免 div/span 产生泛选择器
                        if (!ownText) {{
                            var interactiveTags = {{'button':1,'a':1,'input':1,'textarea':1,'select':1,'label':1,'summary':1,'li':1,'td':1,'th':1}};
                            if (interactiveTags[tag] || (element.getAttribute && element.getAttribute('role'))) {{
                                var tc = (element.textContent || '').trim();
                                if (tc.length <= 60) ownText = tc;
                            }}
                        }}
                        ownText = ownText.substring(0, 30);
                        // 转义 :has-text() 中的双引号
                        function escText(t) {{
                            return t.replace(/"/g, '\\\\"');
                        }}
                        // 计算同标签兄弟中的位置（1-based）
                        function nthOfType(el) {{
                            var idx = 1;
                            for (var s = el.previousElementSibling; s; s = s.previousElementSibling) {{
                                if (s.tagName === el.tagName) idx++;
                            }}
                            return idx;
                        }}
                        // 🔥 辅助函数：向上查找有意义的祖先（最多4层）
                        function findAncestorContext(el, levels) {{
                            var a = el.parentElement;
                            for (var d = 0; d < levels && a && a !== document.body && a !== document.documentElement; d++) {{
                                if (a.id) return '#' + CSS.escape(a.id) + ' ';
                                if (a.className && typeof a.className === 'string') {{
                                    var ac = a.className.trim().split(/\\s+/);
                                    for (var k = 0; k < ac.length; k++) {{
                                        if (ac[k] && !isUtilityClass(ac[k])) {{
                                            return a.tagName.toLowerCase() + '.' + CSS.escape(ac[k]) + ' ';
                                        }}
                                    }}
                                }}
                                a = a.parentElement;
                            }}
                            return '';
                        }}
                        // 🔥 策略1：input/textarea 用 placeholder 或 name
                        if (tag === 'input' || tag === 'textarea') {{
                            var placeholder = element.getAttribute('placeholder') || '';
                            if (placeholder) {{
                                return 'input[placeholder="' + escText(placeholder.trim().substring(0, 30)) + '"]';
                            }}
                            var inputType = element.getAttribute('type') || 'text';
                            if (usefulClasses.length > 0) {{
                                return 'input[type="' + inputType + '"].' + usefulClasses.join('.');
                            }}
                            var ictx = findAncestorContext(element, 3);
                            if (ictx) return ictx + '> input[type="' + inputType + '"]:nth-of-type(' + nthOfType(element) + ')';
                            return 'input[type="' + inputType + '"]';
                        }}
                        // 🔥 策略2：有文本
                        if (ownText) {{
                            if (usefulClasses.length > 0) {{
                                return tag + '.' + usefulClasses[0] + ':has-text("' + escText(ownText) + '")';
                            }}
                            // 无自身类名时，向上查找祖先上下文
                            var ctx = findAncestorContext(element, 4);
                            if (ctx) {{
                                return ctx + tag + ':has-text("' + escText(ownText) + '")';
                            }}
                            // 最后防线：文本 + 位置限定，避免裸 tag:has-text() 匹配到错误元素
                            var n = nthOfType(element);
                            if (n > 1 || element.nextElementSibling || element.previousElementSibling) {{
                                return tag + ':nth-of-type(' + n + '):has-text("' + escText(ownText) + '")';
                            }}
                            return tag + ':has-text("' + escText(ownText) + '")';
                        }}
                        // 🔥 策略3：无文本，用类名组合
                        if (usefulClasses.length > 0) {{
                            return tag + '.' + usefulClasses.join('.');
                        }}
                        // 🔥 策略4：祖先上下文 + nth-of-type（尝试用 textContent 兜底）
                        var ctx2 = findAncestorContext(element, 4);
                        if (ctx2) {{
                            var tcFallback = (element.textContent || '').trim().substring(0, 40);
                            if (tcFallback) {{
                                return ctx2 + '> ' + tag + ':nth-of-type(' + nthOfType(element) + '):has-text("' + escText(tcFallback) + '")';
                            }}
                            return ctx2 + '> ' + tag + ':nth-of-type(' + nthOfType(element) + ')';
                        }}
                        // 最后兜底：tag + textContent
                        var tcLast = (element.textContent || '').trim().substring(0, 40);
                        if (tcLast) return tag + ':has-text("' + escText(tcLast) + '")';
                        return tag;
                    }},

                    // ============ 智能 XPath 生成（相对路径，无绝对路径）============
                    getXPath: function(element) {{
                        var tag = element.tagName.toLowerCase();
                        // 策略1: id → //*[@id='xxx']
                        if (element.id) return '//*[@id="' + element.id + '"]';
                        // 策略2: data-* 属性
                        var dataAttrs = ['data-testid', 'data-test-id', 'data-cy', 'data-key', 'data-value', 'data-index', 'data-row-key', 'data-node-key'];
                        for (var di = 0; di < dataAttrs.length; di++) {{
                            var dv = element.getAttribute(dataAttrs[di]);
                            if (dv) return '//' + tag + '[@' + dataAttrs[di] + '="' + dv + '"]';
                        }}
                        // 策略3: aria-label
                        var aria = element.getAttribute('aria-label');
                        if (aria) return '//' + tag + '[@aria-label="' + aria + '"]';
                        // 策略4: title
                        var title = element.getAttribute('title');
                        if (title) return '//' + tag + '[@title="' + title + '"]';
                        // 获取直接文本
                        var directText = '';
                        for (var c = element.firstChild; c; c = c.nextSibling) {{
                            if (c.nodeType === 3) directText += c.textContent;
                        }}
                        directText = directText.trim().substring(0, 40);
                        // 获取一个有意义的类名
                        var usefulCls = '';
                        if (element.className && typeof element.className === 'string') {{
                            var clsList = element.className.trim().split(/\\s+/);
                            for (var ci = 0; ci < clsList.length; ci++) {{
                                var c = clsList[ci];
                                if (c && !window.__recording._isUtilityClass(c)) {{ usefulCls = c; break; }}
                            }}
                        }}
                        // 策略5: 精确文本匹配（XPath 的 text() 只匹配直接文本节点）
                        if (directText) {{
                            if (usefulCls) return '//' + tag + '[contains(@class,"' + usefulCls + '")][text()="' + directText + '"]';
                            // 向上查找祖先上下文
                            var ctx = window.__recording._findAncestorCls(element, 4);
                            if (ctx) {{
                                var ctxSel = ctx.isId ? ('//' + ctx.tag + '[@id="' + ctx.cls + '"]') : ('//' + ctx.tag + '[contains(@class,"' + ctx.cls + '")]');
                                return ctxSel + '//' + tag + '[text()="' + directText + '"]';
                            }}
                            return '//' + tag + '[text()="' + directText + '"]';
                        }}
                        // 策略6: 无精确文本，尝试 textContent（交互元素）
                        var tc = (element.textContent || '').trim();
                        if (tc && tc.length <= 50) {{
                            var interactiveTags = {{'button':1,'a':1,'input':1,'textarea':1,'select':1,'label':1,'summary':1,'li':1,'td':1,'th':1,'dt':1}};
                            // 🔥 扩展：非交互元素也允许 textContent 兜底（避免回退到纯位置选择器）
                            var canUseText = interactiveTags[tag] || element.getAttribute('role') || (usefulCls === '' && !directText);
                            if (canUseText) {{
                                if (usefulCls) return '//' + tag + '[contains(@class,"' + usefulCls + '")][contains(text(),"' + tc + '")]';
                                var ctx2 = window.__recording._findAncestorCls(element, 4);
                                if (ctx2) {{
                                    var ctxSel2 = ctx2.isId ? ('//' + ctx2.tag + '[@id="' + ctx2.cls + '"]') : ('//' + ctx2.tag + '[contains(@class,"' + ctx2.cls + '")]');
                                    return ctxSel2 + '//' + tag + '[contains(text(),"' + tc + '")]';
                                }}
                                return '//' + tag + '[contains(text(),"' + tc + '")]';
                            }}
                        }}
                        // 策略7: 类名组合
                        if (usefulCls) return '//' + tag + '[contains(@class,"' + usefulCls + '")]';
                        // 策略8: 祖先上下文 + 位置（尝试 textContent 兜底）
                        var ctx3 = window.__recording._findAncestorCls(element, 4);
                        if (ctx3) {{
                            var idx = 1;
                            for (var s = element.previousElementSibling; s; s = s.previousElementSibling) {{
                                if (s.tagName === element.tagName) idx++;
                            }}
                            var ctxSel3 = ctx3.isId ? ('//' + ctx3.tag + '[@id="' + ctx3.cls + '"]') : ('//' + ctx3.tag + '[contains(@class,"' + ctx3.cls + '")]');
                            var xpTc = (element.textContent || '').trim().substring(0, 40);
                            if (xpTc) return ctxSel3 + '//' + tag + '[contains(text(),"' + xpTc + '")]';
                            return ctxSel3 + '//' + tag + '[' + idx + ']';
                        }}
                        // 最后兜底: tag + textContent
                        var xpTc2 = (element.textContent || '').trim().substring(0, 40);
                        if (xpTc2) return '//' + tag + '[contains(text(),"' + xpTc2 + '")]';
                        return '';
                    }},

                    // 辅助: 缓存 skipSet 供 getXPath 使用
                    _skipSet: {{'cursor-pointer':1,'flex':1,'block':1,'inline':1,'inline-block':1,
                        'relative':1,'absolute':1,'fixed':1,'sticky':1,
                        'w-full':1,'h-full':1,'w-screen':1,'h-screen':1,
                        'line-clamp-1':1,'line-clamp-2':1,'truncate':1,
                        'flex-1':1,'flex-col':1,'flex-wrap':1,'flex-row':1,'flex-shrink-0':1,'flex-grow':1,
                        'justify-start':1,'justify-between':1,'justify-center':1,'justify-end':1,
                        'items-center':1,'items-start':1,'items-end':1,'self-center':1,
                        'rounded':1,'rounded-sm':1,'rounded-md':1,'rounded-lg':1,'rounded-full':1,
                        'shadow':1,'shadow-sm':1,'shadow-md':1,'shadow-lg':1,
                        'p-1':1,'p-2':1,'p-3':1,'p-4':1,'p-5':1,'p-6':1,
                        'm-1':1,'m-2':1,'m-3':1,'m-4':1,'mx-auto':1,
                        'px-1':1,'px-2':1,'px-3':1,'px-4':1,'px-5':1,'px-6':1,
                        'py-1':1,'py-2':1,'py-3':1,'py-4':1,'py-5':1,'py-6':1,
                        'text-sm':1,'text-xs':1,'text-lg':1,'text-base':1,'text-xl':1,'text-2xl':1,
                        'font-bold':1,'font-medium':1,'font-normal':1,'font-semibold':1,
                        'overflow-hidden':1,'overflow-auto':1,'box-border':1,'box-content':1,
                        'text-left':1,'text-center':1,'text-right':1,
                        'gap-1':1,'gap-2':1,'gap-3':1,'gap-4':1,'space-x-1':1,'space-x-2':1,'space-y-1':1,'space-y-2':1,
                        'border':1,'border-t':1,'border-b':1,'border-l':1,'border-r':1,'border-0':1,
                        'bg-white':1,'bg-gray-50':1,'bg-gray-100':1,'bg-blue-50':1,'bg-transparent':1,
                        'text-white':1,'text-gray-500':1,'text-gray-600':1,'text-gray-700':1,'text-gray-900':1,'text-blue-500':1,'text-blue-600':1,
                        'hidden':1,'visible':1,'opacity-50':1,'opacity-0':1,'z-10':1,'z-20':1}},
                    _twUtilRe: /(^|:)(p|pl|pr|pt|pb|px|py|m|ml|mr|mt|mb|mx|my|w|h|min-w|min-h|max-w|max-h|top|right|bottom|left|inset|text|font|leading|tracking|bg|border|rounded|flex|order|col|row|gap|space|shadow|opacity|z|object|overflow|grid|place|justify|items|self|ring|outline|rotate|scale|skew|translate|transition|duration|ease|delay|animate|aspect|backdrop|scroll|sr)-/,
                    _isUtilityClass: function(cls) {{
                        if (window.__recording._skipSet[cls]) return true;
                        return window.__recording._twUtilRe.test(cls);
                    }},

                    // 辅助: 向上查找有类名的祖先（供 getXPath 用）
                    _findAncestorCls: function(el, levels) {{
                        var isUtil = window.__recording._isUtilityClass;
                        var a = el.parentElement;
                        for (var d = 0; d < levels && a && a !== document.body && a !== document.documentElement; d++) {{
                            if (a.id) return {{tag: a.tagName.toLowerCase(), cls: a.id, isId: true}};
                            if (a.className && typeof a.className === 'string') {{
                                var ac = a.className.trim().split(/\\s+/);
                                for (var k = 0; k < ac.length; k++) {{
                                    if (ac[k] && !isUtil(ac[k])) return {{tag: a.tagName.toLowerCase(), cls: ac[k], isId: false}};
                                }}
                            }}
                            a = a.parentElement;
                        }}
                        return null;
                    }},

                    // 统计选择器匹配数（处理 :has-text() 等 Playwright 专有伪类）
                    countMatches: function(selector, strategy) {{
                        try {{
                            if (strategy === 'xpath') {{
                                var result = document.evaluate(selector, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                                return result.snapshotLength;
                            }}
                            // CSS: 处理 Playwright 专有伪类 :has-text()
                            var css = selector;
                            var hasTextReg = /:has-text\("(.+?)"\)/g;
                            var match;
                            var texts = [];
                            while ((match = hasTextReg.exec(css)) !== null) {{
                                texts.push(match[1]);
                            }}
                            if (texts.length > 0) {{
                                var baseCss = css.replace(/:has-text\("(.+?)"\)/g, '');
                                var all = document.querySelectorAll(baseCss);
                                var count = 0;
                                for (var i = 0; i < all.length; i++) {{
                                    var el = all[i];
                                    var tc = (el.textContent || '') + ' ' + (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('title') || '') + ' ' + (el.getAttribute('placeholder') || '');
                                    var ok = true;
                                    for (var t = 0; t < texts.length; t++) {{
                                        if (tc.indexOf(texts[t]) === -1) {{ ok = false; break; }}
                                    }}
                                    if (ok) count++;
                                }}
                                return count;
                            }}
                            return document.querySelectorAll(css).length;
                        }} catch(e) {{
                            return -1;
                        }}
                    }},

                    // 最优选择器：CSS vs XPath，谁唯一匹配就用谁
                    getBestSelector: function(element) {{
                        var css = window.__recording.getSelector(element);
                        var xpath = window.__recording.getXPath(element);
                        var cssCount = window.__recording.countMatches(css, 'css');
                        var xpathCount = xpath ? window.__recording.countMatches(xpath, 'xpath') : -1;
                        // 决策: 唯一匹配 > 更少匹配 > XPath优先（text()更精确）> CSS兜底
                        if (cssCount === 1 && xpathCount === 1) {{
                            // 都唯一: XPath text() 比 CSS :has-text() 精确，优先 XPath
                            if (xpath.indexOf('text()') !== -1) {{
                                return {{selector: css, xpath: xpath, strategy: 'xpath'}};
                            }}
                            // CSS 用 has-text 无类名限定 → 用 XPath
                            if (css.indexOf(':has-text') !== -1 && css.indexOf('.') === -1) {{
                                return {{selector: css, xpath: xpath, strategy: 'xpath'}};
                            }}
                            return {{selector: css, xpath: xpath, strategy: 'css'}};
                        }}
                        if (xpathCount === 1) return {{selector: css, xpath: xpath, strategy: 'xpath'}};
                        if (cssCount === 1) return {{selector: css, xpath: xpath, strategy: 'css'}};
                        if (xpathCount > 0 && cssCount > 0) {{
                            return xpathCount <= cssCount ? {{selector: css, xpath: xpath, strategy: 'xpath'}} : {{selector: css, xpath: xpath, strategy: 'css'}};
                        }}
                        if (xpathCount > 0) return {{selector: css, xpath: xpath, strategy: 'xpath'}};
                        if (cssCount > 0) return {{selector: css, xpath: xpath, strategy: 'css'}};
                        return {{selector: css, xpath: xpath, strategy: 'css'}};
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

                // 监听点击事件 - 智能目标识别（点击前刷新待处理的输入）
                document.addEventListener('click', function(e) {{
                    // 先刷新 debounce 中未捕获的输入
                    if (window.__recording.flushAllInputs) window.__recording.flushAllInputs();
                    var target = e.target;
                    // 🔥 向上查找有意义元素：跳过 SVG、图标壳、空壳 div/span
                    var skipTags = {{'svg':1,'path':1,'circle':1,'rect':1,'line':1,'polygon':1,'polyline':1,'ellipse':1,'g':1,'use':1,'style':1,'script':1,'link':1,'meta':1,'head':1,'br':1,'hr':1}};
                    var iconClassPatterns = [/\\banticon\\b/, /\\bicon-\\b/, /\\bicon\\b/, /\\bfa-\\b/, /\\bfa\\b/, /\\bglyphicon\\b/, /\\bmaterial-icons\\b/, /\\bio-\\b/, /\\bsvg\\b/, /\\bico\\b/];
                    function isIconOnly(el) {{
                        return looksLikeIconWrapper(el);
                    }}
                    while (target && target !== document.body) {{
                        var t = target.tagName.toLowerCase();
                        if (skipTags[t]) {{ target = target.parentElement; continue; }}
                        if (isIconOnly(target)) {{ target = target.parentElement; continue; }}
                        break;
                    }}
                    if (!target || target === document.body) target = e.target;
                    // 🔥 下钻：如果目标是无直接文本的空壳 div/span，找真正有文本的子元素
                    function hasDirectText(el) {{
                        for (var c = el.firstChild; c; c = c.nextSibling) {{
                            if (c.nodeType === 3 && c.textContent.trim()) return true;
                        }}
                        return false;
                    }}
                    // 检查元素自身是否像图标（用于 while 循环跳过图标壳）
                    // 注意：isIconOnly 只看 class 和结构，不递归文本长度！
                    // 文本判断交给 drillToTextChild 处理
                    function looksLikeIconWrapper(el) {{
                        if (el.id) return false;
                        // 🔥 class 优先：图标 class 是最强的图标信号（即使有 aria-label/role 也是图标）
                        if (el.className && typeof el.className === 'string') {{
                            for (var p = 0; p < iconClassPatterns.length; p++) {{
                                if (iconClassPatterns[p].test(el.className)) return true;
                            }}
                        }}
                        // 没有图标 class 时，aria-label/title/role 的存在表示这是有意义的元素，不是空壳图标
                        if (el.getAttribute && (el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('role'))) return false;
                        return false;
                    }}
                    function drillToTextChild(el) {{
                        var tag = el.tagName.toLowerCase();
                        // 只对非交互的包装元素下钻
                        if (el.id || el.getAttribute('data-testid') || el.getAttribute('data-node-key') || el.getAttribute('data-key')) return el;
                        var interactive = {{'button':1,'a':1,'input':1,'textarea':1,'select':1,'label':1}};
                        if (interactive[tag]) return el;
                        if (!hasDirectText(el)) {{
                            // 找第一个有文本的非空壳子元素（有多个时选第一个，总比空壳 nth-of-type 强）
                            var bestChild = null;
                            for (var c = el.firstElementChild; c; c = c.nextElementSibling) {{
                                var ct = c.tagName.toLowerCase();
                                if (skipTags[ct]) continue;
                                if (isIconOnly(c)) continue;
                                var hasText = c.textContent && c.textContent.trim();
                                if (hasText) {{
                                    bestChild = c;
                                    break;  // 取第一个即可
                                }}
                            }}
                            if (bestChild) return drillToTextChild(bestChild);
                        }}
                        return el;
                    }}
                    target = drillToTextChild(target);
                    window.__lastClickTarget = target;
                    window.__lastClickDrilled = true;
                    var best = window.__recording.getBestSelector(target);
                    window.__recording.captureAction({{
                        action_type: 'click',
                        selector: best.selector,
                        xpath: best.xpath,
                        selector_strategy: best.strategy,
                        element_tag: target.tagName,
                        element_text: target.textContent ? target.textContent.trim().substring(0, 50) : null,
                        page_url: window.location.href,
                        page_title: document.title
                    }});
                }}, true);

                // 监听输入事件 - 去重版本（400ms debounce）
                (function() {{
                    var isComposing = {{}};
                    var justComposed = {{}};   // 🔥 修复：标记刚完成 composition 的字段
                    var pendingInputs = {{}};   // selector -> {{timer, value, target, placeholder}}
                    var DEBOUNCE_MS = 400;

                    function flushInput(selector) {{
                        var pending = pendingInputs[selector];
                        if (!pending) return;
                        clearTimeout(pending.timer);
                        delete pendingInputs[selector];
                        var best = window.__recording.getBestSelector(pending.target);
                        window.__recording.captureAction({{
                            action_type: 'input',
                            selector: best.selector,
                            xpath: best.xpath,
                            selector_strategy: best.strategy,
                            value: pending.value,
                            element_tag: pending.target.tagName,
                            element_text: pending.placeholder,
                            page_url: window.location.href,
                            page_title: document.title,
                            timestamp: Date.now()
                        }});
                    }}

                    // 暴露 flushAll 给 click 等事件使用
                    window.__recording.flushAllInputs = function() {{
                        Object.keys(pendingInputs).forEach(function(sel) {{
                            flushInput(sel);
                        }});
                    }};

                    document.addEventListener('compositionstart', function(e) {{
                        var best = window.__recording.getBestSelector(e.target);
                        isComposing[best.selector] = true;
                        if (pendingInputs[best.selector]) {{
                            clearTimeout(pendingInputs[best.selector].timer);
                            delete pendingInputs[best.selector];
                        }}
                    }}, true);

                    // 🔥 修复：compositionend 只捕获一次，并阻止后续 input 事件重复捕获
                    document.addEventListener('compositionend', function(e) {{
                        var best = window.__recording.getBestSelector(e.target);
                        isComposing[best.selector] = false;
                        // 清除可能残留的 debounce 定时器
                        if (pendingInputs[best.selector]) {{
                            clearTimeout(pendingInputs[best.selector].timer);
                            delete pendingInputs[best.selector];
                        }}
                        // 直接捕获 composition 后的最终值
                        window.__recording.captureAction({{
                            action_type: 'input',
                            selector: best.selector,
                            xpath: best.xpath,
                            selector_strategy: best.strategy,
                            value: e.target.value,
                            element_tag: e.target.tagName,
                            element_text: e.target.placeholder,
                            page_url: window.location.href,
                            page_title: document.title,
                            timestamp: Date.now()
                        }});
                        // 🔥 关键：标记刚完成，阻止浏览器随后触发的 input 事件再次进入 debounce
                        justComposed[best.selector] = true;
                    }}, true);

                    document.addEventListener('input', function(e) {{
                        var best = window.__recording.getBestSelector(e.target);
                        if (isComposing[best.selector]) return;
                        // 🔥 修复：刚完成 composition，跳过（已在 compositionend 中直接捕获）
                        if (justComposed[best.selector]) {{
                            delete justComposed[best.selector];
                            return;
                        }}

                        // 清除旧定时器，更新为最新值
                        if (pendingInputs[best.selector]) clearTimeout(pendingInputs[best.selector].timer);
                        pendingInputs[best.selector] = {{
                            timer: setTimeout(function() {{ flushInput(best.selector); }}, DEBOUNCE_MS),
                            value: e.target.value,
                            target: e.target,
                            placeholder: e.target.placeholder
                        }};
                    }}, true);

                    // 页面卸载前刷新所有待处理输入
                    window.addEventListener('beforeunload', function() {{
                        Object.keys(pendingInputs).forEach(function(sel) {{ flushInput(sel); }});
                    }});
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
            # 🔥 更新会话中的操作列表为去重后的版本
            session.captured_actions = captured_actions
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
            "xpath": action.xpath,
            "selector_strategy": action.selector_strategy,
            "value": action.value,
            "element_tag": action.element_tag,
            "element_text": action.element_text,
            "page_url": action.page_url,
            "page_title": action.page_title
        }

    def _merge_duplicate_inputs(self, actions: List[CapturedAction]) -> List[CapturedAction]:
        """去重：按时间窗口合并重复输入 + 快速重复点击"""
        if not actions:
            return actions

        # 确保按时间戳排序
        actions = sorted(actions, key=lambda x: x.timestamp)

        to_remove = set()

        # ---- 1. 输入去重：同一选择器的连续输入，保留最后一个（时间窗口内） ----
        INPUT_MERGE_WINDOW_MS = 3000  # 3秒内的连续输入视为同一次输入会话

        # 按选择器分组，再按时间窗口拆分子组
        selector_inputs = {}
        for i, action in enumerate(actions):
            if action.action_type == 'input' and action.selector:
                if action.selector not in selector_inputs:
                    selector_inputs[action.selector] = []
                selector_inputs[action.selector].append((i, action))

        for selector, input_list in selector_inputs.items():
            # 按时间窗口拆分子组（相邻输入间隔 < 3秒视为同一会话）
            sessions = []
            current_session = [input_list[0]]
            for j in range(1, len(input_list)):
                prev_ts = input_list[j-1][1].timestamp
                curr_ts = input_list[j][1].timestamp
                if curr_ts - prev_ts < INPUT_MERGE_WINDOW_MS:
                    current_session.append(input_list[j])
                else:
                    sessions.append(current_session)
                    current_session = [input_list[j]]
            sessions.append(current_session)

            # 每个会话只保留最长值的输入
            for session in sessions:
                if len(session) > 1:
                    best_idx, best_action = max(session, key=lambda x: len(x[1].value or ''))
                    for idx, action in session:
                        if idx != best_idx:
                            to_remove.add(idx)
                    print(f"🔍 合并输入 [{selector[:40]}]: {len(session)}次 → 保留 '{best_action.value}'")

        # ---- 2. 点击去重：同一选择器的快速重复点击（双击保护） ----
        CLICK_DEDUP_WINDOW_MS = 800  # 800ms 内的重复点击视为双击

        for i in range(len(actions)):
            if i in to_remove:
                continue
            action = actions[i]
            if action.action_type != 'click':
                continue
            # 向后查找同选择器的点击
            for j in range(i + 1, len(actions)):
                if j in to_remove:
                    continue
                next_action = actions[j]
                if next_action.action_type != 'click':
                    break  # 只合并连续的 click
                if next_action.selector != action.selector:
                    break
                time_diff = next_action.timestamp - action.timestamp
                if time_diff < CLICK_DEDUP_WINDOW_MS:
                    to_remove.add(j)
                    print(f"🔍 合并重复点击 [{action.selector[:40]}]: 间隔 {time_diff*1000:.0f}ms")
                else:
                    break

        merged = [action for i, action in enumerate(actions) if i not in to_remove]
        removed_count = len(actions) - len(merged)
        if removed_count > 0:
            print(f"📊 去重完成: 移除了 {removed_count} 个重复操作，剩余 {len(merged)} 个")
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