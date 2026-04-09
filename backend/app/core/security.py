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
from fastapi import HTTPException, status, Depends
from .config import get_settings
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
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
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