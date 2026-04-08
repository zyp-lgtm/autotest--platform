#!/bin/bash

echo "=== 启动 Agent ==="
cd /Users/apple/aicode/.worktrees/test-platform/agent
source venv/bin/activate
python agent.py --server ws://localhost:8000/agent 2>&1 | tee /tmp/agent_latest.log &
AGENT_PID=$!

echo "Agent PID: $AGENT_PID"
echo "等待 Agent 连接..."
sleep 3

echo "=== 执行测试任务 ==="
curl -s -X POST "http://localhost:8000/api/v1/ui/tasks/611ac475-20ac-4725-8944-9e15d4376b52/execute" \
  -H "Content-Type: application/json" \
  -d '{"browser_config": {"browser_type": "chromium", "headless": false}}' | jq '{status, result, total_steps}'

echo ""
echo "=== 等待任务完成 ==="
sleep 8

echo ""
echo "=== Agent 日志（最后 30 行）==="
tail -30 /tmp/agent_latest.log

echo ""
echo "=== 清理 ==="
kill $AGENT_PID 2>/dev/null
