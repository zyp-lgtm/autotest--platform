"""
缓存管理 API
提供缓存查询和管理功能
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Dict, Any

from ..utils.cache import get_cache, invalidate_pattern
from ..core.security import verify_token

router = APIRouter(prefix="/cache", tags=["缓存管理"])


class CacheStatsResponse(BaseModel):
    """缓存统计响应"""
    total_requests: int
    hits: int
    misses: int
    hit_rate: str
    size: int
    sets: int
    deletes: int
    evictions: int


class CacheInvalidateRequest(BaseModel):
    """缓存失效请求"""
    pattern: str


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="api/v1/auth/login"))
):
    """
    获取缓存统计信息

    返回缓存命中率、大小等统计信息
    """
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    cache = get_cache()
    stats = cache.get_stats()

    return CacheStatsResponse(
        total_requests=stats['hits'] + stats['misses'],
        hits=stats['hits'],
        misses=stats['misses'],
        hit_rate=stats['hit_rate'],
        size=stats['size'],
        sets=stats['sets'],
        deletes=stats['deletes'],
        evictions=stats['evictions']
    )


@router.post("/invalidate")
async def invalidate_cache(
    request: CacheInvalidateRequest,
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="api/v1/auth/login"))
):
    """
    使缓存失效

    支持通配符模式匹配
    例如：`list_keywords:*` 会清除所有 list_keywords 相关的缓存
    """
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        count = invalidate_pattern(request.pattern)
        return {
            "success": True,
            "message": f"已清除 {count} 个缓存项",
            "pattern": request.pattern,
            "count": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清除缓存失败: {str(e)}"
        )


@router.post("/clear")
async def clear_all_cache(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="api/v1/auth/login"))
):
    """
    清空所有缓存

    注意：这会清除所有缓存项，谨慎使用
    """
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    cache = get_cache()
    size = cache.get_size()
    cache.clear()

    return {
        "success": True,
        "message": f"已清空所有缓存，共 {size} 项",
        "count": size
    }


@router.post("/cleanup")
async def cleanup_expired_cache(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="api/v1/auth/login"))
):
    """
    清理过期缓存

    自动清理已过期的缓存项
    """
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    cache = get_cache()
    count = cache.cleanup_expired()

    return {
        "success": True,
        "message": f"已清理 {count} 个过期缓存项",
        "count": count
    }
