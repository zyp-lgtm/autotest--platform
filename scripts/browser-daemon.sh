#!/bin/bash

####################################################################
# 测试平台浏览器守护进程
#
# 功能：
# 1. 自动启动支持远程调试的 Chrome 浏览器
# 2. 监听 9222 端口，如果 Chrome 意外关闭则自动重启
# 3. 提供优雅的停止机制
#
# 使用方法：
#   ./browser-daemon.sh start   # 启动守护进程
#   ./browser-daemon.sh stop    # 停止守护进程
#   ./browser-daemon.sh status  # 查看状态
#   ./browser-daemon.sh restart # 重启守护进程
#
# 安装方法（仅首次需要）：
#   1. cd /Users/apple/aicode/.worktrees/test-platform/scripts
#   2. chmod +x browser-daemon.sh
#   3. ./browser-daemon.sh install  # 安装到 launchd（开机自启动）
####################################################################

# 配置
CHROME_APP="/Applications/Google Chrome.app"
CHROME_BINARY="${CHROME_APP}/Contents/MacOS/Google Chrome"
DEBUG_PORT=9222
USER_DATA_DIR="/tmp/chrome-debug-test-platform"
PID_FILE="/tmp/chrome-daemon.pid"
LOG_FILE="/tmp/chrome-daemon.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Chrome 是否已安装
check_chrome() {
    if [ ! -d "$CHROME_APP" ]; then
        echo -e "${RED}错误: 找不到 Google Chrome${NC}"
        echo "请安装 Google Chrome 或修改脚本中的 CHROME_APP 路径"
        exit 1
    fi
}

# 检查端口是否被占用
check_port() {
    if lsof -i :$DEBUG_PORT > /dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 启动 Chrome
start_chrome() {
    echo "启动 Chrome 浏览器 (远程调试端口: $DEBUG_PORT)..."

    # 检查端口
    if check_port; then
        echo -e "${YELLOW}警告: 端口 $DEBUG_PORT 已被占用${NC}"
        echo "检查是否已有 Chrome 在运行..."
        if lsof -i :$DEBUG_PORT | grep -q "Chrome"; then
            echo -e "${GREEN}Chrome 已在运行${NC}"
            return 0
        else
            echo -e "${RED}错误: 端口 $DEBUG_PORT 被其他程序占用${NC}"
            echo "占用端口的进程："
            lsof -i :$DEBUG_PORT
            return 1
        fi
    fi

    # 启动 Chrome（后台运行）
    nohup "$CHROME_BINARY" \
        --remote-debugging-port=$DEBUG_PORT \
        --user-data-dir="$USER_DATA_DIR" \
        --no-first-run \
        --no-default-browser-check \
        --disable-popup-blocking \
        > "$LOG_FILE" 2>&1 &

    CHROME_PID=$!

    # 等待 Chrome 启动
    echo -n "等待 Chrome 启动"
    for i in {1..10}; do
        if check_port; then
            echo -e " ${GREEN}✓${NC}"
            echo -e "${GREEN}Chrome 已启动 (PID: $CHROME_PID)${NC}"
            echo $CHROME_PID > "$PID_FILE"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    echo -e " ${RED}✗${NC}"
    echo -e "${RED}Chrome 启动失败${NC}"
    echo "查看日志: cat $LOG_FILE"
    return 1
}

# 停止 Chrome
stop_chrome() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Chrome 守护进程未运行"
        return 0
    fi

    PID=$(cat "$PID_FILE")
    echo "停止 Chrome (PID: $PID)..."

    # 杀死进程
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        sleep 1

        # 如果还在运行，强制杀死
        if kill -0 $PID 2>/dev/null; then
            echo "强制停止..."
            kill -9 $PID
        fi

        echo -e "${GREEN}Chrome 已停止${NC}"
    else
        echo "Chrome 进程不存在"
    fi

    rm -f "$PID_FILE"

    # 清理可能残留的 Chrome 进程
    pkill -f "remote-debugging-port=$DEBUG_PORT" 2>/dev/null
}

# 检查状态
check_status() {
    echo "=== Chrome 守护进程状态 ==="
    echo ""

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo -e "${GREEN}状态: 运行中${NC}"
            echo "PID: $PID"
            echo ""

            if check_port; then
                echo -e "${GREEN}端口 $DEBUG_PORT: 监听中${NC}"
                echo ""
                echo "连接信息："
                echo "  WebSocket URL: ws://localhost:$DEBUG_PORT"
                echo "  Docker URL: ws://host.docker.internal:$DEBUG_PORT"
            else
                echo -e "${YELLOW}警告: 进程存在但端口未监听${NC}"
            fi
        else
            echo -e "${RED}状态: 已停止（PID 文件存在但进程不存在）${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}状态: 未运行${NC}"
    fi

    echo ""
    echo "日志文件: $LOG_FILE"
    echo "用户数据: $USER_DATA_DIR"
}

# 守护进程循环
daemon_loop() {
    echo "Chrome 守护进程启动中..."
    echo "日志: $LOG_FILE"

    while true; do
        # 检查 Chrome 是否在运行
        if ! check_port || ! lsof -i :$DEBUG_PORT | grep -q "Chrome"; then
            echo "$(date): Chrome 未运行，尝试启动..." >> "$LOG_FILE"
            start_chrome
        fi

        # 每 10 秒检查一次
        sleep 10
    done
}

# 安装到 launchd（开机自启动）
install_launchd() {
    PLIST_FILE="$HOME/Library/LaunchAgents/com.testplatform.browser-daemon.plist"
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    SCRIPT_PATH="$SCRIPT_DIR/browser-daemon.sh"

    echo "安装守护进程到 launchd..."

    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.testplatform.browser-daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_PATH</string>
        <string>daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
</dict>
</plist>
EOF

    # 加载 launchd 服务
    launchctl load "$PLIST_FILE"

    echo -e "${GREEN}守护进程已安装并启动${NC}"
    echo "服务文件: $PLIST_FILE"
    echo ""
    echo "使用以下命令管理："
    echo "  launchctl unload $PLIST_FILE  # 停止服务"
    echo "  launchctl load $PLIST_FILE    # 启动服务"
}

# 卸载 launchd
uninstall_launchd() {
    PLIST_FILE="$HOME/Library/LaunchAgents/com.testplatform.browser-daemon.plist"

    if [ -f "$PLIST_FILE" ]; then
        echo "卸载守护进程..."
        launchctl unload "$PLIST_FILE" 2>/dev/null
        rm -f "$PLIST_FILE"
        echo -e "${GREEN}守护进程已卸载${NC}"
    else
        echo "守护进程未安装"
    fi
}

# 主命令处理
case "$1" in
    start)
        check_chrome
        start_chrome
        ;;
    stop)
        stop_chrome
        ;;
    status)
        check_status
        ;;
    restart)
        stop_chrome
        sleep 1
        start_chrome
        ;;
    daemon)
        daemon_loop
        ;;
    install)
        install_launchd
        ;;
    uninstall)
        uninstall_launchd
        ;;
    *)
        echo "Chrome 浏览器守护进程"
        echo ""
        echo "使用方法:"
        echo "  $0 start     启动 Chrome（一次性）"
        echo "  $0 stop      停止 Chrome"
        echo "  $0 status    查看状态"
        echo "  $0 restart   重启 Chrome"
        echo "  $0 install   安装为系统服务（开机自启动）"
        echo "  $0 uninstall 卸载系统服务"
        echo ""
        echo "首次使用建议:"
        echo "  1. 运行: $0 start"
        echo "  2. 运行: $0 status 检查状态"
        echo "  3. 确认正常后运行: $0 install 安装为系统服务"
        exit 1
        ;;
esac
