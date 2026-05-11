from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.user import User
from ...core.security import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    validate_password_strength,
    get_token_from_cookie_or_header
)
from ...core.csrf import get_csrf_token
from ...schemas.user import UserCreate, UserResponse
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 验证密码强度（使用安全模块中的增强版）
    is_valid, error_msgs = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(error_msgs)
        )

    # 检查用户是否存在
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已注册"
        )

    # 哈希密码
    hashed_pwd = hash_password(user_data.password)
    logger.info(f"Creating user {user_data.username}")  # 移除敏感信息

    # 创建用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User {user_data.username} created successfully")
    return new_user


@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        logger.warning(f"Login failed: user {form_data.username} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: invalid password for user {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    logger.info(f"User {form_data.username} logged in successfully")

    # 创建访问令牌
    access_token = create_access_token({"sub": user.username})

    # 生成 CSRF Token（使用用户 ID 作为 session_id）
    csrf_token = get_csrf_token(str(user.id))

    # 设置 HttpOnly Cookie
    # max_age: 24小时 = 86400秒
    # httponly: 防止 XSS 攻击窃取 cookie
    # secure: 生产环境需要 HTTPS
    # samesite: 防止 CSRF 攻击
    from ...core.config import get_settings
    settings = get_settings()

    is_production = settings.ENV == "production"

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=86400,  # 24小时
        httponly=True,
        secure=is_production,  # 生产环境需要 HTTPS
        samesite="lax",  # 防止 CSRF
        path="/"
    )

    # 同时在响应体中返回 token（用于向后兼容和 CSRF token）
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "csrf_token": csrf_token,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(get_token_from_cookie_or_header),
    db: Session = Depends(get_db)
):
    """获取当前用户信息（带缓存）"""
    from ...utils.cache import get_cache

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    username = payload.get("sub")

    # 尝试从缓存获取（使用 v2 缓存键）
    cache_key = f"user_info:v2:{username}"
    cache = get_cache()
    cached_user = cache.get(cache_key)
    if cached_user:
        return UserResponse(**cached_user)

    # 缓存未命中，查询数据库
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=user.role,
        created_at=user.created_at
    )

    # 存入缓存（10 分钟）
    cache.set(cache_key, user_response.model_dump(), ttl=600)

    return user_response
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user


@router.get("/csrf-token")
async def get_csrf(token: str = Depends(get_token_from_cookie_or_header)):
    """
    获取 CSRF Token

    返回一个新的 CSRF Token，用于后续的修改操作
    """
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    # 从 payload 中获取用户信息
    username = payload.get("sub")

    # 这里简化处理，使用 username 作为 session_id
    # 在实际应用中，应该使用用户 ID 或会话 ID
    csrf_token = get_csrf_token(username)

    return {
        "csrf_token": csrf_token
    }