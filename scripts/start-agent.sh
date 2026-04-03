#!/bin/bash

####################################################################
# 测试平台 - 启动本地 Agent
#
# 用于连接到服务器并接收测试任务
####################################################################

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="$SCRIPT_DIR/../agent"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "  测试平台 - 本地执行 Agent"
echo "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    echo "请安装 Python 3.8 或更高版本"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
cd "$AGENT_DIR"

if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装依赖..."
pip install -q -r requirements.txt

# 检查 Playwright 浏览器
echo "检查 Playwright 浏览器..."
if ! playwright install chromium &> /dev/null; then
    echo -e "${YELLOW}需要安装 Playwright 浏览器${NC}"
    echo "运行: playwright install chromium"
fi

echo ""
echo -e "${GREEN}✓ 依赖检查完成${NC}"
echo ""

# 默认服务器地址
DEFAULT_SERVER="ws://localhost:8000/agent"

# 如果提供了参数，使用第一个参数作为服务器地址
if [ -n "$1" ]; then
    SERVER_URL="$1"
else
    SERVER_URL="$DEFAULT_SERVER"
fi

echo "=========================================="
echo "  配置"
echo "=========================================="
echo ""
echo "服务器: $SERVER_URL"
echo ""
echo "=========================================="
echo ""

echo "启动 Agent..."
echo "按 Ctrl+C 停止"
echo ""

python3 agent.py --server "$SERVER_URL"
