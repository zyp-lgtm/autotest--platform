# backend/app/services/variable_resolver.py
import re
from typing import Any, Dict


class VariableResolver:
    """解析字符串中的变量引用"""

    PATTERN = r'\{([^}]+)\}'

    def resolve(self, text: str, context: Dict[str, Any]) -> str:
        """
        解析文本中的变量引用

        示例:
            resolve("{username}", {"username": "test"}) -> "test"
            resolve("{user.id}", {"user": {"id": "123"}}) -> "123"
        """
        if not isinstance(text, str):
            return text

        def replace_var(match):
            var_path = match.group(1)
            value = self._get_value(var_path, context)
            if value is None:
                return f'{{{var_path}}}'
            # 如果是字符串，直接返回；如果是其他类型，转换为字符串
            return value if isinstance(value, str) else str(value)

        return re.sub(self.PATTERN, replace_var, text)

    def _get_value(self, path: str, context: Dict[str, Any]) -> Any:
        """使用点符号从上下文获取值"""
        if '.' in path:
            parts = path.split('.')
            value = context.get(parts[0])
            for part in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        return context.get(path)