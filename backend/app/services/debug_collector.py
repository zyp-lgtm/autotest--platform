"""
调试信息收集器

收集测试执行过程中的各种调试信息：
- 页面截图
- HTML 快照
- 控制台日志
- 网络请求
- 执行详情
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from playwright.async_api import Page, ConsoleMessage, Request, Response
from pathlib import Path

logger = logging.getLogger(__name__)


class DebugInfoCollector:
    """调试信息收集器"""

    def __init__(self, base_dir: str = "./debug_screenshots"):
        """
        初始化调试收集器

        Args:
            base_dir: 调试信息保存的基础目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self.screenshots_dir = self.base_dir / "screenshots"
        self.html_dir = self.base_dir / "html"
        self.logs_dir = self.base_dir / "logs"

        for dir_path in [self.screenshots_dir, self.html_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 调试信息
        self.current_session_id: Optional[str] = None
        self.console_messages: List[Dict[str, Any]] = []
        self.network_requests: List[Dict[str, Any]] = []
        self.execution_steps: List[Dict[str, Any]] = []

    def start_session(self, session_id: str) -> None:
        """开始新的调试会话"""
        self.current_session_id = session_id
        self.console_messages = []
        self.network_requests = []
        self.execution_steps = []

        logger.info(f"开始调试会话: {session_id}")

    async def setup_page_listeners(self, page: Page) -> None:
        """设置页面监听器"""
        # 监听控制台消息
        async def handle_console_message(msg: ConsoleMessage):
            message_info = {
                "type": msg.type,
                "text": msg.text,
                "timestamp": datetime.now().isoformat(),
                "location": f"{msg.location.get('url', 'unknown')}:{msg.location.get('lineNumber', 0)}"
            }
            self.console_messages.append(message_info)

            # 记录到日志
            log_func = logger.info if msg.type == "log" else logger.warning
            log_func(f"控制台 [{msg.type}]: {msg.text}")

        page.on("console", handle_console_message)

        # 监听网络请求
        async def handle_request(request: Request):
            request_info = {
                "method": request.method,
                "url": request.url,
                "resource_type": request.resource_type,
                "timestamp": datetime.now().isoformat(),
                "headers": dict(request.headers)
            }
            # 暂时保存请求信息，等待响应
            request_info["_request_obj"] = request
            self.network_requests.append(request_info)

        page.on("request", handle_request)

        # 监听网络响应
        async def handle_response(response: Response):
            # 找到对应的请求并更新
            for req_info in reversed(self.network_requests):
                if req_info.get("url") == response.url:
                    req_info["status"] = response.status
                    req_info["status_text"] = response.status_text
                    req_info["response_headers"] = dict(response.headers)
                    req_info["timing"] = response.request.timing

                    # 尝试获取响应大小（某些资源可能无法获取）
                    try:
                        response_body = await response.body()
                        req_info["response_size"] = len(response_body)
                    except Exception:
                        # 某些资源（如图片、字体）的响应body无法获取
                        req_info["response_size"] = 0

                    # 记录失败的请求
                    if response.status >= 400:
                        logger.warning(f"网络请求失败: {response.method} {response.url} -> {response.status}")
                    break

        page.on("response", handle_response)

        logger.info("已设置页面监听器: 控制台日志 + 网络请求")

    async def capture_failure_info(
        self,
        page: Page,
        step_name: str,
        error: str,
        selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        捕获失败时的调试信息

        Args:
            page: Playwright 页面对象
            step_name: 失败的步骤名称
            error: 错误信息
            selector: 相关的元素选择器

        Returns:
            Dict: 包含所有调试信息的字典
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_info = {
            "step_name": step_name,
            "error": error,
            "selector": selector,
            "timestamp": timestamp,
            "session_id": self.current_session_id
        }

        # 1. 截图
        try:
            screenshot_path = self.screenshots_dir / f"failure_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            debug_info["screenshot"] = str(screenshot_path)
            logger.info(f"已保存失败截图: {screenshot_path}")
        except Exception as e:
            logger.error(f"截图失败: {e}")
            debug_info["screenshot"] = None

        # 2. HTML 快照
        try:
            html_path = self.html_dir / f"failure_{timestamp}.html"
            html_content = await page.content()
            html_path.write_text(html_content, encoding="utf-8")
            debug_info["html_snapshot"] = str(html_path)
            logger.info(f"已保存 HTML 快照: {html_path}")
        except Exception as e:
            logger.error(f"保存 HTML 失败: {e}")
            debug_info["html_snapshot"] = None

        # 3. 当前 URL 和标题
        try:
            debug_info["url"] = page.url
            debug_info["title"] = await page.title()
        except Exception as e:
            logger.error(f"获取页面信息失败: {e}")
            debug_info["url"] = None
            debug_info["title"] = None

        # 4. 控制台日志（最近 20 条）
        debug_info["console_logs"] = self.console_messages[-20:] if self.console_messages else []

        # 5. 网络请求（最近的，按时间排序）
        debug_info["network_requests"] = [
            {k: v for k, v in req.items() if k != "_request_obj"}
            for req in self.network_requests[-10:]
        ]

        # 6. 执行步骤
        debug_info["execution_steps"] = self.execution_steps

        # 7. 保存完整调试报告（JSON）
        try:
            report_path = self.logs_dir / f"debug_report_{timestamp}.json"
            report_path.write_text(json.dumps(debug_info, indent=2, ensure_ascii=False), encoding="utf-8")
            debug_info["report_path"] = str(report_path)
            logger.info(f"已保存调试报告: {report_path}")
        except Exception as e:
            logger.error(f"保存调试报告失败: {e}")
            debug_info["report_path"] = None

        return debug_info

    def log_step_start(
        self,
        step_name: str,
        keyword: str,
        parameters: Dict[str, Any]
    ) -> None:
        """记录步骤开始"""
        step_info = {
            "action": "start",
            "step_name": step_name,
            "keyword": keyword,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat()
        }
        self.execution_steps.append(step_info)

        # 详细日志
        params_str = json.dumps(parameters, ensure_ascii=False)
        logger.info(f"▶️  开始执行步骤: {step_name} [{keyword}]")
        logger.info(f"   参数: {params_str}")

    def log_step_complete(
        self,
        step_name: str,
        result: Dict[str, Any],
        duration: float
    ) -> None:
        """记录步骤完成"""
        step_info = {
            "action": "complete",
            "step_name": step_name,
            "result": result,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": datetime.now().isoformat()
        }
        self.execution_steps.append(step_info)

        # 详细日志
        status = "✅" if result.get("success") else "❌"
        logger.info(f"{status} 步骤完成: {step_name} (耗时: {step_info['duration_ms']}ms)")

        if not result.get("success"):
            error = result.get("error", "未知错误")
            logger.error(f"   失败原因: {error}")

    def log_parameter_resolution(
        self,
        param_name: str,
        raw_value: str,
        resolved_value: Any
    ) -> None:
        """记录参数解析过程"""
        logger.debug(f"   参数解析: {param_name}")
        logger.debug(f"     原始值: {raw_value}")
        logger.debug(f"     解析后: {resolved_value}")

    def log_element_location(
        self,
        selector: str,
        strategy: str,
        found: bool,
        details: Optional[str] = None
    ) -> None:
        """记录元素定位信息"""
        status = "✅" if found else "❌"
        logger.debug(f"{status} 元素定位: {selector}")
        logger.debug(f"   定位策略: {strategy}")
        if details:
            logger.debug(f"   详情: {details}")

    def get_session_summary(self) -> Dict[str, Any]:
        """获取当前会话的摘要信息"""
        return {
            "session_id": self.current_session_id,
            "total_steps": len([s for s in self.execution_steps if s["action"] == "start"]),
            "console_messages": len(self.console_messages),
            "network_requests": len(self.network_requests),
            "failed_requests": len([r for r in self.network_requests if r.get("status", 200) >= 400]),
            "execution_steps": self.execution_steps
        }

    def end_session(self) -> Dict[str, Any]:
        """结束当前调试会话"""
        summary = self.get_session_summary()
        logger.info(f"调试会话结束: {self.current_session_id}")
        logger.info(f"  总步骤数: {summary['total_steps']}")
        logger.info(f"  控制台消息: {summary['console_messages']}")
        logger.info(f"  网络请求: {summary['network_requests']}")
        logger.info(f"  失败请求: {summary['failed_requests']}")

        return summary

    def clear_session(self) -> None:
        """清除当前会话数据"""
        self.current_session_id = None
        self.console_messages = []
        self.network_requests = []
        self.execution_steps = []
