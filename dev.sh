#!/bin/bash
#
# 测试自动化平台 - 统一启动/停止脚本
#
# 使用方法：
#   ./dev.sh start   - 启动所有服务
#   ./dev.sh stop    -停止所有服务
#   ./dev.sh restart -重启所有服务
#   ./dev.sh status  -查看服务状态
#

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
AGENT_DIR="$SCRIPT_DIR/agent"

# PID 文件
BACKEND_PID_FILE="/tmp/backend.pid"
AGENT_PID_FILE="$AGENT_DIR/.agent.pid"

# 日志文件
BACKEND_LOG="/tmp/backend.log"
AGENT_LOG="/tmp/agent.log"

# 端口
BACKEND_PORT=8000

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🚀 测试自动化平台 - 快速启动/停止脚本                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查服务状态
check_status() {
    echo -e "${YELLOW}📊 服务状态${NC}"
    echo ""

    # 检查后端
    if lsof -ti:$BACKEND_PORT > /dev/null 2>&1; then
        BACKEND_PID=$(lsof -ti:$BACKEND_PORT)
        echo -e "  后端服务: ${GREEN}✅ 运行中${NC} (PID: $BACKEND_PID)"
    else
        echo -e "  后端服务: ${RED}❌ 未运行${NC}"
    fi

    # 检查 Agent
    if [ -f "$AGENT_PID_FILE" ]; then
        AGENT_PID=$(cat "$AGENT_PID_FILE" 2>/dev/null || echo "")
        if ps -p "$AGENT_PID" > /dev/null 2>&1; then
            echo -e "  Agent:     ${GREEN}✅ 运行中${NC} (PID: $AGENT_PID)"
        else
            echo -e "  Agent:     ${RED}❌ 未运行${NC}"
        fi
    else
        # 通过进程检查
        AGENT_PID=$(pgrep -f "python.*agent.py" | head -1)
        if [ -n "$AGENT_PID" ]; then
            echo -e "  Agent:     ${GREEN}✅ 运行中${NC} (PID: $AGENT_PID)"
        else
            echo -e "  Agent:     ${RED}❌ 未运行${NC}"
        fi
    fi

    echo ""
    echo "📡 API 端点:"
    echo "  - 健康检查: http://localhost:$BACKEND_PORT/api/v1/health"
    echo "  - API 文档:  http://localhost:$BACKEND_PORT/docs"
    echo ""
}

# 启动后端
start_backend() {
    echo -e "${BLUE}📡 启动后端服务...${NC}"

    cd "$BACKEND_DIR"

    # 检查是否已在运行
    if lsof -ti:$BACKEND_PORT > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $BACKEND_PORT 已被占用${NC}"
        echo "正在停止现有进程..."
        lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
        sleep 1
    fi

    # 清理旧PID文件
    rm -f "$BACKEND_PID_FILE"

    # 启动后端
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"

    # 等待启动
    sleep 4

    # 验证启动
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端启动成功${NC} (PID: $BACKEND_PID)"
        echo "   日志: tail -f $BACKEND_LOG"
    else
        echo -e "${RED}❌ 后端启动失败${NC}"
        echo "   查看日志: tail -50 $BACKEND_LOG"
        return 1
    fi

    echo ""
}

# 启动 Agent
start_agent() {
    echo -e "${BLUE}🤖 启动 Agent...${NC}"

    cd "$AGENT_DIR"

    # 停止现有 Agent
    if [ -f "$AGENT_PID_FILE" ]; then
        OLD_PID=$(cat "$AGENT_PID_FILE" 2>/dev/null || "")
        if [ -n "$OLD_PID" ] && ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "停止现有 Agent (PID: $OLD_PID)..."
            kill $OLD_PID 2>/dev/null || true
            sleep 1
        fi
    fi

    # 清理旧PID文件
    rm -f "$AGENT_PID_FILE"

    # 启动 Agent
    nohup python3 agent.py --server ws://localhost:$BACKEND_PORT/agent > "$AGENT_LOG" 2>&1 &
    AGENT_PID=$!

    # 等待启动
    sleep 3

    # 验证启动
    if ps -p $AGENT_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Agent 启动成功${NC} (PID: $AGENT_PID)"
        echo "   日志: tail -f $AGENT_LOG"
    else
        echo -e "${YELLOW}⚠️  Agent 启动可能失败${NC}"
        echo "   查看日志: tail -50 $AGENT_LOG"
    fi

    echo ""
}

# 停止后端
stop_backend() {
    echo -e "${YELLOW}🛑 停止后端服务...${NC}"

    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE" 2>/dev/null || "")
        if [ -n "$BACKEND_PID" ] && ps -p "$BACKEND_PID" > /dev/null 2>&1; then
            kill $BACKEND_PID 2>/dev/null || true
            sleep 1
            echo -e "${GREEN}✅ 后端已停止${NC}"
        else
            echo -e "${YELLOW}⚠️  后端未运行${NC}"
        fi
        rm -f "$BACKEND_PID_FILE"
    else
        # 尝试通过端口停止
        if lsof -ti:$BACKEND_PORT > /dev/null 2>&1; then
            lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
            echo -e "${GREEN}✅ 后端已停止${NC}"
        else
            echo -e "${YELLOW}⚠️  后端未运行${NC}"
        fi
    fi
    echo ""
}

# 停止 Agent
stop_agent() {
    echo -e "${YELLOW}🛑 停止 Agent...${NC}"

    if [ -f "$AGENT_PID_FILE" ]; then
        AGENT_PID=$(cat "$AGENT_PID_FILE" 2>/dev/null || "")
        if [ -n "$AGENT_PID" ] && ps -p "$AGENT_PID" > /dev/null 2>&1; then
            kill $AGENT_PID 2>/dev/null || true
            sleep 1
            echo -e "${GREEN}✅ Agent 已停止${NC}"
        else
            echo -e "${YELLOW}⚠️  Agent 未运行${NC}"
        fi
    else
        # 尝试通过进程名停止
        AGENT_PID=$(pgrep -f "python.*agent.py" | head -1)
        if [ -n "$AGENT_PID" ]; then
            kill $AGENT_PID 2>/dev/null || true
            echo -e "${GREEN}✅ Agent 已停止${NC}"
        else
            echo -e "${YELLOW}⚠️  Agent 未运行${NC}"
        fi
    fi
    echo ""
}

# 启动所有服务
start_all() {
    echo ""
    start_backend
    start_agent

    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ 所有服务启动完成！${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    # 显示状态
    check_status

    echo -e "${BLUE}📝 下一步:${NC}"
    echo "  1. 访问 API 文档: http://localhost:$BACKEND_PORT/docs"
    echo "  2. 健康检查: curl http://localhost:$BACKEND_PORT/api/v1/health"
    echo "  3. 查看日志: tail -f $BACKEND_LOG"
    echo ""
}

# 停止所有服务
stop_all() {
    echo ""
    stop_agent
    stop_backend

    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ 所有服务已停止！${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# 重启所有服务
restart_all() {
    echo ""
    echo -e "${BLUE}🔄 重启所有服务...${NC}"
    echo ""
    stop_all
    sleep 2
    start_all
}

# 显示使用帮助
show_help() {
    cat << EOF
用法: ./dev.sh [command]

命令:
  start       启动所有服务（后端 + Agent）
  stop        停止所有服务
  restart     重启所有服务
  status      查看服务状态
  help        显示此帮助信息

示例:
  ./dev.sh start    # 启动所有服务
  ./dev.sh stop     # 停止所有服务
  ./dev.sh restart  # 重启所有服务
  ./dev.sh status   # 查看服务状态

快捷命令:
  ./dev.sh s        # 启动（简写）
  ./dev.sh s        # 停止（简写）
EOF
}

# 主程序
case "${1:-start}" in
    start|s)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        check_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
