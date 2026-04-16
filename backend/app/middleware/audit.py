"""
审计日志中间件

自动记录所有敏感操作，包括：
- 登录/登出
- 创建/更新/删除操作
- 测试执行操作
"""
from sqlalchemy.orm import Session
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.database import get_db
from ..models.audit import AuditLog
import logging

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计日志中间件

    记录所有敏感操作
    """

    # 需要审计的路径模式
    AUDIT_PATHS = {
        "/api/v1/auth/login": "login",
        "/api/v1/auth/logout": "logout",
        "/api/v1/projects": "project",
        "/api/v1/data": "data",
        "/api/v1/keywords": "keyword",
        "/api/v1/scenarios": "scenario",
        "/api/v1/cases": "case",
        "/api/v1/steps": "step",
        "/api/v1/tasks": "task",
        "/api/v1/executions": "execution",
    }

    async def dispatch(self, request: Request, call_next):
        # 只审计需要审计的路径
        path = request.url.path
        action = self._get_action_from_path(path)

        if action is None:
            # 不需要审计的路径，直接通过
            return await call_next(request)

        # 获取请求信息
        method = request.method

        # 执行请求
        response = await call_next(request)

        # 记录审计日志（异步）
        try:
            await self._log_audit(request, response, action, method)
        except Exception as e:
            # 审计日志失败不应该影响业务
            logger.error(f"审计日志记录失败: {e}")

        return response

    def _get_action_from_path(self, path: str) -> str | None:
        """从路径获取操作类型"""
        for audit_path, action in self.AUDIT_PATHS.items():
            if path.startswith(audit_path):
                return action
        return None

    async def _log_audit(self, request: Request, response, action: str, method: str):
        """记录审计日志"""
        try:
            # 获取数据库会话
            db: Session = next(get_db())

            # 从请求中提取信息
            client_ip = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            # 获取用户ID（如果有）
            user_id = None
            try:
                # 从 JWT token 中提取用户信息
                from ..core.security import verify_token

                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    payload = verify_token(token)
                    if payload:
                        # 从数据库获取用户ID
                        from ..models.user import User
                        user = db.query(User).filter(User.username == payload.get("sub")).first()
                        if user:
                            user_id = user.id
            except Exception as e:
                logger.debug(f"无法从 token 获取用户信息: {e}")

            # 检查是否从 Cookie 获取 token
            if not user_id:
                try:
                    from ..core.security import verify_token

                    token = request.cookies.get("access_token")
                    if token:
                        payload = verify_token(token)
                        if payload:
                            from ..models.user import User
                            user = db.query(User).filter(User.username == payload.get("sub")).first()
                            if user:
                                user_id = user.id
                except Exception as e:
                    logger.debug(f"无法从 Cookie 获取用户信息: {e}")

            # 确定 HTTP 方法对应的具体操作
            http_action = self._get_http_action(action, method)

            # 提取资源ID
            resource_id = self._extract_resource_id(request.url.path)

            # 判断操作是否成功
            success = 200 <= response.status_code < 300

            # 创建审计日志
            audit_log = AuditLog(
                action=http_action,
                resource_type=action,
                resource_id=resource_id,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                success=success,
                details={
                    "method": method,
                    "path": request.url.path,
                    "status_code": response.status_code
                }
            )

            db.add(audit_log)
            db.commit()

            logger.info(f"审计日志已记录: {http_action} {action} by user {user_id}")

        except Exception as e:
            logger.error(f"记录审计日志时发生错误: {e}")
            raise

    def _get_http_action(self, resource_type: str, method: str) -> str:
        """根据 HTTP 方法和资源类型确定操作类型"""
        # 特殊处理登录/登出
        if resource_type == "login":
            return "login"
        if resource_type == "logout":
            return "logout"

        # 根据 HTTP 方法映射操作
        action_map = {
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
            "GET": "view"
        }

        return action_map.get(method, "unknown")

    def _extract_resource_id(self, path: str) -> str | None:
        """从路径中提取资源ID"""
        # 示例：/api/v1/projects/123 -> 123
        parts = path.split("/")
        if len(parts) >= 5:
            # 检查最后一段是否是UUID
            potential_id = parts[4]
            if len(potential_id) == 36:  # UUID格式
                return potential_id
        return None
