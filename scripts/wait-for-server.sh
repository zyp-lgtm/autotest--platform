#!/bin/bash

echo "等待服务器启动..."

for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo ""
        echo "✓ 服务器已就绪！"
        echo ""
        curl -s http://localhost:8000/health
        echo ""
        exit 0
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "✗ 服务器启动超时"
echo ""
echo "请检查："
echo "  docker ps"
echo "  docker logs test-platform-backend"
exit 1
