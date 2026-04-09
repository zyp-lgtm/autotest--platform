"""
服务管理 API
提供服务启动、停止、重启功能
"""
import subprocess
import os
import signal
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
import socket

from ..core.security import verify_token, oauth2_scheme

router = APIRouter()


class ServiceManager:
    """服务管理器"""

    def __init__(self):
        self.services = {
            "backend": {
                "name": "后端 API",
                "start_cmd": "python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload",
                "working_dir": "/Users/apple/aicode/.worktrees/test-platform/backend",
                "pid_file": "/tmp/backend.pid",
                "log_file": "/tmp/backend.log",
                "port": 8000,
                "process_name": "uvicorn"
            },
            "frontend": {
                "name": "前端服务",
                "start_cmd": "npm run dev",
                "working_dir": "/Users/apple/aicode/.worktrees/test-platform/frontend",
                "pid_file": "/tmp/frontend.pid",
                "log_file": "/tmp/frontend.log",
                "port": 3000,
                "process_name": "vite"
            },
            "agent": {
                "name": "Agent",
                "start_cmd": "bash start_agent.sh",
                "working_dir": "/Users/apple/aicode/.worktrees/test-platform/agent",
                "pid_file": "/Users/apple/aicode/.worktrees/test-platform/agent/.agent.pid",
                "log_file": "/tmp/agent.log",
                "port": None,
                "process_name": "agent.py"
            }
        }

    def _get_pid(self, service_id: str) -> int | None:
        """获取服务进程 PID"""
        config = self.services.get(service_id)
        if not config:
            return None

        pid_file = Path(config["pid_file"])
        if pid_file.exists():
            try:
                return int(pid_file.read_text().strip())
            except (ValueError, IOError):
                return None
        return None

    def _find_process_by_port(self, port: int) -> int | None:
        """通过端口查找进程 PID"""
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                return int(pids[0])  # 返回第一个PID
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            pass
        return None

    def _is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            return False
        except OSError:
            return True

    def _is_running(self, service_id: str) -> bool:
        """检查服务是否运行"""
        config = self.services.get(service_id)
        if not config:
            return False

        # 优先通过端口检查
        if config.get("port"):
            if self._is_port_in_use(config["port"]):
                return True

        # 其次通过PID文件检查
        pid = self._get_pid(service_id)
        if pid:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                pass

        return False

    async def start_service(self, service_id: str) -> Dict[str, Any]:
        """启动服务"""
        config = self.services.get(service_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"服务 {service_id} 不存在")

        # 检查是否已在运行
        is_running = self._is_running(service_id)

        # Agent 特殊处理：清理过期的 PID 文件
        if service_id == "agent":
            pid_file = Path(config["pid_file"])
            if pid_file.exists() and not is_running:
                # PID 文件存在但进程不在运行，清理它
                try:
                    old_pid = int(pid_file.read_text().strip())
                    # 再次确认进程不存在
                    try:
                        os.kill(old_pid, 0)
                        # 进程确实存在，不能启动
                        return {
                            "success": False,
                            "message": f"{config['name']} 已在运行 (PID: {old_pid})"
                        }
                    except OSError:
                        # 进程不存在，清理 PID 文件
                        pid_file.unlink()
                        print(f"[Agent] 清理过期 PID 文件: {old_pid}")
                except (ValueError, IOError):
                    pid_file.unlink()

        # 重新检查运行状态
        if self._is_running(service_id):
            # 尝试找到现有进程并更新PID文件
            if config.get("port"):
                existing_pid = self._find_process_by_port(config["port"])
                if existing_pid:
                    Path(config["pid_file"]).write_text(str(existing_pid))
                    return {
                        "success": True,
                        "message": f"{config['name']} 已在运行 (PID: {existing_pid})",
                        "already_running": True
                    }
            return {
                "success": False,
                "message": f"{config['name']} 已在运行"
            }

        try:
            # Agent 需要直接调用启动脚本
            if service_id == "agent":
                # 清理旧的 PID 文件
                Path(config["pid_file"]).unlink(missing_ok=True)

                # 直接调用启动脚本（脚本内部已处理 nohup 和输出重定向）
                # start_cmd 已经是 "bash start_agent.sh"，所以直接执行即可
                cmd = f"cd {config['working_dir']} && {config['start_cmd']}"
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    start_new_session=True
                )

                # 等待一下让进程启动
                await asyncio.sleep(2)

                # 读取PID文件获取实际PID
                try:
                    actual_pid = int(Path(config["pid_file"]).read_text().strip())
                    print(f"[Agent] Agent 启动，PID: {actual_pid}")
                except:
                    print(f"[Agent] 无法读取PID文件，使用启动的PID: {process.pid}")
            else:
                log_file = open(config["log_file"], "a")
                process = subprocess.Popen(
                    config["start_cmd"],
                    shell=True,
                    cwd=config["working_dir"],
                    stdout=log_file,
                    stderr=log_file,
                    start_new_session=True
                )

            # 等待服务启动
            wait_time = 5 if service_id == "agent" else 3
            if service_id == "frontend":
                wait_time = 5  # 前端需要更长的启动时间
            await asyncio.sleep(wait_time)

            # Agent 使用后台进程，无法通过 process.poll() 检查
            if service_id == "agent":
                # 通过检查PID文件和进程是否存在来判断
                try:
                    actual_pid = int(Path(config["pid_file"]).read_text().strip())
                    # 检查进程是否真的在运行
                    os.kill(actual_pid, 0)
                    return {
                        "success": True,
                        "message": f"{config['name']} 启动成功",
                        "pid": actual_pid
                    }
                except (OSError, ValueError, IOError):
                    # 进程不存在或PID文件无效
                    Path(config["pid_file"]).unlink(missing_ok=True)
                    return {
                        "success": False,
                        "message": f"{config['name']} 启动后退出，请检查日志: {config['log_file']}"
                    }
            elif service_id == "frontend":
                # 前端服务：通过端口查找实际的 vite 进程 PID
                if config.get("port") and self._is_port_in_use(config["port"]):
                    actual_pid = self._find_process_by_port(config["port"])
                    if actual_pid:
                        # 写入实际的 PID
                        Path(config["pid_file"]).write_text(str(actual_pid))
                        return {
                            "success": True,
                            "message": f"{config['name']} 启动成功",
                            "pid": actual_pid
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"{config['name']} 启动后未在端口 {config['port']} 检测到进程"
                        }
                else:
                    return {
                        "success": False,
                        "message": f"{config['name']} 启动后端口 {config['port']} 未被占用"
                    }
            else:
                # 其他服务正常检查
                if process.poll() is None:
                    return {
                        "success": True,
                        "message": f"{config['name']} 启动成功",
                        "pid": process.pid
                    }
                else:
                    Path(config["pid_file"]).unlink(missing_ok=True)
                    return {
                        "success": False,
                        "message": f"{config['name']} 启动后退出，请检查日志: {config['log_file']}"
                    }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")

    async def stop_service(self, service_id: str) -> Dict[str, Any]:
        """停止服务"""
        config = self.services.get(service_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"服务 {service_id} 不存在")

        # 停止后端服务需要特殊处理：先返回响应，再停止
        if service_id == "backend":
            # 检查是否是后端自己停止自己
            pid = self._get_pid("backend")
            if pid:
                # 使用后台任务延迟停止，确保响应先返回
                asyncio.create_task(self._stop_backend_async(pid))
                return {
                    "success": True,
                    "message": f"{config['name']} 正在停止...",
                    "async": True
                }
            else:
                return {
                    "success": False,
                    "message": f"{config['name']} 未运行"
                }

        # 其他服务的正常停止逻辑
        pid = self._get_pid(service_id)
        if not pid:
            return {
                "success": False,
                "message": f"{config['name']} 未运行"
            }

        try:
            # 尝试杀死进程组
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                # 进程组不存在，尝试杀死单个进程
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

            # 等待进程退出
            for _ in range(10):
                await asyncio.sleep(0.5)
                try:
                    os.kill(pid, 0)
                except OSError:
                    # 进程已退出
                    Path(config["pid_file"]).unlink(missing_ok=True)
                    return {
                        "success": True,
                        "message": f"{config['name']} 已停止"
                    }

            # 如果进程还在运行，强制杀死
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

            Path(config["pid_file"]).unlink(missing_ok=True)
            return {
                "success": True,
                "message": f"{config['name']} 已停止"
            }
        except ProcessLookupError:
            Path(config["pid_file"]).unlink(missing_ok=True)
            return {
                "success": True,
                "message": f"{config['name']} 已停止"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"停止失败: {str(e)}")

    async def _stop_backend_async(self, pid: int):
        """异步停止后端服务"""
        try:
            # 等待1秒确保响应已发送
            await asyncio.sleep(1)

            # 尝试通过端口查找并停止
            config = self.services["backend"]
            if config.get("port"):
                actual_pid = self._find_process_by_port(config["port"])
                if actual_pid:
                    pid = actual_pid

            # 停止后端进程
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except ProcessLookupError:
                pass  # 进程已不存在

            await asyncio.sleep(2)
            # 清理PID文件
            Path("/tmp/backend.pid").unlink(missing_ok=True)
        except Exception as e:
            print(f"后台停止失败: {e}")

    async def restart_service(self, service_id: str) -> Dict[str, Any]:
        """重启服务"""
        config = self.services.get(service_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"服务 {service_id} 不存在")

        # 重启后端服务需要特殊处理
        if service_id == "backend":
            # 先停止后端
            pid = self._get_pid("backend")
            if pid:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                    print(f"[重启] 已停止后端 PID: {pid}")
                except ProcessLookupError:
                    pass

            # 等待一下确保停止信号已发送
            await asyncio.sleep(0.5)

            # 使用启动脚本来重启后端
            # 脚本会自动处理目录切换和端口占用
            script_path = "/Users/apple/aicode/.worktrees/test-platform/backend/start_backend.sh"
            subprocess.Popen(
                f"sleep 2 && cd {config['working_dir']} && bash {script_path}",
                shell=True,
                stdout=open("/tmp/backend_restart.log", "w"),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

            return {
                "success": True,
                "message": f"{config['name']} 正在后台重启...",
                "async": True
            }
        else:
            # 对于其他服务，先尝试停止
            # 如果服务未运行，stop_service 会返回 success: False，但我们应该继续
            pid = self._get_pid(service_id)
            if pid:
                # 服务在运行，先停止
                try:
                    await self.stop_service(service_id)
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"[重启] 停止服务时出错: {e}，继续启动...")

            # 无论停止是否成功，都尝试启动服务
            return await self.start_service(service_id)

    async def _restart_backend_async(self):
        """异步重启后端服务"""
        try:
            print("[重启] 开始异步重启后端...")

            # 先停止后端
            pid = self._get_pid("backend")
            if pid:
                print(f"[重启] 停止后端 PID: {pid}")
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except ProcessLookupError:
                    print("[重启] 进程已不存在")
                    pass
            else:
                print("[重启] 后端未运行")

            # 等待后端完全停止
            await asyncio.sleep(2)

            # 使用独立脚本启动后端
            script_path = "/Users/apple/aicode/.worktrees/test-platform/backend/start_backend.sh"
            print(f"[重启] 执行启动脚本: {script_path}")

            process = subprocess.Popen(
                ["/bin/bash", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            print(f"[重启] 启动脚本进程 PID: {process.pid}")

        except Exception as e:
            print(f"[重启] 后台重启失败: {e}")
            import traceback
            traceback.print_exc()


service_manager = ServiceManager()


@router.post("/services/{service_id}/start")
async def start_service(
    service_id: str,
    token: str = Depends(oauth2_scheme)
):
    """启动服务"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    return await service_manager.start_service(service_id)


@router.post("/services/{service_id}/stop")
async def stop_service(
    service_id: str,
    token: str = Depends(oauth2_scheme)
):
    """停止服务"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    return await service_manager.stop_service(service_id)


@router.post("/services/{service_id}/restart")
async def restart_service(
    service_id: str,
    token: str = Depends(oauth2_scheme)
):
    """重启服务"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    return await service_manager.restart_service(service_id)
