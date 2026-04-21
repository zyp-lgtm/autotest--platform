"""
批量操作 API

提供批量操作功能以提高测试管理效率
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..models.ui_task import UIScenario
from ..models.user import User
from ..core.database import get_db
from ..core.security import get_authenticated_user
from .utils import validate_uuid, serialize_model
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batch", tags=["批量操作"])


@router.post("/scenarios/enable")
async def batch_enable_scenarios(
    scenario_ids: List[str],
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """批量启用场景"""
    try:
        if not scenario_ids:
            raise HTTPException(status_code=400, detail="场景ID列表不能为空")

        enabled_count = 0
        not_found_count = 0

        for scenario_id in scenario_ids:
            try:
                # 验证UUID格式
                validate_uuid(scenario_id, "场景")

                # 查找场景
                scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()

                if scenario:
                    scenario.enabled = True
                    enabled_count += 1
                else:
                    not_found_count += 1

            except Exception as e:
                logger.warning(f"启用场景 {scenario_id} 失败: {e}")
                not_found_count += 1

        db.commit()

        logger.info(f"用户 {user.username} 批量启用场景: 成功 {enabled_count} 个，失败 {not_found_count} 个")

        return {
            "message": f"已启用 {enabled_count} 个场景",
            "total_requested": len(scenario_ids),
            "enabled_count": enabled_count,
            "not_found_count": not_found_count,
            "success": enabled_count > 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量启用场景失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量启用场景失败: {str(e)}")


@router.post("/scenarios/disable")
async def batch_disable_scenarios(
    scenario_ids: List[str],
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """批量禁用场景"""
    try:
        if not scenario_ids:
            raise HTTPException(status_code=400, detail="场景ID列表不能为空")

        disabled_count = 0
        not_found_count = 0

        for scenario_id in scenario_ids:
            try:
                validate_uuid(scenario_id, "场景")

                scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()

                if scenario:
                    scenario.enabled = False
                    disabled_count += 1
                else:
                    not_found_count += 1

            except Exception as e:
                logger.warning(f"禁用场景 {scenario_id} 失败: {e}")
                not_found_count += 1

        db.commit()

        logger.info(f"用户 {user.username} 批量禁用场景: 成功 {disabled_count} 个，失败 {not_found_count} 个")

        return {
            "message": f"已禁用 {disabled_count} 个场景",
            "total_requested": len(scenario_ids),
            "disabled_count": disabled_count,
            "not_found_count": not_found_count,
            "success": disabled_count > 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量禁用场景失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量禁用场景失败: {str(e)}")


@router.post("/scenarios/delete")
async def batch_delete_scenarios(
    scenario_ids: List[str],
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """批量删除场景"""
    try:
        if not scenario_ids:
            raise HTTPException(status_code=400, detail="场景ID列表不能为空")

        deleted_count = 0
        not_found_count = 0

        for scenario_id in scenario_ids:
            try:
                validate_uuid(scenario_id, "场景")

                scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()

                if scenario:
                    # 检查是否有关联的测试用例
                    from ..models.ui_task import UICase
                    case_count = db.query(UICase).filter(UICase.scenario_id == scenario_id).count()

                    if case_count > 0:
                        logger.warning(f"场景 {scenario.name} 有 {case_count} 个用例，跳过删除")
                        continue

                    scenario_name = scenario.name
                    db.delete(scenario)
                    deleted_count += 1
                else:
                    not_found_count += 1

            except Exception as e:
                logger.warning(f"删除场景 {scenario_id} 失败: {e}")
                not_found_count += 1

        db.commit()

        logger.info(f"用户 {user.username} 批量删除场景: 成功 {deleted_count} 个，失败 {not_found_count} 个")

        return {
            "message": f"已删除 {deleted_count} 个场景",
            "total_requested": len(scenario_ids),
            "deleted_count": deleted_count,
            "not_found_count": not_found_count,
            "skipped_count": len(scenario_ids) - deleted_count - not_found_count,
            "success": deleted_count > 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除场景失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除场景失败: {str(e)}")


@router.post("/scenarios/export")
async def batch_export_scenarios(
    scenario_ids: List[str],
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """批量导出场景数据"""
    try:
        if not scenario_ids:
            raise HTTPException(status_code=400, detail="场景ID列表不能为空")

        exported_scenarios = []
        not_found_count = 0

        for scenario_id in scenario_ids:
            try:
                validate_uuid(scenario_id, "场景")

                scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()

                if scenario:
                    # 获取场景的测试用例
                    from ..models.ui_task import UICase, UIStep
                    cases = db.query(UICase).filter(UICase.scenario_id == scenario_id).all()

                    scenario_data = {
                        "id": str(scenario.id),
                        "name": scenario.name,
                        "description": scenario.description,
                        "enabled": scenario.enabled,
                        "cases": []
                    }

                    for case in cases:
                        # 获取用例的测试步骤
                        steps = db.query(UIStep).filter(UIStep.case_id == case.id).all()

                        case_data = {
                            "id": str(case.id),
                            "name": case.name,
                            "description": case.description,
                            "enabled": case.enabled,
                            "steps": []
                        }

                        for step in steps:
                            step_data = {
                                "id": str(step.id),
                                "step_name": step.step_name,
                                "keyword_id": str(step.keyword_id),
                                "parameters": step.parameters,
                                "continue_on_failure": step.continue_on_failure
                            }
                            case_data["steps"].append(step_data)

                        scenario_data["cases"].append(case_data)

                    exported_scenarios.append(scenario_data)
                else:
                    not_found_count += 1

            except Exception as e:
                logger.warning(f"导出场景 {scenario_id} 失败: {e}")
                not_found_count += 1

        logger.info(f"用户 {user.username} 批量导出场景: 成功 {len(exported_scenarios)} 个，失败 {not_found_count} 个")

        return {
            "message": f"已导出 {len(exported_scenarios)} 个场景",
            "total_requested": len(scenario_ids),
            "exported_count": len(exported_scenarios),
            "not_found_count": not_found_count,
            "data": exported_scenarios,
            "success": len(exported_scenarios) > 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导出场景失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量导出场景失败: {str(e)}")


@router.post("/tasks/delete")
async def batch_delete_tasks(
    task_ids: List[str],
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """批量删除任务"""
    try:
        if not task_ids:
            raise HTTPException(status_code=400, detail="任务ID列表不能为空")

        deleted_count = 0
        not_found_count = 0

        for task_id in task_ids:
            try:
                validate_uuid(task_id, "任务")

                from ..models.ui_task import UITask
                task = db.query(UITask).filter(UITask.id == task_id).first()

                if task:
                    # 检查权限
                    if task.owner_id != user.id:
                        logger.warning(f"用户 {user.username} 无权删除任务 {task.name}")
                        continue

                    task_name = task.name
                    db.delete(task)
                    deleted_count += 1
                else:
                    not_found_count += 1

            except Exception as e:
                logger.warning(f"删除任务 {task_id} 失败: {e}")
                not_found_count += 1

        db.commit()

        logger.info(f"用户 {user.username} 批量删除任务: 成功 {deleted_count} 个，失败 {not_found_count} 个")

        return {
            "message": f"已删除 {deleted_count} 个任务",
            "total_requested": len(task_ids),
            "deleted_count": deleted_count,
            "not_found_count": not_found_count,
            "success": deleted_count > 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除任务失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除任务失败: {str(e)}")


@router.get("/operations/preview")
async def preview_batch_operation(
    operation_type: str,
    item_ids: List[str],
    item_type: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """预览批量操作结果"""
    try:
        if not item_ids:
            raise HTTPException(status_code=400, detail="项目ID列表不能为空")

        if item_type == "scenarios":
            items = db.query(UIScenario).filter(UIScenario.id.in_(item_ids)).all()
        elif item_type == "tasks":
            from ..models.ui_task import UITask
            items = db.query(UITask).filter(UITask.id.in_(item_ids)).all()
        else:
            raise HTTPException(status_code=400, detail=f"不支持的类型: {item_type}")

        # 分析影响
        impact = {
            "total_items": len(items),
            "operation": operation_type,
            "item_type": item_type,
            "items": [],
            "warnings": [],
            "errors": []
        }

        for item in items:
            item_info = {
                "id": str(item.id),
                "name": item.name,
                "enabled": getattr(item, 'enabled', True)
            }

            # 检查依赖关系
            if item_type == "scenarios" and operation_type == "delete":
                from ..models.ui_task import UICase
                case_count = db.query(UICase).filter(UICase.scenario_id == item.id).count()
                if case_count > 0:
                    item_info["warning"] = f"该场景有 {case_count} 个测试用例，无法删除"
                    impact["warnings"].append(f"{item.name}: {case_count} 个用例")

            impact["items"].append(item_info)

        return impact

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览批量操作失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览批量操作失败: {str(e)}")
