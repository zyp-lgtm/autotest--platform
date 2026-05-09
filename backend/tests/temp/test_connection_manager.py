#!/usr/bin/env python3
"""测试 ConnectionManager 是否能看到 Agent"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.api.agent import manager

print("=" * 60)
print("ConnectionManager 测试")
print("=" * 60)

# 测试单例
print(f"1. manager 类型: {type(manager)}")
print(f"2. manager._initialized: {manager._initialized}")
print(f"3. active_connections 数量: {len(manager.active_connections)}")
print(f"4. agents 数量: {len(manager.agents)}")

if manager.active_connections:
    print(f"5. 已连接的 Agent IDs: {list(manager.active_connections.keys())}")

if manager.agents:
    print(f"6. 已注册的 Agent IDs: {list(manager.agents.keys())}")
    for agent_id, info in manager.agents.items():
        print(f"   - {agent_id}: {info}")

# 测试 get_all_agents
all_agents = manager.get_all_agents()
print(f"7. get_all_agents() 返回类型: {type(all_agents)}")
print(f"8. get_all_agents() 长度: {len(all_agents)}")
print(f"9. get_all_agents() 内容: {all_agents}")

print("\n" + "=" * 60)
