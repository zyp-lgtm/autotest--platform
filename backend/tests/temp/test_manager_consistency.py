#!/usr/bin/env python3
"""测试 manager 实例一致性"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("测试 Manager 实例一致性")
print("=" * 60)

# 导入 agent 模块（模拟 main.py 的导入）
from app.api import agent

print(f"\n1. agent.manager ID: {id(agent.manager)}")
print(f"2. agent.manager.agents: {agent.manager.get_all_agents()}")

# 模拟 executor.py 的导入
from app.api import agent as agent_manager

print(f"\n3. agent_manager.manager ID: {id(agent_manager.manager)}")
print(f"4. agent_manager.manager.agents: {agent_manager.manager.get_all_agents()}")

print(f"\n5. 两个 ID 是否相同: {id(agent.manager) == id(agent_manager.manager)}")

# 测试注册
print(f"\n6. 模拟注册一个测试 Agent...")
agent.manager.register_agent("test-agent-123", {"name": "测试"})

print(f"\n7. agent.manager.agents: {agent.manager.get_all_agents()}")
print(f"8. agent_manager.manager.agents: {agent_manager.manager.get_all_agents()}")

print("\n" + "=" * 60)
