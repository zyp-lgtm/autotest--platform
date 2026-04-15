#!/usr/bin/env python3
"""
测试平台 - 本地执行 Agent

运行在用户本地机器上，接收服务器下发的测试任务并在本地浏览器中执行。
"""
import asyncio
import websockets
import json
import logging
import sys
import os
import uuid
import atexit
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page

# 禁用代理，避免 SOCKS 代理错误
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['NO_PROXY_LOCAL'] = '1'

# PID 文件路径
PID_FILE = Path(__file__).parent / ".agent.pid"


class PIDFile:
    """PID 文件锁，确保只有一个 Agent 实例运行"""

    def __init__(self, pid_file: Path):
        self.pid_file = pid_file
        self.acquired = False

    def acquire(self) -> bool:
        """尝试获取锁"""
        if self.pid_file.exists():
            try:
                old_pid = int(self.pid_file.read_text().strip())
                # 检查旧进程是否还在运行
                try:
                    os.kill(old_pid, 0)  # 发送信号 0 检查进程是否存在
                    logging.error(f"Agent 已在运行 (PID: {old_pid})")
                    logging.error("如需重启，请先执行: python agent.py --stop")
                    return False
                except OSError:
                    # 旧进程不存在，清理 PID 文件
                    logging.warning(f"清理 stale PID 文件: {old_pid}")
                    self.pid_file.unlink()
            except (ValueError, IOError) as e:
                logging.warning(f"读取 PID 文件失败: {e}")
                self.pid_file.unlink()

        # 写入当前进程 PID
        self.pid_file.write_text(str(os.getpid()))
        self.acquired = True
        atexit.register(self.release)
        logging.info(f"PID 锁已创建: {os.getpid()}")
        return True

    def release(self):
        """释放锁"""
        if self.acquired and self.pid_file.exists():
            self.pid_file.unlink()
            logging.info("PID 锁已释放")

    @classmethod
    def stop_running_agent(cls) -> bool:
        """停止正在运行的 Agent"""
        pid_file = Path(__file__).parent / ".agent.pid"
        if not pid_file.exists():
            print("未找到运行中的 Agent")
            return False

        try:
            pid = int(pid_file.read_text().strip())
            print(f"正在停止 Agent (PID: {pid})...")
            os.kill(pid, 15)  # SIGTERM
            import time
            time.sleep(1)

            # 检查是否已停止
            try:
                os.kill(pid, 0)
                print("Agent 未响应 SIGTERM，使用 SIGKILL...")
                os.kill(pid, 9)  # SIGKILL
            except OSError:
                pass

            pid_file.unlink()
            print("✓ Agent 已停止")
            return True
        except (ValueError, OSError, ProcessLookupError) as e:
            print(f"停止 Agent 失败: {e}")
            return False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalAgent:
    """本地测试执行 Agent"""

    def __init__(self, server_url: str, agent_id: str = None):
        """
        初始化 Agent

        Args:
            server_url: 服务器 WebSocket URL (如 ws://localhost:8000/agent)
            agent_id: Agent ID，如果为 None 则自动生成
        """
        self.server_url = server_url
        self.agent_id = agent_id or str(uuid.uuid4())
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.connected = False

        logger.info(f"初始化 Agent: {self.agent_id}")

    async def start(self):
        """启动 Agent（支持自动重连）"""
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                logger.info(f"正在连接到服务器: {self.server_url}")
                if retry_count > 0:
                    logger.info(f"重连尝试 {retry_count + 1}/{max_retries}")

                async with websockets.connect(self.server_url) as websocket:
                    self.connected = True
                    logger.info("✓ 已连接到服务器")
                    retry_count = 0  # 连接成功，重置重试计数

                    # 发送注册消息
                    await self._register(websocket)

                    # 监听服务器消息
                    await self._listen(websocket)

            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket 连接错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"等待 5 秒后重连...")
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Agent 错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"等待 5 秒后重连...")
                    await asyncio.sleep(5)

        logger.error("达到最大重试次数，Agent 退出")
        self.connected = False
        await self._cleanup()

    async def _register(self, websocket):
        """向服务器注册"""
        register_msg = {
            "type": "register",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "capabilities": {
                "browser_types": ["chromium", "firefox", "webkit"],
                "platform": sys.platform,
                "headless": False  # 本地执行通常需要看到浏览器
            }
        }

        await websocket.send(json.dumps(register_msg))
        logger.info(f"已注册 Agent: {self.agent_id}")

    async def _listen(self, websocket):
        """监听服务器消息"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error(f"无效的 JSON 消息: {message}")
                except Exception as e:
                    logger.error(f"处理消息错误: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket 连接已关闭")
        except Exception as e:
            logger.error(f"监听循环异常: {e}")
            raise

    async def _handle_message(self, websocket, data: Dict[str, Any]):
        """处理服务器消息"""
        msg_type = data.get("type")

        if msg_type == "ping":
            # 心跳
            await websocket.send(json.dumps({
                "type": "pong",
                "agent_id": self.agent_id
            }))

        elif msg_type == "task":
            # 执行测试任务
            task_id = data.get("task_id")
            logger.info(f"收到任务: {task_id}")

            try:
                result = await self._execute_task(data)
                await websocket.send(json.dumps({
                    "type": "task_result",
                    "agent_id": self.agent_id,
                    "task_id": task_id,
                    "result": result
                }))
            except Exception as e:
                logger.error(f"执行任务失败: {e}")
                await websocket.send(json.dumps({
                    "type": "task_result",
                    "agent_id": self.agent_id,
                    "task_id": task_id,
                    "result": {
                        "success": False,
                        "error": str(e)
                    }
                }))

        elif msg_type == "close":
            # 关闭浏览器
            await self._close_browser()
            await websocket.send(json.dumps({
                "type": "closed",
                "agent_id": self.agent_id
            }))

        else:
            logger.warning(f"未知消息类型: {msg_type}")

    async def _execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试任务"""
        task_id = task_data.get("task_id")
        browser_type = task_data.get("browser_type", "chromium")
        headless = task_data.get("headless", False)
        url = task_data.get("url")
        steps = task_data.get("steps", [])

        logger.info("=" * 60)
        logger.info(f"开始执行任务: {task_id}")
        logger.info(f"浏览器: {browser_type}, headless: {headless}")
        logger.info(f"步骤总数: {len(steps)}")
        logger.info("=" * 60)

        results = []
        step_count = 0
        success_count = 0
        fail_count = 0

        try:
            # 启动浏览器
            if not self.browser:
                self.playwright = await async_playwright().start()

                browser_map = {
                    "chromium": self.playwright.chromium,
                    "firefox": self.playwright.firefox,
                    "webkit": self.playwright.webkit
                }
                browser_engine = browser_map.get(browser_type, self.playwright.chromium)

                # 配置浏览器启动选项
                launch_options = {
                    "headless": headless,
                    "slow_mo": 50  # 减慢操作速度，便于观察
                }

                # macOS 特殊处理：添加一些参数帮助窗口显示
                import platform
                if platform.system() == "Darwin":
                    # 在 macOS 上，确保窗口在前台显示
                    if not headless:
                        launch_options["args"] = [
                            "--start-maximized",  # 最大化窗口
                            "--disable-infobars",  # 禁用信息栏
                        ]

                logger.info(f"浏览器启动选项: {launch_options}")
                self.browser = await browser_engine.launch(**launch_options)
                logger.info(f"✓ 浏览器已启动: {browser_type} (headless={headless})")

            # 创建页面
            page = await self.browser.new_page()

            # 执行步骤
            for i, step in enumerate(steps, 1):
                step_count = i
                logger.info(f"\n[步骤 {i}/{len(steps)}]")

                step_result = await self._execute_step(page, step)
                results.append(step_result)

                if step_result.get("success", False):
                    success_count += 1
                else:
                    fail_count += 1
                    # 检查是否需要继续执行
                    continue_on_failure = step.get("continue_on_failure", False)
                    if not continue_on_failure:
                        logger.info(f"  → 步骤失败且 continue_on_failure=False，停止执行")
                        break
                    else:
                        logger.info(f"  → 步骤失败但 continue_on_failure=True，继续执行")

            # 输出执行摘要
            logger.info("")
            logger.info("=" * 60)
            logger.info("执行摘要")
            logger.info("=" * 60)
            logger.info(f"总步骤数: {step_count}")
            logger.info(f"成功: {success_count}")
            logger.info(f"失败: {fail_count}")
            logger.info(f"结果: {'✓ 通过' if fail_count == 0 else '✗ 失败'}")
            logger.info("=" * 60)

            # 如果是非 headless 模式，保持浏览器窗口打开一段时间，便于查看
            if not headless and self.browser:
                logger.info("浏览器窗口将保持 5 秒，便于查看...")
                import asyncio
                await asyncio.sleep(5)

            # 关闭浏览器，释放资源
            await self._close_browser()

            return {
                "success": fail_count == 0,
                "results": results,
                "message": "任务执行完成"
            }

        except Exception as e:
            logger.error(f"")
            logger.error("=" * 60)
            logger.error(f"执行任务失败: {e}")
            logger.error("=" * 60)
            # 出错时也关闭浏览器
            await self._close_browser()
            return {
                "success": False,
                "error": str(e),
                "results": results
            }

    async def _execute_step(self, page: Page, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        import time
        from datetime import datetime
        action = step.get("action")
        params = step.get("parameters", {})

        # 记录开始时间
        start_time = time.time()

        # 收集详细日志
        logs = []
        def add_log(level: str, message: str):
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message
            }
            logs.append(log_entry)
            if level == "error":
                logger.error(f"  {message}")
            else:
                logger.info(f"  {message}")

        # 增强日志输出
        if action == "navigate":
            add_log("info", f"操作: 导航到 URL")
            add_log("info", f"参数: url={params.get('url')}")
        elif action == "click":
            add_log("info", f"操作: 点击元素")
            add_log("info", f"参数: selector={params.get('selector')}")
        elif action == "input":
            add_log("info", f"操作: 输入文本")
            add_log("info", f"参数: selector={params.get('selector')}, text={params.get('text')}")
        elif action == "wait":
            add_log("info", f"操作: 等待元素")
            state = params.get('state', 'visible')
            add_log("info", f"参数: selector={params.get('selector')}, state={state}, timeout={params.get('timeout', 5000)}ms")
        elif action == "screenshot":
            add_log("info", f"操作: 截图")
            add_log("info", f"参数: path={params.get('path')}")
        else:
            add_log("info", f"操作: {action}")
            add_log("info", f"参数: {params}")

        try:
            if action == "navigate":
                url = params.get("url")
                await page.goto(url)
                elapsed = time.time() - start_time
                add_log("info", f"✓ 成功 | 耗时: {elapsed:.2f}秒")
                return {
                    "success": True,
                    "action": action,
                    "duration": elapsed,
                    "logs": logs
                }

            elif action == "click":
                selector = params.get("selector")
                await page.click(selector)
                elapsed = time.time() - start_time
                add_log("info", f"✓ 成功 | 耗时: {elapsed:.2f}秒")
                return {
                    "success": True,
                    "action": action,
                    "duration": elapsed,
                    "logs": logs
                }

            elif action == "input":
                selector = params.get("selector")
                text = params.get("text")
                clear_first = params.get("clear_first", False)

                # 对于隐藏的输入框，直接使用 force=True 强制填充
                try:
                    # 先尝试点击元素使其获得焦点（超时时间短）
                    await page.click(selector, timeout=3000)
                    add_log("info", "→ 已点击元素使其可见")
                except Exception as e:
                    # 如果点击失败，使用 force=True 强制操作
                    add_log("info", f"→ 点击失败，使用 force=True: {str(e)[:50]}...")

                # 清空现有内容（如果需要）
                if clear_first:
                    await page.fill(selector, "", force=True)
                    add_log("info", "→ 已清空现有内容")

                # 填充文本（使用 force=True 强制操作隐藏元素）
                await page.fill(selector, text, force=True)
                elapsed = time.time() - start_time
                add_log("info", f"✓ 成功 | 输入文本: {text} | 耗时: {elapsed:.2f}秒")
                return {
                    "success": True,
                    "action": action,
                    "duration": elapsed,
                    "logs": logs
                }

            elif action == "wait":
                selector = params.get("selector")
                timeout = params.get("timeout", 5000)
                state = params.get("state", "visible")  # 支持 attached/visible/hidden
                await page.wait_for_selector(selector, timeout=timeout, state=state)
                elapsed = time.time() - start_time
                add_log("info", f"✓ 成功 | 等待状态: {state} | 耗时: {elapsed:.2f}秒")
                return {
                    "success": True,
                    "action": action,
                    "duration": elapsed,
                    "logs": logs
                }

            elif action == "screenshot":
                path = params.get("path", f"screenshot_{uuid.uuid4().hex}.png")
                await page.screenshot(path=path)
                elapsed = time.time() - start_time
                add_log("info", f"✓ 成功 | 保存路径: {path} | 耗时: {elapsed:.2f}秒")
                return {
                    "success": True,
                    "action": action,
                    "screenshot": path,
                    "duration": elapsed,
                    "logs": logs
                }

            else:
                return {
                    "success": False,
                    "action": action,
                    "error": f"未知操作: {action}",
                    "logs": logs
                }

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            add_log("error", f"✗ 失败 | 耗时: {elapsed:.2f}秒")
            add_log("error", f"错误详情: {error_msg}")

            # 失败时自动截图
            screenshot_path = None
            try:
                screenshot_path = f"screenshot_error_{uuid.uuid4().hex}.png"
                await page.screenshot(path=screenshot_path)
                add_log("info", f"✓ 已保存失败截图: {screenshot_path}")
            except Exception as screenshot_error:
                add_log("error", f"截图失败: {str(screenshot_error)}")

            return {
                "success": False,
                "action": action,
                "error": error_msg,
                "duration": elapsed,
                "logs": logs,
                "screenshot": screenshot_path
            }

    async def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        logger.info("浏览器已关闭")

    async def _cleanup(self):
        """清理资源"""
        await self._close_browser()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="测试平台本地执行 Agent")
    parser.add_argument(
        "--server",
        default="ws://localhost:8000/agent",
        help="服务器 WebSocket URL"
    )
    parser.add_argument(
        "--agent-id",
        default=None,
        help="Agent ID（可选，默认自动生成）"
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="停止正在运行的 Agent"
    )

    args = parser.parse_args()

    # 处理停止命令
    if args.stop:
        PIDFile.stop_running_agent()
        return

    # 检查单例
    pid_lock = PIDFile(PID_FILE)
    if not pid_lock.acquire():
        sys.exit(1)

    print("""
╔════════════════════════════════════════╗
║  测试平台 - 本地执行 Agent              ║
╚════════════════════════════════════════╝
    """)
    print(f"服务器: {args.server}")
    print(f"Agent ID: {args.agent_id or '自动生成'}")
    print(f"进程 PID: {os.getpid()}")
    print("")

    agent = LocalAgent(args.server, args.agent_id)

    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        print("\n停止 Agent")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
    finally:
        pid_lock.release()


if __name__ == "__main__":
    main()
