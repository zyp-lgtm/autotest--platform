#!/bin/bash
# 独立的后端启动脚本
# 用于在界面无法启动后端时使用

cd "$(dirname "$0")"

echo "=========================================="
echo "启动后端服务"
echo "=========================================="

# 检查是否已在运行
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  端口 8000 已被占用"
    echo "正在尝试停止现有进程..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# 清理旧PID文件
rm -f /tmp/backend.pid

# 启动后端
echo "启动后端服务..."
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > /tmp/backend.pid

echo ""
echo "等待后端启动..."
sleep 3

# 检查是否启动成功
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ 后端启动成功 (PID: $BACKEND_PID)"
    echo "日志文件: /tmp/backend.log"
    echo "健康检查: curl http://localhost:8000/api/v1/health"
else
    echo "❌ 后端启动失败"
    echo "查看日志: tail -50 /tmp/backend.log"
    exit 1
fi
