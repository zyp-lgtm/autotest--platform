from fastapi import APIRouter, Depends, HTTPException, status
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
    oauth2_scheme
)
from ...core.csrf import get_csrf_token
from ...schemas.user import UserCreate, UserResponse
import logging

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
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "csrf_token": csrf_token
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user


@router.get("/csrf-token")
async def get_csrf(token: str = Depends(oauth2_scheme)):
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