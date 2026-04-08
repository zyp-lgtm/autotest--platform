#!/bin/bash

echo "=== 强制刷新容器代码 ==="

# 1. 停止容器
echo "停止容器..."
/Applications/Docker.app/Contents/Resources/bin/docker stop test-platform-backend

# 2. 清除 Python 缓存
echo "清除缓存..."
/Applications/Docker.app/Contents/Resources/bin/docker exec test-platform-backend find /app -type f -name "*.pyc" -delete 2>/dev/null || true
/Applications/Docker.app/Contents/Resources/bin/docker exec test-platform-backend find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 3. 启动容器
echo "启动容器..."
/Applications/Docker.app/Contents/Resources/bin/docker start test-platform-backend

# 4. 等待启动
echo "等待启动完成..."
sleep 15

# 5. 验证代码
echo "验证代码版本..."
/Applications/Docker.app/Contents/Resources/bin/docker exec test-platform-backend grep -n "当前可用 Agent 数量" /app/app/services/executor.py

# 6. 验证健康状态
curl -s http://localhost:8000/health | jq

echo ""
echo "=== 刷新完成 ==="
