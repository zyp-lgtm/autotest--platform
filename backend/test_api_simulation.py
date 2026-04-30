#!/usr/bin/env python3
"""
模拟完整的 API 调用流程
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.recording.converter import recording_converter
from app.services.recorder import CapturedAction
from app.services.recording.data_extractor import DataPattern, data_extractor

async def simulate_api_call():
    """模拟 API 端点的完整流程"""
    print("="*60)
    print("模拟 API 调用流程")
    print("="*60)

    # 模拟请求数据
    request_actions = [
        {"action_type": "navigate", "page_url": "https://example.com"},
        {"action_type": "input", "selector": "#test", "value": "test"}
    ]

    request_patterns = [
        {"id": "p1", "field_name": "test", "pattern_type": "input",
         "values": ["test"], "confidence": 0.9, "selected": True, "suggested_variations": []}
    ]

    try:
        # 转换操作（与 API 端点相同的方式）
        print("\n1. 转换操作...")
        actions = [CapturedAction(**action) for action in request_actions]
        print(f"   ✅ 创建了 {len(actions)} 个操作")

        # 转换模式
        print("\n2. 转换数据模式...")
        patterns = [DataPattern(**pattern) for pattern in request_patterns]
        print(f"   ✅ 创建了 {len(patterns)} 个模式")

        # 生成场景
        print("\n3. 生成场景...")
        scenario = await recording_converter.convert_to_scenario(
            actions=actions,
            scenario_name="测试场景",
            project_id="test-project"
        )
        print(f"   ✅ 场景名称: {scenario.name}")
        print(f"   ✅ 用例数: {len(scenario.cases)}")
        print(f"   ✅ 步骤数: {len(scenario.cases[0].steps)}")

        # 生成测试数据
        print("\n4. 生成测试数据...")
        test_data = data_extractor.generate_test_data(
            patterns=patterns,
            scenario_name="测试场景",
            project_id="test-project"
        )
        print(f"   ✅ 测试数据名称: {test_data['name']}")

        print("\n" + "="*60)
        print("✅ 完整流程成功！")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(simulate_api_call())
    sys.exit(0 if success else 1)
