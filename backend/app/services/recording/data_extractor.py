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
            "number": r'^\d+$',
            "zip_code": r'^\d{5,6}$',
            "qq": r'^[1-9]\d{4,10}$',
            "wechat": r'^[a-zA-Z]{1}[a-zA-Z0-9_\-]{5,19}$'
        }

        # 🔥 新增：增强的字段名映射表（支持电商等更多场景）
        self.field_mapping = {
            # ==== 用户认证 ====
            "user": "username",
            "用户": "username",
            "username": "username",
            "account": "username",
            "账号": "username",

            "email": "email",
            "邮箱": "email",
            "mail": "email",
            "邮件": "email",
            "e-mail": "email",

            "password": "password",
            "密码": "password",
            "pass": "password",
            "pwd": "password",
            "passwd": "password",

            # ==== 联系方式 ====
            "phone": "phone",
            "电话": "phone",
            "tel": "phone",
            "mobile": "phone",
            "手机": "phone",
            "联系电话": "phone",
            "手机号": "phone",

            # ==== 个人信息 ====
            "name": "name",
            "名称": "name",
            "fullname": "name",
            "姓名": "name",
            "realname": "name",
            "真实姓名": "name",

            "address": "address",
            "地址": "address",
            "location": "address",
            "位置": "address",

            "idcard": "id_card",
            "id_card": "id_card",
            "身份证": "id_card",
            "证件号": "id_card",

            # ==== 电商相关（新增） ====
            "product": "product_name",
            "商品": "product_name",
            "product_name": "product_name",
            "商品名称": "product_name",
            "item": "product_name",
            "货物": "product_name",

            "price": "price",
            "价格": "price",
            "金额": "price",
            "单价": "price",
            "售价": "price",

            "quantity": "quantity",
            "qty": "quantity",
            "数量": "quantity",
            "库存": "quantity",
            "件数": "quantity",

            "sku": "sku",
            "SKU": "sku",
            "商品编码": "sku",

            "category": "category",
            "分类": "category",
            "品类": "category",

            # ==== 订单相关 ====
            "order": "order_id",
            "订单": "order_id",
            "order_id": "order_id",
            "订单号": "order_id",
            "orderno": "order_id",

            "payment": "payment_method",
            "支付": "payment_method",
            "payment_method": "payment_method",
            "支付方式": "payment_method",

            # ==== 搜索相关 ====
            "search": "search_keyword",
            "搜索": "search_keyword",
            "keyword": "search_keyword",
            "关键词": "search_keyword",
            "query": "search_keyword",

            # ==== 内容相关 ====
            "title": "title",
            "标题": "title",
            "subject": "title",
            "主题": "title",

            "content": "content",
            "内容": "content",
            "description": "content",
            "描述": "content",
            "remark": "content",
            "备注": "content",

            "comment": "comment",
            "评论": "comment",
            "评价": "comment",
            "反馈": "comment",

            # ==== 其他通用字段 ====
            "value": "value",
            "数值": "value",
            "text": "text",
            "文本": "text",
            "id": "id",
            "标识": "id",
            "code": "code",
            "编码": "code",
            "编号": "code"
        }

    def extract_patterns(self, actions: List[CapturedAction]) -> List[DataPattern]:
        """从操作序列中提取数据模式（增强版）"""

        patterns = []

        # 🔥 步骤1: 分析输入操作（主要数据源）
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

        # 🔥 步骤2: 分析URL参数
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

        # 🔥 步骤3: 分析选择操作（select 标签）
        select_actions = [a for a in actions if a.action_type == "select"]
        for action in select_actions:
            if action.value:
                field_name = self._guess_field_name(action, 0, patterns)
                patterns.append(DataPattern(
                    id=str(uuid.uuid4()),
                    field_name=f"{field_name}_selection",
                    pattern_type="select",
                    values=[action.value],
                    confidence=0.85,
                    selected=True
                ))

        # 🔥 步骤4: 注释掉断言生成（默认不生成，避免噪音）
        # 用户可以后续手动添加断言
        # for action in actions:
        #     if action.action_type == "input" and action.value:
        #         patterns.append(DataPattern(
        #             id=str(uuid.uuid4()),
        #             field_name=f"assert_{self._guess_field_name(action, 0, [])}",
        #             pattern_type="assertion",
        #             values=[action.value],
        #             confidence=0.7,
        #             selected=False
        #         ))

        return self._merge_similar_patterns(patterns)

    def group_related_fields(self, patterns: List[DataPattern]) -> Dict[str, List[DataPattern]]:
        """将相关字段分组（用于生成测试数据）"""

        groups = {
            "user_info": [],      # 用户信息组
            "contact": [],        # 联系方式组
            "product": [],        # 商品相关组
            "order": [],          # 订单相关组
            "other": []           # 其他组
        }

        user_info_keywords = ["username", "password", "name", "realname", "id_card"]
        contact_keywords = ["phone", "email", "mobile", "tel", "mail"]
        product_keywords = ["product", "sku", "price", "quantity", "category"]
        order_keywords = ["order", "payment", "address"]

        for pattern in patterns:
            field_name = pattern.field_name.lower()

            if any(keyword in field_name for keyword in user_info_keywords):
                groups["user_info"].append(pattern)
            elif any(keyword in field_name for keyword in contact_keywords):
                groups["contact"].append(pattern)
            elif any(keyword in field_name for keyword in product_keywords):
                groups["product"].append(pattern)
            elif any(keyword in field_name for keyword in order_keywords):
                groups["order"].append(pattern)
            else:
                groups["other"].append(pattern)

        # 移除空组
        return {k: v for k, v in groups.items() if v}

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
        """根据上下文猜测字段名（增强版）"""

        # 从元素信息中提取线索
        element_text = (action.element_text or "").lower()
        selector = action.selector.lower()
        element_attributes = action.element_attributes or {}

        # 🔥 优先级1: 检查 HTML 属性（name, id, placeholder 等）
        for attr_name in ['name', 'id', 'placeholder', 'aria-label', 'data-field']:
            attr_value = str(element_attributes.get(attr_name, '')).lower()
            if attr_value:
                for keyword, field_name in self.field_mapping.items():
                    if keyword in attr_value:
                        return field_name

        # 🔥 优先级2: 检查元素文本（label、相邻文本）
        for keyword, field_name in self.field_mapping.items():
            if keyword in element_text:
                return field_name

        # 🔥 优先级3: 检查选择器
        for keyword, field_name in self.field_mapping.items():
            if keyword in selector:
                return field_name

        # 🔥 优先级4: 根据输入值类型推断
        if action.value:
            value_type = self._infer_value_type(action.value)
            if value_type:
                return value_type

        # 生成语义化的默认字段名
        return self._generate_semantic_field_name(existing_patterns)

    def _infer_value_type(self, value: str) -> Optional[str]:
        """根据值推断字段类型"""
        if not value:
            return None

        # 邮箱
        if re.match(self.patterns["email"], value):
            return "email"

        # 手机号
        if re.match(self.patterns["phone_cn"], value):
            return "phone"

        # 日期
        if re.match(self.patterns["date"], value):
            return "date"

        # URL
        if re.match(self.patterns["url"], value):
            return "url"

        # QQ号
        if re.match(self.patterns["qq"], value):
            return "qq"

        # 数字（可能是ID、数量、价格等）
        if re.match(self.patterns["number"], value):
            if len(value) >= 10:  # 可能是ID
                return "id"
            elif len(value) <= 5:  # 可能是数量
                return "quantity"
            else:  # 可能是价格
                return "price"

        return None

    def _generate_semantic_field_name(self, existing_patterns: List[DataPattern]) -> str:
        """生成语义化的字段名"""
        # 计算现有 field_* 类型的字段数量
        field_count = sum(1 for p in existing_patterns if p.field_name.startswith("field_"))

        # 使用更有意义的命名
        semantic_names = [
            "input_text", "user_input", "form_field", "data_value",
            "text_field", "input_value", "field_data"
        ]

        # 尝试使用语义化名称
        for name in semantic_names:
            if not any(p.field_name == name for p in existing_patterns):
                return name

        # 如果都被占用，使用带编号的名称
        return f"field_{field_count + 1}"

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
        """计算数据模式的置信度（增强版）"""

        confidence = 0.3  # 基础置信度

        # 🔥 因素1: 元素属性（name, id, placeholder 等）
        element_attributes = action.element_attributes or {}
        for attr_name in ['name', 'id', 'placeholder', 'aria-label']:
            attr_value = str(element_attributes.get(attr_name, '')).lower()
            if attr_value:
                # 检查是否包含明确的字段关键词
                if any(keyword in attr_value for keyword in self.field_mapping.keys()):
                    confidence += 0.25
                    break

        # 🔥 因素2: 元素文本（label 文本）
        if action.element_text:
            element_text_lower = action.element_text.lower()
            # 检查是否包含明确的字段指示
            if any(keyword in element_text_lower for keyword in
                   ["用户", "邮箱", "密码", "手机", "姓名", "地址", "商品", "订单"]):
                confidence += 0.2

        # 🔥 因素3: 选择器语义化程度
        selector_lower = action.selector.lower()
        semantic_indicators = [
            "name=", "id=", "placeholder=",  # 有属性
            "input", "textarea", "select",  # 表单元素
            "user", "email", "password", "phone", "login", "search"
        ]
        if any(indicator in selector_lower for indicator in semantic_indicators):
            confidence += 0.15

        # 🔥 因素4: 值的模式匹配
        if action.value:
            # 检查是否符合某个已知模式
            for pattern_name, pattern in self.patterns.items():
                if re.match(pattern, action.value):
                    confidence += 0.15
                    break

            # 值的长度合理性（不是太长也不是太短）
            value_length = len(action.value or "")
            if 3 <= value_length <= 50:
                confidence += 0.05

        # 🔥 因素5: 元素标签类型
        if action.element_tag:
            if action.element_tag in ["input", "textarea", "select"]:
                confidence += 0.1

        # 🔥 因素6: 上下文一致性（如果前面有相似的字段，提高置信度）
        # 这个因素需要在 extract_patterns 层面处理，这里暂时标记

        return min(confidence, 1.0)

    def _merge_similar_patterns(
        self,
        patterns: List[DataPattern]
    ) -> List[DataPattern]:
        """合并相似的数据模式（增强版）"""

        if not patterns:
            return []

        # 🔥 策略1: 按字段名精确分组
        merged_by_name = {}
        for pattern in patterns:
            field_name = pattern.field_name

            if field_name not in merged_by_name:
                merged_by_name[field_name] = {
                    "pattern": pattern,
                    "values": [],
                    "confidences": []
                }

            # 收集值和置信度
            merged_by_name[field_name]["values"].extend(pattern.values)
            merged_by_name[field_name]["confidences"].append(pattern.confidence)

        # 🔥 策略2: 处理每个分组的合并
        result = []
        for field_name, group in merged_by_name.items():
            base_pattern = group["pattern"]

            # 去重值
            unique_values = list(set(group["values"]))

            # 计算平均置信度
            avg_confidence = sum(group["confidences"]) / len(group["confidences"])

            # 如果有多个值，说明这个字段被多次输入，提高置信度
            if len(unique_values) > 1:
                avg_confidence = min(avg_confidence + 0.1, 1.0)

            # 创建合并后的模式
            merged_pattern = DataPattern(
                id=base_pattern.id,
                field_name=field_name,
                pattern_type=base_pattern.pattern_type,
                values=unique_values,
                confidence=round(avg_confidence, 2),
                selected=base_pattern.selected,
                suggested_variations=base_pattern.suggested_variations
            )

            result.append(merged_pattern)

        # 🔥 策略3: 按置信度排序，高置信度的在前
        result.sort(key=lambda p: p.confidence, reverse=True)

        return result

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

        # 只保留基准行，不生成变体
        data_sets = [base_row]

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