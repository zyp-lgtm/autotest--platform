#!/bin/bash

echo "=== 检查后端容器状态 ==="
docker ps -a | grep test-platform

echo ""
echo "=== 查看后端日志（最后 50 行）==="
docker logs test-platform-backend --tail 50

echo ""
echo "=== 检查容器健康状态 ==="
docker inspect test-platform-backend --format='{{.State.Health.Status}}'

echo ""
echo "=== 尝试进入容器检查 ==="
docker exec test-platform-backend ls /app/app/main.py 2>&1

echo ""
echo "=== 检查 Python 环境 ==="
docker exec test-platform-backend python --version 2>&1

echo ""
echo "=== 检查依赖 ==="
docker exec test-platform-backend pip list | grep fastapi 2>&1
