"""
变量解析器

负责解析和替换步骤参数中的变量引用
支持测试数据绑定和变量替换功能
"""

import re
import logging
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..models.ui_task import UICase
from ..models.test_data import TestData, DataBinding

logger = logging.getLogger(__name__)


class VariableResolver:
    """变量解析器 - 处理测试变量和数据绑定"""

    def __init__(self, db: Session):
        """
        初始化变量解析器

        Args:
            db: 数据库会话
        """
        self.db = db
        # 变量引用正则：${variable_name}
        self.var_pattern = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    def resolve_case_variables(
        self, case: UICase, data_row_index: int = 0
    ) -> Dict[str, Any]:
        """
        解析用例的所有变量

        Args:
            case: 测试用例
            data_row_index: 测试数据行索引（默认0，表示第一行数据）

        Returns:
            变量名字典：{"username": "admin", "password": "123456"}
        """
        variables = {}

        try:
            logger.info(f"🔍 [VAR_RESOLVE] 开始解析用例变量，case_id: {case.id}")

            # 1. 获取用例绑定的测试数据
            # 🔥 SQLite 中 UUID 存储为字符串（无横线），需要转换 case.id 为字符串进行比较
            case_id_str = str(case.id).replace("-", "") if case.id else case.id

            logger.info(f"🔍 [VAR_RESOLVE] 转换后的 case_id_str: {case_id_str}")

            # 先查询所有绑定的测试数据（不带过滤条件，诊断用）
            all_bindings = self.db.query(DataBinding).all()
            logger.info(f"🔍 [VAR_RESOLVE] 数据库中共有 {len(all_bindings)} 个数据绑定")
            for b in all_bindings:
                logger.info(
                    f"🔍 [VAR_RESOLVE] 绑定记录: case_id={b.case_id}(类型:{type(b.case_id)}), data_id={b.data_id}, enabled={b.enabled}"
                )

            bindings = (
                self.db.query(DataBinding)
                .filter(DataBinding.case_id == case_id_str, DataBinding.enabled == 1)
                .all()
            )

            logger.info(f"🔍 [VAR_RESOLVE] 找到 {len(bindings)} 个匹配的数据绑定")

            if bindings:
                # 用例级数据绑定（优先级最高）
                logger.info(f"✅ 找到 {len(bindings)} 个数据绑定")
                for binding in bindings:
                    # 🔥 将字符串格式的 data_id 转换为 UUID 对象进行查询
                    # DataBinding.data_id 是 String(36)，但 TestData.id 是 UUID 类型
                    try:
                        data_id_uuid = uuid.UUID(binding.data_id)
                    except (ValueError, AttributeError) as e:
                        logger.error(
                            f"无效的 data_id 格式: {binding.data_id}, 错误: {e}"
                        )
                        continue

                    test_data = (
                        self.db.query(TestData)
                        .filter(TestData.id == data_id_uuid)
                        .first()
                    )

                    if not test_data:
                        logger.warning(f"测试数据 {binding.data_id} 不存在")
                        continue

                    logger.info(f"✅ 找到测试数据: {test_data.name}")
                    self._extract_variables_from_test_data(
                        test_data, data_row_index, variables
                    )
            else:
                # 场景级 fallback：查找场景关联的 TestData
                logger.info(
                    f"用例 {case.name} (ID: {case.id}) 没有用例级数据绑定，"
                    f"尝试场景级数据 (scenario_id={case.scenario_id})"
                )
                test_data = (
                    self.db.query(TestData)
                    .filter(TestData.scenario_id == case.scenario_id)
                    .first()
                )

                if not test_data:
                    logger.info(f"场景 {case.scenario_id} 也没有场景级测试数据")
                    return variables

                logger.info(f"✅ 找到场景级测试数据: {test_data.name}")
                self._extract_variables_from_test_data(
                    test_data, data_row_index, variables
                )

        except Exception as e:
            logger.error(f"解析变量失败: {e}", exc_info=True)

        return variables

    def _extract_variables_from_test_data(
        self, test_data: TestData, data_row_index: int, variables: Dict[str, Any]
    ) -> None:
        """
        从 TestData 中提取指定行的数据到变量字典

        Args:
            test_data: 测试数据对象
            data_row_index: 数据行索引
            variables: 变量字典（原地修改）
        """
        logger.info(
            f"🔍 [VAR_RESOLVE] 从测试数据提取变量: test_data.id={test_data.id}, test_data.name={test_data.name}"
        )

        data_rows = test_data.data
        logger.info(
            f"🔍 [VAR_RESOLVE] 测试数据内容: {data_rows}, 类型: {type(data_rows)}"
        )

        if not isinstance(data_rows, list) or len(data_rows) == 0:
            logger.warning(f"测试数据 {test_data.name} 为空")
            return

        # 确保索引有效
        idx = min(data_row_index, len(data_rows) - 1)
        data_row = data_rows[idx]

        logger.info(
            f"🔍 [VAR_RESOLVE] 选择数据行 {idx}: {data_row}, 类型: {type(data_row)}"
        )

        # 将数据行中的字段提取为变量
        if isinstance(data_row, dict):
            variables.update(data_row)
            logger.info(
                f"✅ 从测试数据 {test_data.name} 加载变量: "
                f"{list(data_row.keys())} = {data_row}"
            )
            logger.info(f"🔍 [VAR_RESOLVE] 当前变量字典: {variables}")
        else:
            logger.warning(f"数据行格式错误，期望字典，实际: {type(data_row)}")

    def replace_variables(
        self, parameters: Dict[str, Any], variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        替换参数中的变量引用

        Args:
            parameters: 原始参数（可能包含 ${variable}）
            variables: 变量字典

        Returns:
            替换后的参数

        Examples:
            >>> parameters = {"text": "${username}"}
            >>> variables = {"username": "admin"}
            >>> replace_variables(parameters, variables)
            {"text": "admin"}
        """
        if not parameters:
            return {}

        logger.info(f"🔄 变量替换: 参数={parameters}, 可用变量={variables}")

        result = {}

        for key, value in parameters.items():
            # 跳过内部字段（以下划线开头）
            if key.startswith("_"):
                result[key] = value
                continue

            # 处理字符串值
            if isinstance(value, str):
                replaced = self._replace_string(value, variables)
                if replaced != value:
                    logger.info(f"  ✅ {key}: {value} → {replaced}")
                result[key] = replaced
            # 处理嵌套字典
            elif isinstance(value, dict):
                result[key] = self.replace_variables(value, variables)
            # 处理列表
            elif isinstance(value, list):
                result[key] = [
                    (
                        self._replace_string(item, variables)
                        if isinstance(item, str)
                        else item
                    )
                    for item in value
                ]
            else:
                # 其他类型直接保留
                result[key] = value

        return result

    def _replace_string(self, text: str, variables: Dict[str, Any]) -> str:
        """
        替换字符串中的变量引用

        Args:
            text: 原始字符串
            variables: 变量字典

        Returns:
            替换后的字符串
        """

        def replacer(match):
            var_name = match.group(1)
            if var_name in variables:
                return str(variables[var_name])
            # 如果变量不存在，保持原样
            logger.warning(f"变量 ${{{var_name}}} 未定义，保持原样")
            return match.group(0)

        return self.var_pattern.sub(replacer, text)

    def get_all_variables(
        self, case: UICase, data_row_index: int = 0
    ) -> Dict[str, Any]:
        """
        获取用例的所有变量（便捷方法）

        Args:
            case: 测试用例
            data_row_index: 数据行索引

        Returns:
            变量字典
        """
        return self.resolve_case_variables(case, data_row_index)

    def resolve_step_parameters(
        self, step_parameters: Dict[str, Any], case: UICase, data_row_index: int = 0
    ) -> Dict[str, Any]:
        """
        解析步骤参数（一站式服务）

        Args:
            step_parameters: 步骤参数
            case: 测试用例
            data_row_index: 数据行索引

        Returns:
            解析后的参数
        """
        # 1. 解析变量
        variables = self.resolve_case_variables(case, data_row_index)

        # 2. 替换参数中的变量引用
        resolved_params = self.replace_variables(step_parameters, variables)

        logger.info(f"参数解析: 原始={step_parameters}, 解析后={resolved_params}")

        return resolved_params


# 全局实例工厂
def create_variable_resolver(db: Session) -> VariableResolver:
    """创建变量解析器实例"""
    return VariableResolver(db)
