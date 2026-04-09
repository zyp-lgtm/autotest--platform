"""
调试文件服务 API
提供测试执行产生的调试文件（截图、HTML快照、JSON报告）的访问
"""
import os
import mimetypes
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

router = APIRouter()


def get_debug_base_path() -> Path:
    """获取调试文件基础路径"""
    # 从环境变量或配置读取，默认使用项目根目录下的 debug 文件夹
    debug_path = os.getenv("DEBUG_FILES_PATH", "debug")
    return Path(debug_path).resolve()


def sanitize_path(file_path: str) -> Path:
    """
    清理和验证文件路径，防止路径遍历攻击
    """
    # 解码 URL 编码的路径
    from urllib.parse import unquote
    clean_path = unquote(file_path)

    # 移除任何 ../ 或 ./ 等路径遍历字符
    clean_path = clean_path.replace('..', '').replace('./', '')

    # 构建完整路径
    base_path = get_debug_base_path()
    full_path = (base_path / clean_path).resolve()

    # 验证路径是否在基础路径内
    if not str(full_path).startswith(str(base_path)):
        raise HTTPException(
            status_code=403,
            detail="访问被拒绝：无效的文件路径"
        )

    return full_path


@router.get("/files/debug")
async def get_debug_file(path: str):
    """
    获取调试文件（截图、HTML快照、JSON报告等）

    参数:
        path: 文件相对路径（相对于 DEBUG_FILES_PATH）

    返回:
        文件内容或 404 错误
    """
    try:
        file_path = sanitize_path(path)

        # 检查文件是否存在
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {path}"
            )

        # 检查是否为文件（不是目录）
        if not file_path.is_file():
            raise HTTPException(
                status_code=400,
                detail="请求的不是有效文件"
            )

        # 获取 MIME 类型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            # 默认处理
            if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                mime_type = f'image/{file_path.suffix[1:]}'
            elif file_path.suffix.lower() == '.svg':
                mime_type = 'image/svg+xml'
            elif file_path.suffix.lower() == '.html':
                mime_type = 'text/html'
            elif file_path.suffix.lower() == '.json':
                mime_type = 'application/json'
            else:
                mime_type = 'application/octet-stream'

        # 返回文件
        return FileResponse(
            path=str(file_path),
            media_type=mime_type,
            filename=file_path.name,
            headers={
                "Cache-Control": "public, max-age=3600",  # 缓存 1 小时
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"读取文件失败: {str(e)}"
        )


@router.get("/files/debug/list")
async def list_debug_files(path: Optional[str] = None):
    """
    列出调试目录中的文件

    参数:
        path: 可选的子目录路径

    返回:
        文件和目录列表
    """
    try:
        base_path = get_debug_base_path()

        if path:
            list_path = sanitize_path(path)
        else:
            list_path = base_path

        if not list_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"目录不存在: {path or ''}"
            )

        if not list_path.is_dir():
            raise HTTPException(
                status_code=400,
                detail="请求的不是目录"
            )

        # 列出内容
        items = []
        for item in list_path.iterdir():
            item_info = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
                "modified": item.stat().st_mtime,
            }

            # 计算相对路径
            try:
                relative_path = item.relative_to(base_path)
                item_info["path"] = str(relative_path)
            except ValueError:
                item_info["path"] = item.name

            items.append(item_info)

        # 按类型和名称排序
        items.sort(key=lambda x: (x["type"] == "file", x["name"]))

        return {
            "path": path or "",
            "items": items
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"列出文件失败: {str(e)}"
        )


@router.delete("/files/debug")
async def delete_debug_file(path: str):
    """
    删除调试文件

    参数:
        path: 文件相对路径

    返回:
        删除结果
    """
    try:
        file_path = sanitize_path(path)

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {path}"
            )

        # 删除文件或目录
        if file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)
        else:
            file_path.unlink()

        return {
            "success": True,
            "message": f"已删除: {path}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除文件失败: {str(e)}"
        )
