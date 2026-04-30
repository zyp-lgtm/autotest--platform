#!/usr/bin/env python3
"""
完整的API测试 - 模拟真实的HTTP请求
"""
import asyncio
import sys
import json
sys.path.insert(0, '.')

async def test_api():
    """完整测试API调用流程"""
    print("="*60)
    print("完整API测试")
    print("="*60)

    # 模拟请求数据
    request_data = {
        "project_id": "b5f37124-e987-41c6-8c02-8bf0d12ba420",
        "scenario_name": "API测试",
        "actions": [
            {"action_type": "navigate", "page_url": "https://example.com"},
            {"action_type": "input", "selector": "#test", "value": "test"},
            {"action_type": "click", "selector": ".btn"}
        ],
        "data_patterns": [
            {
                "id": "p1",
                "field_name": "test",
                "pattern_type": "input",
                "values": ["test"],
                "confidence": 0.9,
                "selected": True,
                "suggested_variations": []
            }
        ]
    }

    try:
        # 清除所有缓存模块
        for key in list(sys.modules.keys()):
            if 'recording' in key.lower() or 'recorder' in key.lower():
                del sys.modules[key]

        # 导入模块
        from app.services.recording.converter import recording_converter
        from app.services.recorder import CapturedAction
        from app.services.recording.data_extractor import DataPattern, data_extractor

        # 转换操作
        print("\n1. 转换操作...")
        actions = [CapturedAction(**action) for action in request_data['actions']]
        print(f"   ✅ 转换了 {len(actions)} 个操作")

        # 转换模式
        print("\n2. 转换数据模式...")
        patterns = [DataPattern(**pattern) for pattern in request_data['data_patterns']]
        print(f"   ✅ 转换了 {len(patterns)} 个数据模式")

        # 生成场景
        print("\n3. 生成场景...")
        scenario = await recording_converter.convert_to_scenario(
            actions=actions,
            scenario_name=request_data['scenario_name'],
            project_id=request_data['project_id']
        )
        print(f"   ✅ 场景: {scenario.name}")
        print(f"   ✅ 用例: {len(scenario.cases)}")
        print(f"   ✅ 步骤: {len(scenario.cases[0].steps)}")

        # 生成测试数据
        print("\n4. 生成测试数据...")
        test_data = data_extractor.generate_test_data(
            patterns=patterns,
            scenario_name=request_data['scenario_name'],
            project_id=request_data['project_id']
        )
        print(f"   ✅ 测试数据: {test_data['name']}")
        print(f"   ✅ 数据条数: {len(test_data['data'])}")

        # 构建响应
        response = {
            "scenario": {
                "name": scenario.name,
                "description": scenario.description,
                "scenario_type": scenario.scenario_type,
                "cases": [
                    {
                        "id": case.id,
                        "name": case.name,
                        "description": case.description,
                        "steps": [
                            {
                                "id": step.id,
                                "step_name": step.step_name,
                                "keyword_id": step.keyword_id,
                                "parameters": step.parameters,
                                "enabled": step.enabled,
                                "continue_on_failure": step.continue_on_failure,
                                "step_order": step.step_order
                            }
                            for step in case.steps
                        ]
                    }
                    for case in scenario.cases
                ],
                "metadata": {
                    "created_by": "recording",
                    "actions_count": len(actions),
                    "data_patterns_count": len(patterns)
                }
            },
            "test_data": test_data
        }

        print("\n" + "="*60)
        print("✅ 完整流程测试成功！")
        print("="*60)
        print(f"\n响应预览:")
        print(json.dumps({"scenario": {"name": response["scenario"]["name"], "steps_count": len(response["scenario"]["cases"][0]["steps"])}, "test_data": response["test_data"]["name"]}, indent=2))

        return True

    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)
