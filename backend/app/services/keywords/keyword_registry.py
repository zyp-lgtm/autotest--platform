"""
关键字注册表

提供插件化的关键字注册和管理系统，实现关键字的可扩展性。

## 设计模式

1. **注册表模式 (Registry Pattern)**: 集中管理关键字处理器
2. **策略模式 (Strategy Pattern)**: 每个关键字是一个独立的策略
3. **装饰器模式 (Decorator Pattern)**: 使用装饰器注册关键字

## 使用方式

### 1. 使用装饰器注册关键字

```python
from app.services.keywords.keyword_registry import keyword_registry

@keyword_registry.register("ui", "NAVIGATE")
async def navigate_keyword(parameters, context):
    url = parameters.get("url")
    page = context.get("page")
    await page.goto(url)
    return {"success": True, "data": {"url": url}}
```

### 2. 手动注册关键字

```python
def my_keyword_handler(parameters, context):
    return {"success": True, "data": {}}

keyword_registry.register("ui", "MY_KEYWORD")(my_keyword_handler)
```

### 3. 执行关键字

```python
result = await keyword_registry.execute(
    category="ui",
    name="NAVIGATE",
    parameters={"url": "https://example.com"},
    context={"page": page}
)
```

## 插件扩展

第三方可以创建自己的关键字插件：

```python
# my_plugin/keywords.py
from app.services.keywords.keyword_registry import keyword_registry

@keyword_registry.register("custom", "MY_ACTION")
async def my_custom_action(parameters, context):
    # 自定义逻辑
    return {"success": True}
```
"""

import logging
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class KeywordCategory(Enum):
    """关键字类别"""
    API = "api"
    UI = "ui"
    CUSTOM = "custom"  # 用户自定义关键字


@dataclass
class KeywordHandler:
    """关键字处理器元数据"""
    name: str
    category: str
    handler: Callable
    description: str = ""
    parameters_schema: Optional[Dict] = None
    author: str = ""
    version: str = "1.0.0"


class KeywordRegistry:
    """
    关键字注册表

    提供插件化的关键字注册和管理功能。
    """

    def __init__(self):
        """初始化注册表"""
        # 格式: {category: {name: KeywordHandler}}
        self._handlers: Dict[str, Dict[str, KeywordHandler]] = {
            "api": {},
            "ui": {},
            "custom": {}
        }
        # 别名映射: {alias: (category, name)}
        self._aliases: Dict[str, tuple] = {}

    def register(
        self,
        category: str,
        name: Optional[str] = None,
        description: str = "",
        parameters_schema: Optional[Dict] = None,
        author: str = "",
        version: str = "1.0.0",
        aliases: Optional[List[str]] = None
    ) -> Callable:
        """
        注册关键字处理器（装饰器）

        Args:
            category: 关键字类别（api, ui, custom）
            name: 关键字名称（如果为 None，使用函数名）
            description: 关键字描述
            parameters_schema: 参数 JSON Schema
            author: 作者
            version: 版本
            aliases: 别名列表

        Returns:
            装饰器函数

        Example:
            @keyword_registry.register("ui", "NAVIGATE", description="导航到URL")
            async def navigate_keyword(parameters, context):
                ...
        """
        def decorator(func: Callable) -> Callable:
            keyword_name = name or func.__name__

            # 创建处理器元数据
            handler = KeywordHandler(
                name=keyword_name,
                category=category,
                handler=func,
                description=description,
                parameters_schema=parameters_schema,
                author=author,
                version=version
            )

            # 注册到分类中
            if category not in self._handlers:
                self._handlers[category] = {}

            self._handlers[category][keyword_name] = handler

            # 注册别名
            if aliases:
                for alias in aliases:
                    self._aliases[alias] = (category, keyword_name)

            logger.info(f"✅ 注册关键字: {category}.{keyword_name} ({func.__name__})")
            return func

        return decorator

    def register_handler(
        self,
        category: str,
        name: str,
        handler: Callable,
        description: str = "",
        parameters_schema: Optional[Dict] = None,
        author: str = "",
        version: str = "1.0.0"
    ) -> None:
        """
        手动注册关键字处理器

        Args:
            category: 关键字类别
            name: 关键字名称
            handler: 处理函数
            description: 描述
            parameters_schema: 参数 Schema
            author: 作者
            version: 版本
        """
        keyword_handler = KeywordHandler(
            name=name,
            category=category,
            handler=handler,
            description=description,
            parameters_schema=parameters_schema,
            author=author,
            version=version
        )

        if category not in self._handlers:
            self._handlers[category] = {}

        self._handlers[category][name] = keyword_handler
        logger.info(f"✅ 注册关键字: {category}.{name}")

    def unregister(self, category: str, name: str) -> bool:
        """
        注销关键字

        Args:
            category: 关键字类别
            name: 关键字名称

        Returns:
            是否成功注销
        """
        if category in self._handlers and name in self._handlers[category]:
            del self._handlers[category][name]
            logger.info(f"❌ 注销关键字: {category}.{name}")
            return True
        return False

    async def execute(
        self,
        category: str,
        name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行关键字

        Args:
            category: 关键字类别
            name: 关键字名称
            parameters: 参数
            context: 上下文

        Returns:
            执行结果
        """
        # 检查别名
        if name in self._aliases:
            category, name = self._aliases[name]

        # 查找处理器
        if category not in self._handlers:
            return {
                "success": False,
                "error": f"未知类别: {category}"
            }

        if name not in self._handlers[category]:
            return {
                "success": False,
                "error": f"关键字不存在: {category}.{name}"
            }

        handler = self._handlers[category][name]

        try:
            # 执行处理器
            logger.info(f"执行关键字: {category}.{name}")
            result = await handler.handler(parameters, context)

            # 确保返回值格式正确
            if not isinstance(result, dict):
                return {
                    "success": False,
                    "error": f"关键字返回值必须是字典: {type(result)}"
                }

            return result

        except Exception as e:
            logger.error(f"关键字执行失败: {category}.{name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_handler(self, category: str, name: str) -> Optional[KeywordHandler]:
        """
        获取关键字处理器

        Args:
            category: 类别
            name: 名称

        Returns:
            处理器元数据，如果不存在返回 None
        """
        if category in self._handlers and name in self._handlers[category]:
            return self._handlers[category][name]
        return None

    def list_keywords(self, category: Optional[str] = None) -> List[KeywordHandler]:
        """
        列出所有关键字

        Args:
            category: 过滤类别（如果为 None，返回所有）

        Returns:
            关键字处理器列表
        """
        if category:
            if category not in self._handlers:
                return []
            return list(self._handlers[category].values())

        # 返回所有类别中的关键字
        all_handlers = []
        for category_handlers in self._handlers.values():
            all_handlers.extend(category_handlers.values())
        return all_handlers

    def get_categories(self) -> List[str]:
        """
        获取所有类别

        Returns:
            类别列表
        """
        return list(self._handlers.keys())

    def count_keywords(self, category: Optional[str] = None) -> int:
        """
        统计关键字数量

        Args:
            category: 过滤类别

        Returns:
            关键字数量
        """
        handlers = self.list_keywords(category)
        return len(handlers)

    def exists(self, category: str, name: str) -> bool:
        """
        检查关键字是否存在

        Args:
            category: 类别
            name: 名称

        Returns:
            是否存在
        """
        return self.get_handler(category, name) is not None

    def get_keyword_info(self, category: str, name: str) -> Optional[Dict]:
        """
        获取关键字信息

        Args:
            category: 类别
            name: 名称

        Returns:
            关键字信息字典
        """
        handler = self.get_handler(category, name)
        if not handler:
            return None

        return {
            "name": handler.name,
            "category": handler.category,
            "description": handler.description,
            "parameters_schema": handler.parameters_schema,
            "author": handler.author,
            "version": handler.version,
            "handler": handler.handler.__name__
        }

    def clear(self, category: Optional[str] = None) -> None:
        """
        清空注册表

        Args:
            category: 如果指定，只清空该类别
        """
        if category:
            if category in self._handlers:
                self._handlers[category].clear()
        else:
            for handlers in self._handlers.values():
                handlers.clear()
        logger.info("🗑️  清空关键字注册表")


# 全局注册表实例
keyword_registry = KeywordRegistry()


# ============================================================================
# 便捷装饰器
# ============================================================================

def register_api_keyword(
    name: Optional[str] = None,
    description: str = "",
    parameters_schema: Optional[Dict] = None,
    author: str = "",
    version: str = "1.0.0",
    aliases: Optional[List[str]] = None
) -> Callable:
    """
    注册 API 关键字装饰器

    Example:
        @register_api_keyword("API_GET", description="发送 GET 请求")
        async def api_get(parameters, context):
            ...
    """
    return keyword_registry.register(
        category="api",
        name=name,
        description=description,
        parameters_schema=parameters_schema,
        author=author,
        version=version,
        aliases=aliases
    )


def register_ui_keyword(
    name: Optional[str] = None,
    description: str = "",
    parameters_schema: Optional[Dict] = None,
    author: str = "",
    version: str = "1.0.0",
    aliases: Optional[List[str]] = None
) -> Callable:
    """
    注册 UI 关键字装饰器

    Example:
        @register_ui_keyword("CLICK", description="点击元素")
        async def click_element(parameters, context):
            ...
    """
    return keyword_registry.register(
        category="ui",
        name=name,
        description=description,
        parameters_schema=parameters_schema,
        author=author,
        version=version,
        aliases=aliases
    )


def register_custom_keyword(
    name: Optional[str] = None,
    description: str = "",
    parameters_schema: Optional[Dict] = None,
    author: str = "",
    version: str = "1.0.0",
    aliases: Optional[List[str]] = None
) -> Callable:
    """
    注册自定义关键字装饰器

    Example:
        @register_custom_keyword("MY_ACTION", description="我的自定义操作")
        async def my_action(parameters, context):
            ...
    """
    return keyword_registry.register(
        category="custom",
        name=name,
        description=description,
        parameters_schema=parameters_schema,
        author=author,
        version=version,
        aliases=aliases
    )
