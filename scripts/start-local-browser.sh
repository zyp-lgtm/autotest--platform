#!/bin/bash

####################################################################
# 测试平台 - 本地浏览器一键启动脚本
#
# 这是用户唯一需要运行的脚本！
# 运行后，Chrome 浏览器将在后台运行，测试平台可以直接使用
####################################################################

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DAEMON_SCRIPT="$SCRIPT_DIR/browser-daemon.sh"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "  测试平台 - 本地浏览器服务"
echo "=========================================="
echo ""

# 检查守护进程脚本
if [ ! -f "$DAEMON_SCRIPT" ]; then
    echo "错误: 找不到守护进程脚本"
    exit 1
fi

# 启动服务
echo "正在启动本地浏览器服务..."
echo ""

$DAEMON_SCRIPT start

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ 本地浏览器服务已启动${NC}"
    echo ""
    echo "=========================================="
    echo "  现在您可以直接执行测试任务了！"
    echo "=========================================="
    echo ""
    echo "使用说明："
    echo ""
    echo "1. 在任务的\"打开浏览器\"关键字中设置:"
    echo "   {"
    echo "     \"keyword\": \"打开浏览器\","
    echo "     \"parameters\": {"
    echo "       \"use_local\": true,"
    echo "       \"headless\": false"
    echo "     }"
    echo "   }"
    echo ""
    echo "2. 执行任务，浏览器会自动在您的 Mac 上打开"
    echo ""
    echo "=========================================="
    echo ""
    echo "其他命令："
    echo "  查看状态: $DAEMON_SCRIPT status"
    echo "  停止服务: $DAEMON_SCRIPT stop"
    echo "  安装为开机启动: $DAEMON_SCRIPT install"
    echo ""
else
    echo ""
    echo -e "${YELLOW}启动失败，请检查:${NC}"
    echo "  1. 确保 Google Chrome 已安装"
    echo "  2. 检查端口 9222 是否被其他程序占用"
    echo "     运行: lsof -i :9222"
    echo ""
    exit 1
fi
