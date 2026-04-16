from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
try:
    from jose import ExpiredSignatureError
except ImportError:
    # 旧版本可能没有这个异常
    ExpiredSignatureError = JWTError
import bcrypt
import base64
import secrets
from fastapi.security.oauth2 import OAuth2PasswordBearer
from fastapi import HTTPException, status, Depends, Cookie, Request
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from ..models.user import User
import logging

logger = logging.getLogger(__name__)

# 密码哈希上下文（备用）
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_EXPIRATION)
    to_encode.update({"exp": expire})
    logger.info(f"[create_access_token] 使用 JWT_SECRET: {settings.JWT_SECRET[:20]}...")
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    logger.info(f"[create_access_token] 生成的 Token: {encoded_jwt[:30]}...")
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        logger.info(f"[verify_token] 使用 JWT_SECRET: {settings.JWT_SECRET[:20]}...")
        logger.info(f"[verify_token] Token 前缀: {token[:30]}...")
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        logger.info(f"[verify_token] Token 验证成功: {payload}")
        return payload
    except ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        logger.warning(f"[verify_token] JWT_SECRET: {settings.JWT_SECRET[:20]}...")
        logger.warning(f"[verify_token] Token: {token[:30]}...")
        return None


def hash_password(password: str) -> str:
    """
    哈希密码

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    # bcrypt 有 72 字节限制
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        密码是否匹配
    """
    # 同样需要截断
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    验证密码强度

    Args:
        password: 待验证的密码

    Returns:
        (是否通过强度要求, 错误信息列表)
    """
    errors = []

    if len(password) < 8:
        errors.append("密码长度至少为 8 位")

    if not any(c.isupper() for c in password):
        errors.append("密码必须包含至少一个大写字母")

    if not any(c.islower() for c in password):
        errors.append("密码必须包含至少一个小写字母")

    if not any(c.isdigit() for c in password):
        errors.append("密码必须包含至少一个数字")

    # 检查常见弱密码
    common_passwords = ["password", "12345678", "qwerty123", "abc12345"]
    if password.lower() in common_passwords:
        errors.append("密码不能是常见弱密码")

    return len(errors) == 0, errors


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    获取当前认证用户

    Args:
        token: JWT token

    Returns:
        用户 payload

    Raises:
        HTTPException: 如果 token 无效
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    return payload


def generate_secure_secret(length: int = 32) -> str:
    """
    生成安全的随机密钥

    Args:
        length: 密钥长度（字节）

    Returns:
        URL 安全的随机密钥
    """
    return secrets.token_urlsafe(length)


# Cookie-based authentication for HttpOnly cookies
class CookieAuthScheme:
    """
    从 Cookie 中读取 access_token 的认证方案
    与 Header Bearer token 兼容
    """

    async def __call__(self, request) -> Optional[str]:
        # 首先尝试从 Authorization header 获取（向后兼容）
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            logger.debug(f"[CookieAuth] 从 Authorization header 获取 token: {token[:20]}...")
            return token

        # 然后尝试从 Cookie 获取
        token = request.cookies.get("access_token")
        if token:
            logger.debug(f"[CookieAuth] 从 Cookie 获取 token: {token[:20]}...")
            return token

        logger.debug("[CookieAuth] 未找到 token")
        return None


# 创建 Cookie 认证方案实例
cookie_scheme = CookieAuthScheme()


async def get_token_from_cookie_or_header(request: Request) -> str:
    """
    从 Cookie 或 Header 获取 token

    优先级：
    1. Authorization header (Bearer token)
    2. Cookie (HttpOnly cookie)

    Args:
        request: FastAPI Request 对象

    Returns:
        有效的 JWT token

    Raises:
        HTTPException: 如果没有找到有效的 token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 首先尝试从 Authorization header 获取（向后兼容）
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        logger.debug(f"[get_token_from_cookie_or_header] 使用 Header token: {token[:20]}...")
        return token

    # 然后尝试从 Cookie 获取
    token = request.cookies.get("access_token")
    if token:
        logger.debug(f"[get_token_from_cookie_or_header] 使用 Cookie token: {token[:20]}...")
        return token

    # 都没有则抛出异常
    logger.warning("[get_token_from_cookie_or_header] 未找到 token")
    raise credentials_exception


# ============================================================================
# 认证依赖函数 - 消除代码重复
# ============================================================================

async def get_authenticated_user(
    token: str = Depends(get_token_from_cookie_or_header),
    db: Session = Depends(get_db)
) -> User:
    """
    从 Cookie 或 Header 获取 token 并验证，返回当前用户

    统一的认证依赖函数，替代各 API 端点中重复的认证逻辑

    Args:
        token: JWT token (从 Cookie 或 Header 自动获取)
        db: 数据库会话

    Returns:
        User: 当前认证用户对象

    Raises:
        HTTPException: 认证失败时抛出 401 错误

    Usage:
        from fastapi import Depends
        from app.core.security import get_authenticated_user

        @router.get("/api/endpoint")
        async def my_endpoint(user: User = Depends(get_authenticated_user)):
            return {"username": user.username}
    """
    # 验证 token
    payload = verify_token(token)
    if not payload:
        raise credentials_exception

    # 获取用户信息
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    logger.debug(f"[get_authenticated_user] 用户认证成功: {user.username}")
    return user


async def require_admin(
    current_user: User = Depends(get_authenticated_user)
) -> User:
    """
    要求管理员权限的依赖函数

    Args:
        current_user: 当前认证用户

    Returns:
        User: 当前管理员用户

    Raises:
        HTTPException: 非管理员用户抛出 403 错误

    Usage:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(admin_user: User = Depends(require_admin)):
            return {"message": "用户已删除"}
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    logger.debug(f"[require_admin] 管理员权限验证通过: {current_user.username}")
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(get_token_from_cookie_or_header),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    可选的用户认证 - 允许匿名访问

    如果提供了有效的 token，返回用户对象；否则返回 None

    Args:
        token: JWT token (可选)
        db: 数据库会话

    Returns:
        Optional[User]: 用户对象或 None

    Usage:
        @router.get("/public/content")
        async def public_content(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.username}"}
            return {"message": "Hello, anonymous!"}
    """
    if not token:
        return None

    try:
        payload = verify_token(token)
        if not payload:
            return None

        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        return user if user and user.is_active else None

    except Exception:
        return None