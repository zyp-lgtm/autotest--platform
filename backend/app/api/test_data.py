"""
测试数据管理 API

提供测试数据的 CRUD 操作和数据绑定功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..models.test_data import TestData, DataBinding
from ..models.user import User
from ..models.ui_task import UICase
from ..core.database import get_db
from ..core.security import get_authenticated_user
from .utils import validate_and_fetch, validate_uuid, serialize_model
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test-data", tags=["测试数据管理"])


@router.post("/")
async def create_test_data(
    data: dict,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建测试数据"""
    try:
        project_id = data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id 是必需的")

        # 转换为UUID对象
        try:
            project_id_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的 project_id 格式")

        # 验证项目存在
        from ..models.project import Project
        project = db.query(Project).filter(Project.id == project_id_uuid).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 创建测试数据
        new_data = TestData(
            project_id=project_id_uuid,
            name=data.get("name"),
            description=data.get("description"),
            data_type=data.get("data_type", "json"),
            data=data.get("data", []),
            tags=data.get("tags", []),
            created_by=user.id
        )

        db.add(new_data)
        db.commit()
        db.refresh(new_data)

        logger.info(f"用户 {user.username} 创建测试数据: {new_data.name}")
        return serialize_model(new_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建测试数据失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建测试数据失败: {str(e)}")


@router.get("/")
async def list_test_data(
    project_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取测试数据列表"""
    query = db.query(TestData)

    if project_id:
        # 转换 project_id 为 UUID
        try:
            project_id_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            query = query.filter(TestData.project_id == project_id_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的 project_id 格式")

    test_data_list = query.order_by(TestData.created_at.desc()).offset(skip).limit(limit).all()

    return [serialize_model(data) for data in test_data_list]


@router.get("/{data_id}")
async def get_test_data(
    data_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取测试数据详情"""
    data_uuid = validate_uuid(data_id, "测试数据")
    test_data = validate_and_fetch(db, TestData, data_id, "测试数据")
    return serialize_model(test_data)


@router.put("/{data_id}")
async def update_test_data(
    data_id: str,
    data_update: dict,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新测试数据"""
    test_data = validate_and_fetch(db, TestData, data_id, "测试数据")

    update_fields = ["name", "description", "data", "data_type", "tags"]
    for field in update_fields:
        if field in data_update:
            setattr(test_data, field, data_update[field])

    db.commit()
    db.refresh(test_data)

    logger.info(f"用户 {user.username} 更新测试数据: {test_data.name}")
    return serialize_model(test_data)


@router.delete("/{data_id}")
async def delete_test_data(
    data_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除测试数据"""
    try:
        test_data = validate_and_fetch(db, TestData, data_id, "测试数据")

        # 检查是否有关联的有效绑定（case 仍然存在的）
        valid_bindings = db.query(DataBinding).join(
            UICase, DataBinding.case_id == UICase.id
        ).filter(DataBinding.data_id == test_data.id).all()

        if valid_bindings:
            # 获取用例名称用于提示
            case_names = [db.query(UICase).filter(UICase.id == b.case_id).first().name
                          for b in valid_bindings]
            raise HTTPException(
                status_code=400,
                detail=f"测试数据被以下用例使用，无法删除: {', '.join(case_names)}"
            )

        # 删除所有相关的绑定记录（包括孤立的绑定）
        all_bindings = db.query(DataBinding).filter(DataBinding.data_id == test_data.id).all()
        for binding in all_bindings:
            db.delete(binding)

        # 删除测试数据
        db.delete(test_data)
        db.commit()

        logger.info(f"用户 {user.username} 删除测试数据: {test_data.name}, 清理了 {len(all_bindings)} 条绑定记录")
        return {"message": "测试数据已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除测试数据失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除测试数据失败: {str(e)}")


# 数据绑定管理

@router.post("/bindings")
async def bind_data_to_case(
    binding: dict,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """绑定测试数据到用例"""
    try:
        case_id = binding.get("case_id")
        data_id = binding.get("data_id")

        if not case_id or not data_id:
            raise HTTPException(status_code=400, detail="case_id 和 data_id 是必需的")

        # 验证用例存在
        test_case = db.query(UICase).filter(UICase.id == case_id).first()
        if not test_case:
            raise HTTPException(status_code=404, detail="用例不存在")

        # 验证测试数据存在
        test_data = db.query(TestData).filter(TestData.id == data_id).first()
        if not test_data:
            raise HTTPException(status_code=404, detail="测试数据不存在")

        # 检查绑定是否已存在
        existing = db.query(DataBinding).filter(
            DataBinding.case_id == case_id,
            DataBinding.data_id == data_id
        ).first()

        if existing:
            # 如果已存在，更新启用状态
            existing.enabled = 1 if binding.get("enabled", True) else 0
            db.commit()
            return serialize_model(existing)

        # 创建新绑定
        new_binding = DataBinding(
            case_id=case_id,
            data_id=data_id,
            enabled=1 if binding.get("enabled", True) else 0
        )

        db.add(new_binding)
        db.commit()
        db.refresh(new_binding)

        logger.info(f"用户 {user.username} 绑定数据到用例: {test_case.name} <- {test_data.name}")
        return serialize_model(new_binding)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"绑定数据失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"绑定数据失败: {str(e)}")


@router.get("/bindings/case/{case_id}")
async def get_case_bindings(
    case_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取用例的所有数据绑定"""
    from ..api.utils import validate_uuid
    case_uuid = validate_uuid(case_id, "用例")

    bindings = db.query(DataBinding).filter(
        DataBinding.case_id == case_uuid,
        DataBinding.enabled == 1
    ).all()

    result = []
    for binding in bindings:
        # 获取关联的测试数据
        test_data = db.query(TestData).filter(TestData.id == binding.data_id).first()
        if test_data:
            binding_data = serialize_model(binding)
            binding_data["test_data"] = serialize_model(test_data)
            result.append(binding_data)

    return result


@router.delete("/bindings/{binding_id}")
async def unbind_data(
    binding_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """解除数据绑定"""
    from ..api.utils import validate_uuid
    binding_uuid = validate_uuid(binding_id, "绑定")

    try:
        binding = db.query(DataBinding).filter(DataBinding.id == binding_uuid).first()
        if not binding:
            raise HTTPException(status_code=404, detail="绑定不存在")

        db.delete(binding)
        db.commit()

        logger.info(f"用户 {user.username} 解除数据绑定: {binding_id}")
        return {"message": "数据绑定已解除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解除绑定失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"解除绑定失败: {str(e)}")
