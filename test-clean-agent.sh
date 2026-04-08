#!/bin/bash

# 清理所有旧 Agent
pkill -9 -f "python.*agent.py"
sleep 2

# 启动新 Agent（使用 -u 禁用缓冲）
cd /Users/apple/aicode/.worktrees/test-platform/agent
source venv/bin/activate
python -u agent.py --server ws://localhost:8000/agent > /tmp/agent_detailed.log 2>&1 &
NEW_AGENT_PID=$!

echo "新 Agent PID: $NEW_AGENT_PID"
sleep 4

# 执行任务
echo "=== 执行测试任务 ==="
curl -s -X POST "http://localhost:8000/api/v1/ui/tasks/611ac475-20ac-4725-8944-9e15d4376b52/execute" \
  -H "Content-Type: application/json" \
  -d '{"browser_config": {"browser_type": "chromium", "headless": false}}' | jq '{status, result, total_steps}'

echo ""
echo "=== 等待任务完成 ==="
sleep 15

echo ""
echo "=== 详细日志 ==="
cat /tmp/agent_detailed.log

echo ""
echo "=== 清理 ==="
kill $NEW_AGENT_PID 2>/dev/null
