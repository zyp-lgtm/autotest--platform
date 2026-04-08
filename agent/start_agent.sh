#!/bin/bash
# Agent 启动脚本
cd "$(dirname "$0")"

# 清理旧的 PID 文件（让 agent 自己创建）
rm -f .agent.pid

# 启动 Agent（不使用输出重定向，让 agent 自己处理日志）
nohup python3 agent.py --server ws://localhost:8000/agent > /tmp/agent.log 2>&1 &

echo "Agent 启动脚本已执行"
exit 0
