#!/bin/bash

####################################################################
# 测试平台 - 重启后端容器
#
# 用于应用代码更改后重启 Docker 容器
####################################################################

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/../docker"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "  重启后端容器"
echo "=========================================="
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行"
    echo "请先启动 Docker Desktop"
    exit 1
fi

cd "$DOCKER_DIR"

echo "正在重启后端容器..."
echo ""

docker compose restart backend

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ 后端容器重启成功${NC}"
    echo ""
    echo "等待服务启动..."
    sleep 5

    echo ""
    echo "查看实时日志（Ctrl+C 退出）:"
    echo "  docker logs test-platform-backend -f"
    echo ""
    echo "或者直接执行测试任务！"
else
    echo ""
    echo "重启失败，请检查日志"
    exit 1
fi
