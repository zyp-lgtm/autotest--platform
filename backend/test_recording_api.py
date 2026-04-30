#!/usr/bin/env python3
"""
测试录制API的完整流程
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.recording.converter import RecordingConverter
from app.services.recorder import CapturedAction
from app.services.recording.data_extractor import DataPattern

async def main():
    print("=" * 60)
    print("测试录制API完整流程")
    print("=" * 60)

    # 初始化转换器
    converter = RecordingConverter()
    print("✅ 转换器初始化成功")

    # 创建测试操作
    actions = [
        CapturedAction(
            action_type="navigate",
            page_url="https://example.com/login"
        ),
        CapturedAction(
            action_type="input",
            selector="#username",
            value="testuser"
        ),
        CapturedAction(
            action_type="click",
            selector=".btn"
        )
    ]
    print(f"✅ 创建了 {len(actions)} 个操作")

    # 创建数据模式
    patterns = [
        DataPattern(
            id="test-1",
            field_name="username",
            pattern_type="input",
            values=["testuser"],
            confidence=0.9,
            selected=True
        )
    ]
    print(f"✅ 创建了 {len(patterns)} 个数据模式")

    try:
        # 生成场景
        print("\n开始生成场景...")
        scenario = await converter.convert_to_scenario(
            actions=actions,
            scenario_name="测试场景",
            project_id="test-project-id"
        )

        print(f"✅ 场景生成成功!")
        print(f"   名称: {scenario.name}")
        print(f"   描述: {scenario.description}")
        print(f"   用例数: {len(scenario.cases)}")

        for i, case in enumerate(scenario.cases):
            print(f"\n   用例 {i+1}: {case.name}")
            print(f"   步骤数: {len(case.steps)}")
            for j, step in enumerate(case.steps[:3]):  # 只显示前3个步骤
                print(f"     {j+1}. {step.step_name} (keyword: {step.keyword_id})")

        # 生成测试数据
        print("\n开始生成测试数据...")
        from app.services.recording.data_extractor import data_extractor
        test_data = data_extractor.generate_test_data(
            patterns=patterns,
            scenario_name="测试场景",
            project_id="test-project-id"
        )

        print(f"✅ 测试数据生成成功!")
        print(f"   数据名称: {test_data['name']}")
        print(f"   数据条数: {len(test_data['data'])}")

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
