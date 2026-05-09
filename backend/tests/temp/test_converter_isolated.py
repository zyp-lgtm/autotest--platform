"""
完全独立的录制转换器测试 - 隔离问题
"""
import asyncio
import sys
sys.path.insert(0, '.')

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid

# 重新定义所有类，避免导入问题
@dataclass
class TestStep:
    id: str
    step_name: str
    keyword_id: str
    parameters: Dict[str, Any]
    enabled: bool = True
    continue_on_failure: bool = False
    step_order: int = 0

@dataclass
class TestCase:
    id: str
    name: str
    description: str
    steps: List[TestStep]

@dataclass
class GeneratedScenario:
    name: str
    description: str
    scenario_type: str = "recorded"
    cases: List[TestCase] = field(default_factory=list)

class SimpleConverter:
    """简化的转换器 - 隔离测试"""

    def __init__(self):
        self.keyword_mapping = {
            "click": "CLICK",
            "input": "INPUT",
            "navigate": "NAVIGATE",
            "select": "SELECT_OPTION"
        }
        self.keyword_cache: Dict[str, str] = {}

    async def _get_keyword_id(self, keyword_name: str) -> str:
        """获取关键字ID"""
        print(f"DEBUG: _get_keyword_id called with keyword_name={keyword_name}")
        print(f"DEBUG: Available locals: {list(locals().keys())}")

        if keyword_name in self.keyword_cache:
            print(f"DEBUG: Cache hit for {keyword_name}")
            return self.keyword_cache[keyword_name]

        temp_id = f"kw_{keyword_name.upper()}"
        self.keyword_cache[keyword_name] = temp_id
        print(f"DEBUG: Created new ID {temp_id} for {keyword_name}")
        return temp_id

    async def convert_to_scenario(self, actions, scenario_name: str, project_id: str) -> GeneratedScenario:
        """转换操作为场景"""
        scenario = GeneratedScenario(
            name=scenario_name,
            description=f"包含 {len(actions)} 个操作"
        )

        main_case = TestCase(
            id=str(uuid.uuid4()),
            name="主流程",
            description="测试",
            steps=[]
        )

        for index, action in enumerate(actions):
            print(f"\n处理操作 {index+1}: {action['action_type']}")
            keyword_name = self.keyword_mapping.get(action['action_type'], "CLICK")
            print(f"  映射到关键字: {keyword_name}")
            keyword_id = await self._get_keyword_id(keyword_name)
            print(f"  获得ID: {keyword_id}")

            step = TestStep(
                id=str(uuid.uuid4()),
                step_name=f"步骤{index+1}",
                keyword_id=keyword_id,
                parameters={"selector": action.get("selector", "")},
                step_order=index + 1
            )
            main_case.steps.append(step)

        scenario.cases.append(main_case)
        return scenario

# 测试数据
test_actions = [
    {"action_type": "navigate", "page_url": "https://example.com"},
    {"action_type": "input", "selector": "#test", "value": "test"},
    {"action_type": "click", "selector": ".btn"}
]

async def main():
    print("="*60)
    print("独立转换器测试")
    print("="*60)

    converter = SimpleConverter()

    try:
        scenario = await converter.convert_to_scenario(
            actions=test_actions,
            scenario_name="独立测试",
            project_id="test"
        )

        print(f"\n✅ 成功生成场景!")
        print(f"   名称: {scenario.name}")
        print(f"   用例: {len(scenario.cases)}")
        print(f"   步骤: {len(scenario.cases[0].steps)}")

        for i, step in enumerate(scenario.cases[0].steps):
            print(f"     {i+1}. {step.step_name} ({step.keyword_id})")

        return True

    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
