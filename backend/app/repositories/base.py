"""
基础仓储类

定义所有 Repository 的通用接口和功能
"""
from typing import TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func
import uuid
import logging

logger = logging.getLogger(__name__)

# 泛型类型：模型类
T = TypeVar('T')


class BaseRepository:
    """
    基础仓储类

    提供通用的 CRUD 操作，所有具体 Repository 继承此类
    """

    def __init__(self, session: Session, model: Type[T]):
        """
        初始化 Repository

        Args:
            session: SQLAlchemy 数据库会话
            model: SQLAlchemy 模型类
        """
        self.session = session
        self.model = model

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        根据 ID 获取实体

        Args:
            entity_id: 实体 ID 字符串

        Returns:
            实体对象，不存在返回 None
        """
        try:
            eid = uuid.UUID(entity_id)
        except ValueError:
            logger.warning(f"无效的ID格式: {entity_id}")
            return None

        return self.session.query(self.model).filter(self.model.id == eid).first()

    def get_by_id_or_raise(self, entity_id: str, entity_name: str = "实体") -> T:
        """
        根据 ID 获取实体，不存在则抛出异常

        Args:
            entity_id: 实体 ID 字符串
            entity_name: 实体名称（用于错误消息）

        Returns:
            实体对象

        Raises:
            ValueError: ID 格式无效或实体不存在
        """
        try:
            eid = uuid.UUID(entity_id)
        except ValueError:
            raise ValueError(f"无效的{entity_name}ID格式: {entity_id}")

        entity = self.session.query(self.model).filter(self.model.id == eid).first()
        if not entity:
            raise ValueError(f"{entity_name}不存在: {entity_id}")

        return entity

    def list_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[Any] = None
    ) -> List[T]:
        """
        获取所有实体列表

        Args:
            limit: 限制返回数量
            offset: 偏移量
            order_by: 排序字段

        Returns:
            实体列表
        """
        query = self.session.query(self.model)

        if order_by is not None:
            query = query.order_by(order_by)

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def filter(self, **kwargs) -> List[T]:
        """
        根据条件过滤实体

        Args:
            **kwargs: 过滤条件

        Returns:
            符合条件的实体列表
        """
        query = self.session.query(self.model)

        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.all()

    def filter_one(self, **kwargs) -> Optional[T]:
        """
        根据条件获取单个实体

        Args:
            **kwargs: 过滤条件

        Returns:
            符合条件的实体，不存在返回 None
        """
        query = self.session.query(self.model)

        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.first()

    def create(self, **kwargs) -> T:
        """
        创建新实体

        Args:
            **kwargs: 实体属性

        Returns:
            创建的实体对象
        """
        entity = self.model(**kwargs)
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity_id: str, **kwargs) -> Optional[T]:
        """
        更新实体

        Args:
            entity_id: 实体 ID
            **kwargs: 更新的属性

        Returns:
            更新后的实体对象，不存在返回 None
        """
        entity = self.get_by_id(entity_id)
        if not entity:
            return None

        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity_id: str) -> bool:
        """
        删除实体

        Args:
            entity_id: 实体 ID

        Returns:
            是否删除成功
        """
        entity = self.get_by_id(entity_id)
        if not entity:
            return False

        self.session.delete(entity)
        self.session.commit()
        return True

    def count(self, **kwargs) -> int:
        """
        统计实体数量

        Args:
            **kwargs: 过滤条件

        Returns:
            符合条件的实体数量
        """
        query = self.session.query(func.count(self.model.id))

        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.scalar() or 0

    def exists(self, **kwargs) -> bool:
        """
        检查实体是否存在

        Args:
            **kwargs: 过滤条件

        Returns:
            是否存在符合条件的实体
        """
        return self.count(**kwargs) > 0

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """
        批量创建实体

        Args:
            items: 实体属性字典列表

        Returns:
            创建的实体列表
        """
        entities = [self.model(**item) for item in items]
        self.session.add_all(entities)
        self.session.commit()

        for entity in entities:
            self.session.refresh(entity)

        return entities

    def get_in(self, field_name: str, values: List[Any]) -> List[T]:
        """
        根据字段值列表获取实体

        Args:
            field_name: 字段名
            values: 字段值列表

        Returns:
            符合条件的实体列表
        """
        if not hasattr(self.model, field_name):
            logger.warning(f"模型没有字段: {field_name}")
            return []

        field = getattr(self.model, field_name)
        return self.session.query(self.model).filter(field.in_(values)).all()
