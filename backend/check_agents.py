#!/usr/bin/env python3
"""检查 Agent 注册状态"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.api.agent import manager

print("=" * 60)
print("Agent 注册状态检查")
print("=" * 60)

agents = manager.get_all_agents()
print(f"\n当前注册的 Agent 数量: {len(agents)}")

if agents:
    for agent_id, info in agents.items():
        print(f"\nAgent ID: {agent_id}")
        print(f"  信息: {info}")
else:
    print("\n❌ 没有注册的 Agent")
    print("\n可能的原因:")
    print("  1. Agent 没有启动")
    print("  2. Agent 连接到了不同的后端实例")
    print("  3. 后端重启导致 Agent 连接断开")

print("\n" + "=" * 60)
