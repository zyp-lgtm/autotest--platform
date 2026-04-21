"""
智能数据提取器 - 从录制操作中提取测试数据模式
"""
import uuid
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse, parse_qs

from app.services.recorder import CapturedAction


@dataclass
class DataPattern:
    """数据模式"""
    id: str
    field_name: str
    pattern_type: str  # "input", "url", "assertion"
    values: List[Any]
    confidence: float
    selected: bool = True
    suggested_variations: List[Any] = field(default_factory=list)


class DataExtractor:
    """数据提取器 - 智能识别可变数据模式"""

    def __init__(self):
        # 可变数据的识别模式
        self.patterns = {
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "phone_cn": r'^1[3-9]\d{9}$',
            "phone_general": r'^\d{10,15}$',
            "username": r'^[a-zA-Z0-9_]{4,20}$',
            "password": r'^.{6,20}$',
            "id_card": r'^\d{15,18}$',
            "date": r'^\d{4}-\d{2}-\d{2}$',
            "url": r'^https?://[^\s]+$',
            "number": r'^\d+$'
        }

    def extract_patterns(self, actions: List[CapturedAction]) -> List[DataPattern]:
        """从操作序列中提取数据模式"""

        patterns = []

        # 1. 分析输入操作
        input_actions = [a for a in actions if a.action_type == "input"]
        for idx, action in enumerate(input_actions):
            if action.value and self._is_variable_data(action.value):
                field_name = self._guess_field_name(action, idx, patterns)
                variations = self._generate_variations(action.value)

                patterns.append(DataPattern(
                    id=str(uuid.uuid4()),
                    field_name=field_name,
                    pattern_type="input",
                    values=[action.value],
                    confidence=self._calculate_confidence(action),
                    selected=True,
                    suggested_variations=variations
                ))

        # 2. 分析URL参数
        nav_actions = [a for a in actions if a.action_type == "navigate"]
        for action in nav_actions:
            url_params = self._extract_url_params(action.page_url)
            for param_name, param_value in url_params.items():
                if self._is_variable_data(str(param_value)):
                    patterns.append(DataPattern(
                        id=str(uuid.uuid4()),
                        field_name=param_name,
                        pattern_type="url",
                        values=[param_value],
                        confidence=0.9,
                        selected=True
                    ))

        # 3. 分析验证点（断言数据）
        for action in actions:
            if action.action_type == "input" and action.value:
                # 输入值可以作为断言的期望值
                patterns.append(DataPattern(
                    id=str(uuid.uuid4()),
                    field_name=f"assert_{self._guess_field_name(action, 0, [])}",
                    pattern_type="assertion",
                    values=[action.value],
                    confidence=0.7,
                    selected=False  # 断言数据默认不选中
                ))

        return self._merge_similar_patterns(patterns)

    def _is_variable_data(self, value: str) -> bool:
        """判断是否为可变数据"""
        if not value or len(value) > 100:  # 过长或空值
            return False

        # 检查是否匹配可变数据模式
        for pattern_name, pattern in self.patterns.items():
            if re.match(pattern, value):
                return True

        # 短文本可能是用户输入
        if 1 < len(value) < 30 and not value.isspace():
            return True

        return False

    def _guess_field_name(
        self,
        action: CapturedAction,
        index: int,
        existing_patterns: List[DataPattern]
    ) -> str:
        """根据上下文猜测字段名"""

        # 从元素信息中提取线索
        element_text = (action.element_text or "").lower()
        selector = action.selector.lower()

        # 常见字段名映射
        field_mapping = {
            # 用户相关
            "user": "username",
            "用户": "username",
            "email": "email",
            "邮箱": "email",
            "mail": "email",
            "password": "password",
            "密码": "password",
            "pass": "password",
            "pwd": "password",
            "phone": "phone",
            "电话": "phone",
            "tel": "phone",
            "mobile": "phone",

            # 通用字段
            "name": "name",
            "名称": "name",
            "title": "title",
            "标题": "title",
            "content": "content",
            "内容": "content",
            "value": "value",
            "数值": "value",
            "id": "id",
            "标识": "id"
        }

        # 检查元素文本
        for keyword, field_name in field_mapping.items():
            if keyword in element_text or keyword in selector:
                return field_name

        # 检查选择器中的关键词
        for keyword, field_name in field_mapping.items():
            if keyword in selector:
                return field_name

        # 根据索引生成默认字段名
        index_counter = 1
        for pattern in existing_patterns:
            if pattern.field_name.startswith("field_"):
                index_counter += 1

        return f"field_{index_counter}"

    def _generate_variations(self, value: str) -> List[Any]:
        """生成数据变体（用于测试数据）"""

        variations = [value]

        # 根据数据类型生成边界值和特殊值
        if "@" in value:  # 邮箱
            variations.extend([
                "test@example.com",
                "invalid@email",
                "",
                "a" * 100  # 超长邮箱
            ])

        elif re.match(r'^1[3-9]\d{9}$', value):  # 手机号
            variations.extend([
                "13800138000",  # 有效号码
                "12345678901",  # 可能有效
                "12345",  # 过短
                "12345678901234567"  # 过长
            ])

        elif re.match(r'^[a-zA-Z0-9_]{4,16}$', value):  # 用户名
            variations.extend([
                value + "_test",
                "admin",
                "test_user",
                "",
                "a" * 20  # 过长
            ])

        elif len(value) < 20:  # 短文本
            variations.extend([
                value + "_边界值",
                "",
                "特殊字符!@#$%",
                value.upper() if value.islower() else value.lower()
            ])

        return variations

    def _extract_url_params(self, url: str) -> Dict[str, str]:
        """提取URL参数"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)

            # 将参数从列表转换为单个值
            return {
                key: values[0] if len(values) == 1 else values
                for key, values in params.items()
            }
        except Exception:
            return {}

    def _calculate_confidence(self, action: CapturedAction) -> float:
        """计算数据模式的置信度"""

        confidence = 0.5

        # 如果有明确的元素文本，提高置信度
        if action.element_text:
            confidence += 0.2

        # 如果选择器语义化，提高置信度
        if any(keyword in action.selector.lower()
               for keyword in ["user", "email", "password", "phone", "name"]):
            confidence += 0.2

        # 如果值符合常见模式，提高置信度
        if any(re.match(pattern, action.value or "")
               for pattern in self.patterns.values()):
            confidence += 0.1

        return min(confidence, 1.0)

    def _merge_similar_patterns(
        self,
        patterns: List[DataPattern]
    ) -> List[DataPattern]:
        """合并相似的数据模式"""

        if not patterns:
            return []

        # 简单的合并策略：按字段名分组
        merged = {}
        for pattern in patterns:
            field_name = pattern.field_name

            if field_name not in merged:
                merged[field_name] = pattern
            else:
                # 合并值
                existing = merged[field_name]
                existing.values.extend(pattern.values)
                existing.values = list(set(existing.values))  # 去重

        return list(merged.values())

    def generate_test_data(
        self,
        patterns: List[DataPattern],
        scenario_name: str,
        project_id: str
    ) -> Dict[str, Any]:
        """从数据模式生成测试数据"""

        # 选择的模式
        selected_patterns = [p for p in patterns if p.selected]

        if not selected_patterns:
            return {}

        # 生成基础数据集（原始值）
        base_row = {}
        for pattern in selected_patterns:
            if pattern.values:
                base_row[pattern.field_name] = pattern.values[0]

        # 生成变体数据集
        data_sets = [base_row]

        # 为每个模式生成变体
        for pattern in selected_patterns[:3]:  # 限制前3个模式，避免过多变体
            if pattern.suggested_variations:
                for variation in pattern.suggested_variations[:2]:  # 每个模式2个变体
                    variant_row = base_row.copy()
                    variant_row[pattern.field_name] = variation
                    data_sets.append(variant_row)

        return {
            "name": f"{scenario_name}_测试数据",
            "description": "从录制中自动提取",
            "data_type": "json",
            "data": data_sets,
            "tags": ["auto-generated", "recorded"],
            "project_id": project_id
        }


# 全局数据提取器实例
data_extractor = DataExtractor()