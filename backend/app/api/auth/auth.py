from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.user import User
from ...core.security import create_access_token, verify_token, hash_password, verify_password
from ...schemas.user import UserCreate, UserResponse
import logging
import re

logger = logging.getLogger(__name__)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度

    Args:
        password: 密码

    Returns:
        (是否有效, 错误消息)
    """
    if len(password) < 6:
        return False, "密码长度至少为 6 位"

    if len(password) > 128:
        return False, "密码长度不能超过 128 位"

    # 检查是否包含至少一个字母
    if not re.search(r'[A-Za-z]', password):
        return False, "密码必须包含至少一个字母"

    # 检查是否包含至少一个数字
    if not re.search(r'\d', password):
        return False, "密码必须包含至少一个数字"

    return True, ""

router = APIRouter(prefix="/auth", tags=["认证"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 验证密码强度
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
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
    logger.info(f"Creating user {user_data.username} with hashed password")

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
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user