#!/usr/bin/env python3
"""
服务健康监控和告警系统
监控测试平台的所有关键服务
"""
import asyncio
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sys
import subprocess
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    service: str
    status: str  # healthy, degraded, down
    message: str
    response_time: float = 0.0
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class HealthMonitor:
    """服务健康监控器"""

    def __init__(self):
        self.results: List[HealthCheckResult] = []
        self.history: List[Dict] = []
        self.alerts: List[str] = []
        self.start_time = datetime.now()

    async def check_backend(self) -> HealthCheckResult:
        """检查后端服务"""
        url = "http://localhost:8000/health"
        start = datetime.now()

        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                elapsed = (datetime.now() - start).total_seconds()

                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return HealthCheckResult(
                        service="后端 API",
                        status="healthy",
                        message="服务正常",
                        response_time=elapsed,
                        details={"data": data}
                    )
                else:
                    return HealthCheckResult(
                        service="后端 API",
                        status="degraded",
                        message=f"状态码: {response.status}",
                        response_time=elapsed
                    )
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError):
                return HealthCheckResult(
                    service="后端 API",
                    status="down",
                    message="连接超时"
                )
            return HealthCheckResult(
                service="后端 API",
                status="down",
                message=f"连接失败: {str(e.reason)}"
            )
        except Exception as e:
            return HealthCheckResult(
                service="后端 API",
                status="down",
                message=f"检查失败: {str(e)}"
            )

    async def check_frontend(self) -> HealthCheckResult:
        """检查前端服务"""
        url = "http://localhost:3000"
        start = datetime.now()

        try:
            # 尝试端口检查（支持 IPv4 和 IPv6）
            import socket
            port_open = False

            # 先尝试 IPv6（Vite 默认监听 IPv6）
            try:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('::1', 3000, 0, 0))
                sock.close()
                if result == 0:
                    port_open = True
            except Exception:
                pass

            # 如果 IPv6 失败，尝试 IPv4
            if not port_open:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex(('127.0.0.1', 3000))
                    sock.close()
                    if result == 0:
                        port_open = True
                except Exception:
                    pass

            elapsed = (datetime.now() - start).total_seconds()

            if port_open:
                # 端口开放，检查是否有 node/vite 进程
                try:
                    ps_result = subprocess.run(
                        ['lsof', '-i', ':3000'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )

                    if ps_result.returncode == 0 and 'node' in ps_result.stdout.lower():
                        return HealthCheckResult(
                            service="前端服务",
                            status="healthy",
                            message="服务运行中 (Vite 开发服务器)",
                            response_time=elapsed,
                            details={"method": "port_check"}
                        )
                except Exception:
                    pass

                return HealthCheckResult(
                    service="前端服务",
                    status="healthy",
                    message="端口开放，服务正在运行",
                    response_time=elapsed
                )
            else:
                return HealthCheckResult(
                    service="前端服务",
                    status="down",
                    message="端口 3000 未开放"
                )

        except Exception as e:
            return HealthCheckResult(
                service="前端服务",
                status="down",
                message=f"检查失败: {str(e)}"
            )

    def check_agent(self) -> HealthCheckResult:
        """检查 Agent 进程"""
        try:
            # 检查 PID 文件
            pid_file = Path(__file__).parent / ".agent.pid"

            if not pid_file.exists():
                return HealthCheckResult(
                    service="Agent",
                    status="down",
                    message="未找到 PID 文件，Agent 未启动"
                )

            # 读取 PID
            pid = int(pid_file.read_text().strip())

            # 检查进程是否存在（使用 os.kill 发送信号 0）
            try:
                os.kill(pid, 0)  # 不发送信号，只检查进程是否存在
            except OSError:
                return HealthCheckResult(
                    service="Agent",
                    status="down",
                    message=f"PID 文件存在但进程 {pid} 不运行"
                )

            # 获取进程信息（使用 ps 命令）
            try:
                result = subprocess.run(
                    ['ps', '-p', str(pid), '-o', 'pcpu,rss,etime'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split()
                        cpu_percent = float(parts[0])
                        memory_kb = int(parts[1])
                        elapsed_time = parts[2]

                        return HealthCheckResult(
                            service="Agent",
                            status="healthy",
                            message=f"运行中 (PID: {pid})",
                            details={
                                "pid": pid,
                                "cpu_percent": cpu_percent,
                                "memory_mb": memory_kb / 1024,
                                "elapsed_time": elapsed_time
                            }
                        )
            except Exception:
                pass  # 使用默认信息

            return HealthCheckResult(
                service="Agent",
                status="healthy",
                message=f"运行中 (PID: {pid})",
                details={"pid": pid}
            )

        except ValueError:
            return HealthCheckResult(
                service="Agent",
                status="degraded",
                message="PID 文件格式错误"
            )
        except Exception as e:
            return HealthCheckResult(
                service="Agent",
                status="down",
                message=f"检查失败: {str(e)}"
            )

    async def check_docker_services(self) -> List[HealthCheckResult]:
        """检查 Docker 服务"""
        results = []

        # 服务列表
        services = {
            "test-platform-db": "PostgreSQL",
            "test-platform-redis": "Redis",
            "test-platform-backend": "后端容器",
            "test-platform-frontend": "前端容器"
        }

        for container, name in services.items():
            try:
                # 尝试检查 Docker 容器状态
                result = subprocess.run(
                    ['docker', 'inspect', '-f', '{{.State.Status}}', container],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                if result.returncode == 0:
                    status = result.stdout.strip()
                    if status == "running":
                        results.append(HealthCheckResult(
                            service=name,
                            status="healthy",
                            message=f"容器运行中"
                        ))
                    else:
                        results.append(HealthCheckResult(
                            service=name,
                            status="down",
                            message=f"容器状态: {status}"
                        ))
                else:
                    results.append(HealthCheckResult(
                        service=name,
                        status="down",
                        message="容器不存在"
                    ))

            except FileNotFoundError:
                # Docker 命令不可用
                results.append(HealthCheckResult(
                    service=name,
                    status="degraded",
                    message="Docker 不可用，无法检查"
                ))
            except Exception as e:
                results.append(HealthCheckResult(
                    service=name,
                    status="degraded",
                    message=f"检查失败: {str(e)}"
                ))

        return results

    async def run_all_checks(self) -> List[HealthCheckResult]:
        """运行所有健康检查"""
        logger.info("开始健康检查...")
        self.results = []

        # 检查后端
        backend_result = await self.check_backend()
        self.results.append(backend_result)

        # 检查前端
        frontend_result = await self.check_frontend()
        self.results.append(frontend_result)

        # 检查 Agent
        agent_result = self.check_agent()
        self.results.append(agent_result)

        # 检查 Docker 服务
        docker_results = await self.check_docker_services()
        self.results.extend(docker_results)

        # 生成告警
        self._generate_alerts()

        # 保存历史
        self._save_history()

        return self.results

    def _generate_alerts(self):
        """生成告警"""
        self.alerts = []

        for result in self.results:
            if result.status == "down":
                self.alerts.append(f"🔴 {result.service}: {result.message}")
            elif result.status == "degraded":
                self.alerts.append(f"🟡 {result.service}: {result.message}")

    def _save_history(self):
        """保存检查历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in self.results],
            "alerts": self.alerts
        }
        self.history.append(record)

        # 只保留最近 100 条记录
        if len(self.history) > 100:
            self.history = self.history[-100:]

    def print_report(self):
        """打印健康报告"""
        print("\n" + "=" * 60)
        print("服务健康监控报告".center(50))
        print("=" * 60)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"运行时长: {datetime.now() - self.start_time}")
        print("")

        # 总体状态
        healthy_count = sum(1 for r in self.results if r.status == "healthy")
        total_count = len(self.results)

        if healthy_count == total_count:
            print("🟢 总体状态: 所有服务正常")
        elif healthy_count > total_count / 2:
            print("🟡 总体状态: 部分服务异常")
        else:
            print("🔴 总体状态: 多个服务异常")

        print("")

        # 详细结果
        for result in self.results:
            status_icon = {
                "healthy": "✅",
                "degraded": "⚠️ ",
                "down": "❌"
            }.get(result.status, "❓")

            print(f"{status_icon} {result.service}")
            print(f"   状态: {result.status}")
            print(f"   消息: {result.message}")

            if result.response_time > 0:
                print(f"   响应时间: {result.response_time:.3f}s")

            if result.details:
                for key, value in result.details.items():
                    if key not in ["data"]:
                        print(f"   {key}: {value}")

            print("")

        # 告警
        if self.alerts:
            print("⚠️  告警:")
            for alert in self.alerts:
                print(f"   {alert}")
            print("")

        print("=" * 60)

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_services": len(self.results),
            "healthy": sum(1 for r in self.results if r.status == "healthy"),
            "degraded": sum(1 for r in self.results if r.status == "degraded"),
            "down": sum(1 for r in self.results if r.status == "down"),
            "alerts": self.alerts
        }


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="测试平台服务健康监控")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="持续监控，每 30 秒检查一次"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只检查一次（默认）"
    )

    args = parser.parse_args()

    monitor = HealthMonitor()

    if args.watch:
        # 持续监控模式
        try:
            while True:
                await monitor.run_all_checks()

                if args.json:
                    print(json.dumps(monitor.get_summary(), ensure_ascii=False, indent=2))
                else:
                    monitor.print_report()

                print("⏱️  30 秒后重新检查... (Ctrl+C 退出)")
                await asyncio.sleep(30)

        except KeyboardInterrupt:
            print("\n监控已停止")
    else:
        # 单次检查模式
        await monitor.run_all_checks()

        if args.json:
            print(json.dumps(monitor.get_summary(), ensure_ascii=False, indent=2))
        else:
            monitor.print_report()


if __name__ == "__main__":
    asyncio.run(main())
