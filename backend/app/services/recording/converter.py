"""
录制数据转换引擎 - 将Playwright操作转换为系统关键字
"""
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from app.services.recorder import CapturedAction


@dataclass
class TestStep:
    """测试步骤"""
    id: str
    step_name: str
    keyword_id: str
    parameters: Dict[str, Any]
    enabled: bool = True
    continue_on_failure: bool = False
    step_order: int = 0


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    steps: List[TestStep]


@dataclass
class GeneratedScenario:
    """生成的测试场景"""
    name: str
    description: str
    scenario_type: str = "recorded"
    cases: List[TestCase] = None

    def __post_init__(self):
        if self.cases is None:
            self.cases = []


class RecordingConverter:
    """录制转换器 - 将捕获的操作转换为测试场景"""

    def __init__(self):
        # 操作类型到关键字的映射
        self.keyword_mapping = {
            "click": "CLICK",
            "input": "INPUT",
            "navigate": "NAVIGATE",
            "select": "SELECT_OPTION",
            "wait": "WAIT_FOR_ELEMENT",
            "scroll": "SCROLL_TO_ELEMENT",
            "hover": "HOVER"
        }

        # 关键字名称到ID的映射（需要从数据库查询）
        self.keyword_cache: Dict[str, str] = {}

    async def convert_to_scenario(
        self,
        actions: List[CapturedAction],
        scenario_name: str,
        project_id: str,
        enable_smart_wait: bool = True,  # 🔥 新增：智能等待开关
        data_patterns: List[Any] = None,  # 🔥 新增：数据模式（用于变量替换）
        selected_patterns: List[str] = None,  # 🔥 新增：选中的模式ID列表
        filter_auto_navigate: bool = True  # 🔥 新增：是否过滤自动跳转导航
    ) -> GeneratedScenario:
        """将录制的操作序列转换为测试场景（支持变量替换）"""

        if not actions:
            raise ValueError("没有可转换的操作")

        # 🔥 构建变量映射表
        variable_map = {}
        if data_patterns and selected_patterns:
            for pattern in data_patterns:
                if pattern.selected and pattern.id in selected_patterns:
                    # 创建变量映射：原始值 -> 变量引用
                    for value in pattern.values:
                        variable_map[str(value)] = f"${{{pattern.field_name}}}"

        # 生成场景
        scenario = GeneratedScenario(
            name=scenario_name,
            description=f"通过录制创建，包含 {len(actions)} 个操作",
            scenario_type="recorded"
        )

        # 创建主用例
        main_case = TestCase(
            id=str(uuid.uuid4()),
            name="主流程",
            description="录制的主要操作流程",
            steps=[]
        )

        # 🔥 关键修复：确保 navigate 操作总是第一步
        # 将操作分为 navigate 操作和其他操作
        navigate_actions = [a for a in actions if a.action_type == 'navigate']
        other_actions = [a for a in actions if a.action_type != 'navigate']

        # 🔥 智能导航过滤：只保留主动导航，过滤掉自动跳转
        # 规则：只保留第一个导航操作，过滤掉后续连续的导航
        # 这解决了录制时包含所有页面跳转的问题
        ordered_actions = []
        if navigate_actions:
            if filter_auto_navigate:
                # 🔥 智能过滤算法
                # 策略1：只保留第一个导航（最简单有效）
                ordered_actions.append(navigate_actions[0])

                # 📝 可选优化策略（可以后续根据需要启用）：
                # 策略2：基于时间间隔 - 如果两个导航间隔<1秒，只保留第一个
                # if len(navigate_actions) > 1:
                #     for i in range(1, len(navigate_actions)):
                #         time_diff = navigate_actions[i].timestamp - navigate_actions[0].timestamp
                #         if time_diff < 1.0:  # 1秒内的导航认为是自动跳转
                #             continue  # 跳过这个导航
                #         ordered_actions.append(navigate_actions[i])
                #         break

                # 策略3：基于URL模式 - 过滤掉相似URL的导航
                # first_url = navigate_actions[0].page_url
                # for nav in navigate_actions[1:]:
                #     # 如果URL路径相似，可能是子页面跳转
                #     if nav.page_url.startswith(first_url) or first_url.startswith(nav.page_url):
                #         continue  # 跳过相似URL的导航
                #     ordered_actions.append(nav)
            else:
                # 不过滤，保留所有导航（兼容模式）
                ordered_actions.extend(navigate_actions)

        # 添加其他操作
        ordered_actions.extend(other_actions)

        # 🔥 新增：转换操作为步骤（支持智能等待和变量替换）
        step_counter = 0
        for index, action in enumerate(ordered_actions):
            steps = await self._convert_action_to_step(
                action,
                step_counter,
                enable_smart_wait and index > 0,  # 第一个操作（通常是导航）不需要等待
                variable_map  # 🔥 传递变量映射
            )
            main_case.steps.extend(steps)
            step_counter += len(steps)

        # 自动生成基础断言（暂时禁用，等待后续完善）
        # assertions = self._generate_assertions(ordered_actions)
        # main_case.steps.extend(assertions)

        scenario.cases.append(main_case)

        return scenario

    async def _convert_action_to_step(
        self,
        action: CapturedAction,
        index: int,
        add_wait_step: bool = False,  # 🔥 新增：是否添加等待步骤
        variable_map: Dict[str, str] = None  # 🔥 新增：变量映射表
    ) -> List[TestStep]:  # 🔥 修改：返回步骤列表
        """转换单个操作为测试步骤（可能包含等待步骤，支持变量替换）"""

        steps = []
        if variable_map is None:
            variable_map = {}

        # 🔥 新增：如果需要，先添加等待步骤
        if add_wait_step and action.action_type in ['click', 'input', 'select', 'hover', 'double_click']:
            wait_step = TestStep(
                id=str(uuid.uuid4()),
                step_name=f"等待元素就绪: {self._get_element_description(action)}",
                keyword_id=await self._get_keyword_id("WAIT_FOR_ELEMENT"),
                parameters={
                    "selector": action.selector,
                    "state": "visible",
                    "timeout": 5000
                },
                enabled=True,
                continue_on_failure=True,   # 🔥 等待失败不阻断后续步骤
                step_order=index
            )
            steps.append(wait_step)
            index += 1  # 实际操作步骤序号递增

        # 获取关键字名称
        keyword_name = self.keyword_mapping.get(action.action_type, "CLICK")

        # 获取关键字ID
        keyword_id = await self._get_keyword_id(keyword_name)

        # 🔥 修改：构建参数（应用变量替换）
        parameters = await self._build_parameters(action, variable_map)

        # 生成步骤描述
        step_name = self._generate_step_name(action)

        # 实际操作步骤
        actual_step = TestStep(
            id=str(uuid.uuid4()),
            step_name=step_name,
            keyword_id=keyword_id,
            parameters=parameters,
            enabled=True,
            continue_on_failure=True,   # 🔥 点击失败不阻断后续步骤
            step_order=index
        )
        steps.append(actual_step)

        return steps

    async def _build_parameters(
        self,
        action: CapturedAction,
        variable_map: Dict[str, str] = None  # 🔥 新增：变量映射表
    ) -> Dict[str, Any]:
        """根据操作类型构建参数（支持变量替换）"""

        if variable_map is None:
            variable_map = {}

        parameters = {
            "selector": action.selector,
            "timeout": 30000  # 默认30秒超时
        }

        # 根据操作类型添加特定参数
        if action.action_type == "input":
            # 🔥 应用变量替换
            input_value = action.value or ""
            if input_value in variable_map:
                parameters["text"] = variable_map[input_value]
                parameters["_original_value"] = input_value  # 保留原始值供参考
            else:
                parameters["text"] = input_value

        elif action.action_type == "navigate":
            parameters["url"] = action.page_url

        elif action.action_type == "select":
            # SELECT_OPTION 需要 value 参数
            if action.value:
                select_value = action.value
                if select_value in variable_map:
                    parameters["value"] = variable_map[select_value]
                    parameters["_original_value"] = select_value
                else:
                    parameters["value"] = select_value

        return parameters

    def _generate_step_name(self, action: CapturedAction) -> str:
        """生成步骤描述"""

        templates = {
            "click": f"点击 {self._get_element_description(action)}",
            "input": f"在 {self._get_element_description(action)} 输入",
            "navigate": f"导航到 {action.page_url}",
            "select": f"在下拉框 {self._get_element_description(action)} 选择",
            "wait": f"等待 {self._get_element_description(action)} 出现",
            "scroll": f"滚动到 {self._get_element_description(action)}",
            "hover": f"鼠标悬停在 {self._get_element_description(action)}"
        }

        default_name = templates.get(action.action_type, f"执行 {action.action_type} 操作")

        # 如果有输入值，添加到描述中
        if action.action_type == "input" and action.value:
            return f"{default_name} \"{action.value[:20]}...\""

        return default_name

    def _get_element_description(self, action: CapturedAction) -> str:
        """获取元素描述"""
        # 优先使用元素文本
        if action.element_text:
            text = action.element_text[:30] if action.element_text else ""
            if len(action.element_text) > 30:
                text = action.element_text[:30] + "..."
            return f'"{text}"'

        # 使用选择器
        if action.selector:
            selector = action.selector
            if len(selector) > 30:
                selector = selector[:30] + "..."
            return selector

        # 使用标签名
        if action.element_tag:
            return f"<{action.element_tag}>"

        return "元素"

    def _generate_assertions(self, actions: List[CapturedAction]) -> List[TestStep]:
        """基于操作序列生成智能断言"""

        assertions = []

        # 1. 导航后断言页面加载
        for action in actions:
            if action.action_type == "navigate":
                assertions.append(TestStep(
                    id=str(uuid.uuid4()),
                    step_name=f"验证页面加载完成: {action.page_title}",
                    keyword_id="",  # TODO: 需要查询 ASSERT_VISIBLE 的ID
                    parameters={
                        "selector": "body",
                        "timeout": 5000
                    },
                    enabled=True,
                    continue_on_failure=False,
                    step_order=0  # 将在后续调整
                ))

        # 2. 输入后断言值
        for action in actions:
            if action.action_type == "input" and action.value:
                assertions.append(TestStep(
                    id=str(uuid.uuid4()),
                    step_name=f"验证输入值: {action.value[:20]}",
                    keyword_id="",  # TODO: 需要查询 ASSERT_TEXT 的ID
                    parameters={
                        "selector": action.selector,
                        "expected": action.value,
                        "timeout": 3000
                    },
                    enabled=True,
                    continue_on_failure=False,
                    step_order=0
                ))

        # 3. 点击后断言元素可见
        for action in actions:
            if action.action_type == "click":
                assertions.append(TestStep(
                    id=str(uuid.uuid4()),
                    step_name=f"验证点击成功: {self._get_element_description(action)}",
                    keyword_id="",  # TODO: 需要查询 ASSERT_VISIBLE 的ID
                    parameters={
                        "selector": action.selector,
                        "timeout": 3000
                    },
                    enabled=True,
                    continue_on_failure=False,
                    step_order=0
                ))

        return assertions

    async def _get_keyword_id(self, keyword_name: str) -> str:
        """获取关键字ID（从缓存或数据库）"""
        if keyword_name in self.keyword_cache:
            return self.keyword_cache[keyword_name]

        # TODO: 从数据库查询
        # from app.core.database import SessionLocal
        # from app.models.keyword import Keyword
        # db = SessionLocal()
        # keyword = db.query(Keyword).filter(Keyword.name == keyword_name).first()
        # if keyword:
        #     self.keyword_cache[keyword_name] = str(keyword.id)
        #     return str(keyword.id)

        # 临时使用名称作为ID（后续需要替换为真实的数据库ID）
        temp_id = f"kw_{keyword_name.upper()}"
        self.keyword_cache[keyword_name] = temp_id
        return temp_id


# 全局转换器实例
recording_converter = RecordingConverter()