"""
CSRF 保护模块

提供 CSRF Token 生成和验证功能
"""
import secrets
import hashlib
from typing import Optional
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..models.user import User
import time


class CSRFProtection:
    """CSRF 保护类"""

    def __init__(self, secret_key: str = None):
        """
        初始化 CSRF 保护

        Args:
            secret_key: 用于签名的密钥（从配置读取）
        """
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.token_length = 43  # CSRF token 长度

    def generate_token(self, session_id: str) -> str:
        """
        生成 CSRF Token

        Args:
            session_id: 会话 ID（使用用户 ID 或会话标识）

        Returns:
            CSRF Token
        """
        # 生成随机 token
        random_token = secrets.token_urlsafe(self.token_length)

        # 创建签名：hash(session_id + random_token + secret_key)
        signature = hashlib.sha256(
            f"{session_id}:{random_token}:{self.secret_key}".encode()
        ).hexdigest()

        # 组合 token：random_token.signature
        csrf_token = f"{random_token}.{signature}"

        return csrf_token

    def verify_token(self, token: str, session_id: str) -> bool:
        """
        验证 CSRF Token

        Args:
            token: CSRF Token
            session_id: 会话 ID

        Returns:
            验证是否通过
        """
        if not token or not session_id:
            return False

        try:
            # 分离 token 和签名
            parts = token.split('.')
            if len(parts) != 2:
                return False

            random_token, signature = parts

            # 重新计算签名
            expected_signature = hashlib.sha256(
                f"{session_id}:{random_token}:{self.secret_key}".encode()
            ).hexdigest()

            # 使用 secrets.compare_lock 防止时序攻击
            return secrets.compare_digest(signature, expected_signature)

        except Exception:
            return False

    def validate_request(
        self,
        request: Request,
        token_header: str = "X-CSRF-Token",
        token_field: str = "csrf_token"
    ) -> bool:
        """
        验证请求中的 CSRF Token

        Args:
            request: FastAPI 请求对象
            token_header: CSRF Token 所在的 HTTP 头
            token_field: CSRF Token 所在的表单字段

        Returns:
            验证是否通过

        Raises:
            HTTPException: 验证失败时抛出 403 错误
        """
        # 从请求头获取 token
        csrf_token = request.headers.get(token_header)

        # 如果请求头没有，尝试从表单/JSON 获取
        if not csrf_token:
            # 尝试从表单数据获取
            form_data = getattr(request, '_form', None)
            if form_data and token_field in form_data:
                csrf_token = form_data[token_field]
            else:
                # 尝试从 JSON 数据获取
                json_data = getattr(request, '_json', None)
                if json_data and token_field in json_data:
                    csrf_token = json_data[token_field]

        # 从 session 获取 session_id
        # 这里使用用户 ID 作为 session_id
        # 在实际应用中，应该从 session 中获取
        session_id = request.state.get("user_id")

        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="缺少会话信息"
            )

        if not csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="缺少 CSRF Token"
            )

        if not self.verify_token(csrf_token, session_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无效的 CSRF Token"
            )

        return True


# 全局 CSRF 保护实例
csrf_protect = CSRFProtection()


def get_csrf_token(session_id: str) -> str:
    """
    获取 CSRF Token（便捷函数）

    Args:
        session_id: 会话 ID

    Returns:
        CSRF Token
    """
    return csrf_protect.generate_token(session_id)


def verify_csrf_token(token: str, session_id: str) -> bool:
    """
    验证 CSRF Token（便捷函数）

    Args:
        token: CSRF Token
        session_id: 会话 ID

    Returns:
        验证是否通过
    """
    return csrf_protect.verify_token(token, session_id)
