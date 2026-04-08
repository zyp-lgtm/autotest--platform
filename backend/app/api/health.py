"""
系统健康检查 API
提供所有服务和组件的健康状态
"""
import subprocess
import socket
import os
import time
from datetime import datetime
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter()


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.last_check = None
        self.cache_ttl = 30  # 缓存 30 秒
        self.cached_result = None

    def check_cache(self) -> bool:
        """检查缓存是否有效"""
        if self.cached_result is None:
            return False

        if self.last_check is None:
            return False

        elapsed = time.time() - self.last_check
        return elapsed < self.cache_ttl

    async def check_backend(self) -> Dict[str, Any]:
        """检查后端服务"""
        return {
            "id": "backend",
            "name": "后端 API",
            "status": "healthy",
            "message": "服务正常",
            "response_time": 0.001  # 自身检查，响应时间极短
        }

    async def check_frontend(self) -> Dict[str, Any]:
        """检查前端服务"""
        start = time.time()

        # 直接使用 socket 检查（更可靠）
        # 尝试 IPv6（Vite 默认）
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('::1', 3000, 0, 0))
            sock.close()
            if result == 0:
                elapsed = time.time() - start
                return {
                    "id": "frontend",
                    "name": "前端服务",
                    "status": "healthy",
                    "message": "Vite 开发服务器运行中",
                    "response_time": elapsed
                }
        except Exception as e:
            pass

        # 尝试 IPv4
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', 3000))
            sock.close()
            if result == 0:
                elapsed = time.time() - start
                return {
                    "id": "frontend",
                    "name": "前端服务",
                    "status": "healthy",
                    "message": "前端服务运行中",
                    "response_time": elapsed
                }
        except Exception:
            pass

        return {
            "id": "frontend",
            "name": "前端服务",
            "status": "down",
            "message": "端口 3000 未开放"
        }

    async def check_agent(self) -> Dict[str, Any]:
        """检查 Agent 进程"""
        try:
            # 查找 agent 目录（可能在多个位置）
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "agent" / ".agent.pid",  # worktree 结构
                Path(__file__).parent.parent.parent / "agent" / ".agent.pid",  # 扁平结构
                Path("/Users/apple/aicode/.worktrees/test-platform/agent/.agent.pid"),  # 绝对路径
            ]

            pid_file = None
            for path in possible_paths:
                if path.exists():
                    pid_file = path
                    break

            if not pid_file:
                return {
                    "id": "agent",
                    "name": "Agent",
                    "status": "down",
                    "message": "未找到 PID 文件"
                }

            pid = int(pid_file.read_text().strip())

            # 检查进程是否存在
            try:
                os.kill(pid, 0)
            except OSError:
                return {
                    "id": "agent",
                    "name": "Agent",
                    "status": "down",
                    "message": f"进程 {pid} 不运行"
                }

            # 获取进程信息
            try:
                ps_result = subprocess.run(
                    ['ps', '-p', str(pid), '-o', 'pcpu,rss,etime'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                if ps_result.returncode == 0:
                    lines = ps_result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split()
                        cpu_percent = float(parts[0])
                        memory_mb = int(parts[1]) / 1024
                        elapsed_time = parts[2]

                        return {
                            "id": "agent",
                            "name": "Agent",
                            "status": "healthy",
                            "message": f"运行中 (PID: {pid})",
                            "details": {
                                "pid": pid,
                                "cpu_percent": cpu_percent,
                                "memory_mb": round(memory_mb, 2),
                                "elapsed_time": elapsed_time
                            }
                        }
            except Exception:
                pass

            return {
                "id": "agent",
                "name": "Agent",
                "status": "healthy",
                "message": f"运行中 (PID: {pid})",
                "details": {"pid": pid}
            }

        except ValueError:
            return {
                "id": "agent",
                "name": "Agent",
                "status": "degraded",
                "message": "PID 文件格式错误"
            }
        except Exception as e:
            return {
                "id": "agent",
                "name": "Agent",
                "status": "down",
                "message": f"检查失败: {str(e)}"
            }

    async def check_docker_services(self) -> List[Dict[str, Any]]:
        """检查 Docker 容器"""
        services = {
            "test-platform-db": "PostgreSQL",
            "test-platform-redis": "Redis",
            "test-platform-backend": "后端容器",
            "test-platform-frontend": "前端容器"
        }

        results = []

        for container, name in services.items():
            try:
                ps_result = subprocess.run(
                    ['docker', 'inspect', '-f', '{{.State.Status}}', container],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                if ps_result.returncode == 0:
                    status = ps_result.stdout.strip()
                    results.append({
                        "name": name,
                        "status": "healthy" if status == "running" else "down",
                        "message": f"容器状态: {status}"
                    })
                else:
                    results.append({
                        "name": name,
                        "status": "down",
                        "message": "容器不存在"
                    })

            except FileNotFoundError:
                results.append({
                    "name": name,
                    "status": "degraded",
                    "message": "Docker 不可用"
                })
            except Exception as e:
                results.append({
                    "name": name,
                    "status": "degraded",
                    "message": f"检查失败: {str(e)}"
                })

        return results

    async def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        results = []

        # 检查后端
        backend_result = await self.check_backend()
        results.append(backend_result)

        # 检查前端
        frontend_result = await self.check_frontend()
        results.append(frontend_result)

        # 检查 Agent
        agent_result = await self.check_agent()
        results.append(agent_result)

        # 检查 Docker 服务
        docker_results = await self.check_docker_services()
        results.extend(docker_results)

        # 计算总体状态（仅基于核心服务：后端、前端、Agent）
        core_services = results[:3]  # 前3个是核心服务
        healthy_count = sum(1 for r in core_services if r["status"] == "healthy")
        degraded_count = sum(1 for r in core_services if r["status"] == "degraded")
        down_count = sum(1 for r in core_services if r["status"] == "down")

        if down_count > 0:
            overall = "down"
        elif degraded_count > 0:
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "timestamp": datetime.now().isoformat(),
            "overall": overall,
            "summary": {
                "total": len(results),
                "healthy": healthy_count,
                "degraded": degraded_count,
                "down": down_count
            },
            "services": results
        }


# 全局健康检查器实例
health_checker = HealthChecker()


@router.get("/health")
async def get_health_status():
    """获取系统健康状态"""
    # 检查缓存
    if health_checker.check_cache():
        return health_checker.cached_result

    # 运行检查
    result = await health_checker.run_all_checks()

    # 更新缓存
    health_checker.last_check = time.time()
    health_checker.cached_result = result

    return result


@router.post("/health/refresh")
async def refresh_health_status():
    """强制刷新健康状态"""
    result = await health_checker.run_all_checks()

    # 更新缓存
    health_checker.last_check = time.time()
    health_checker.cached_result = result

    return result
