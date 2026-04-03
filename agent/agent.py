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
from datetime import datetime
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page

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
        """启动 Agent"""
        logger.info(f"正在连接到服务器: {self.server_url}")

        try:
            async with websockets.connect(self.server_url) as websocket:
                self.connected = True
                logger.info("✓ 已连接到服务器")

                # 发送注册消息
                await self._register(websocket)

                # 监听服务器消息
                await self._listen(websocket)

        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket 连接错误: {e}")
        except Exception as e:
            logger.error(f"Agent 错误: {e}")
        finally:
            self.connected = False
            logger.info("与服务器断开连接")
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
        async for message in websocket:
            try:
                data = json.loads(message)
                await self._handle_message(websocket, data)
            except json.JSONDecodeError:
                logger.error(f"无效的 JSON 消息: {message}")
            except Exception as e:
                logger.error(f"处理消息错误: {e}")

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

                self.browser = await browser_engine.launch(headless=headless)
                logger.info(f"✓ 浏览器已启动: {browser_type}")

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
                    break  # 失败则停止

            # 任务完成后关闭浏览器
            await self._close_browser()

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
        action = step.get("action")
        params = step.get("parameters", {})

        # 记录开始时间
        start_time = time.time()

        # 增强日志输出
        if action == "navigate":
            logger.info(f"  操作: 导航到 URL")
            logger.info(f"  参数: url={params.get('url')}")
        elif action == "click":
            logger.info(f"  操作: 点击元素")
            logger.info(f"  参数: selector={params.get('selector')}")
        elif action == "input":
            logger.info(f"  操作: 输入文本")
            logger.info(f"  参数: selector={params.get('selector')}, text={params.get('text')}")
        elif action == "wait":
            logger.info(f"  操作: 等待元素")
            logger.info(f"  参数: selector={params.get('selector')}, timeout={params.get('timeout', 5000)}ms")
        elif action == "screenshot":
            logger.info(f"  操作: 截图")
            logger.info(f"  参数: path={params.get('path')}")
        else:
            logger.info(f"  操作: {action}")
            logger.info(f"  参数: {params}")

        try:
            if action == "navigate":
                url = params.get("url")
                await page.goto(url)
                elapsed = time.time() - start_time
                logger.info(f"  ✓ 成功 | 耗时: {elapsed:.2f}秒")
                return {"success": True, "action": action}

            elif action == "click":
                selector = params.get("selector")
                await page.click(selector)
                elapsed = time.time() - start_time
                logger.info(f"  ✓ 成功 | 耗时: {elapsed:.2f}秒")
                return {"success": True, "action": action}

            elif action == "input":
                selector = params.get("selector")
                text = params.get("text")
                await page.fill(selector, text)
                elapsed = time.time() - start_time
                logger.info(f"  ✓ 成功 | 耗时: {elapsed:.2f}秒")
                return {"success": True, "action": action}

            elif action == "wait":
                selector = params.get("selector")
                timeout = params.get("timeout", 5000)
                await page.wait_for_selector(selector, timeout=timeout)
                elapsed = time.time() - start_time
                logger.info(f"  ✓ 成功 | 耗时: {elapsed:.2f}秒")
                return {"success": True, "action": action}

            elif action == "screenshot":
                path = params.get("path", f"screenshot_{uuid.uuid4().hex}.png")
                await page.screenshot(path=path)
                elapsed = time.time() - start_time
                logger.info(f"  ✓ 成功 | 保存路径: {path} | 耗时: {elapsed:.2f}秒")
                return {"success": True, "action": action, "screenshot": path}

            else:
                return {"success": False, "action": action, "error": f"未知操作: {action}"}

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ 失败 | 耗时: {elapsed:.2f}秒")
            logger.error(f"  错误详情: {str(e)}")
            return {"success": False, "action": action, "error": str(e)}

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

    args = parser.parse_args()

    print("""
╔════════════════════════════════════════╗
║  测试平台 - 本地执行 Agent              ║
╚════════════════════════════════════════╝
    """)
    print(f"服务器: {args.server}")
    print(f"Agent ID: {args.agent_id or '自动生成'}")
    print("")

    agent = LocalAgent(args.server, args.agent_id)

    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        print("\n停止 Agent")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
