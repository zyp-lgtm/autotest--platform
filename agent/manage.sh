#!/bin/bash
#
# Agent 管理脚本
# 用于启动、停止、重启和查看 Agent 状态
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
AGENT_PY="$SCRIPT_DIR/agent.py"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取 Agent PID
get_agent_pid() {
    if [ -f "$SCRIPT_DIR/.agent.pid" ]; then
        cat "$SCRIPT_DIR/.agent.pid"
    fi
}

# 检查 Agent 是否运行
is_agent_running() {
    local pid=$(get_agent_pid)
    if [ -n "$pid" ]; then
        if kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        else
            # PID 文件存在但进程不存在，清理
            rm -f "$SCRIPT_DIR/.agent.pid"
        fi
    fi

    # 检查是否有 agent.py 进程运行（无 PID 文件的情况）
    local pgrep_pid=$(pgrep -f "python.*agent.py" | head -1)
    if [ -n "$pgrep_pid" ]; then
        echo "$pgrep_pid"
        return 0
    fi

    return 1
}

# 启动 Agent
start_agent() {
    local pid=$(is_agent_running)
    if [ $? -eq 0 ]; then
        warn "Agent 已在运行 (PID: $pid)"
        return 1
    fi

    info "启动 Agent..."
    cd "$SCRIPT_DIR"
    nohup $PYTHON_BIN "$AGENT_PY" > agent.log 2>&1 &
    local new_pid=$!

    # 等待启动
    sleep 2

    if kill -0 $new_pid 2>/dev/null; then
        info "✓ Agent 已启动 (PID: $new_pid)"
        info "日志: $SCRIPT_DIR/agent.log"
        return 0
    else
        error "✗ Agent 启动失败"
        return 1
    fi
}

# 停止 Agent
stop_agent() {
    local pid=$(is_agent_running)
    if [ $? -ne 0 ]; then
        warn "Agent 未运行"
        return 1
    fi

    info "停止 Agent (PID: $pid)..."

    # 使用 Python 的 --stop 参数（推荐方式）
    cd "$SCRIPT_DIR"
    $PYTHON_BIN "$AGENT_PY" --stop

    sleep 1

    # 验证是否已停止
    if kill -0 "$pid" 2>/dev/null; then
        warn "使用 SIGKILL 强制停止..."
        kill -9 "$pid"
        rm -f "$SCRIPT_DIR/.agent.pid"
    fi

    info "✓ Agent 已停止"
    return 0
}

# 重启 Agent
restart_agent() {
    info "重启 Agent..."
    stop_agent
    sleep 1
    start_agent
}

# 查看 Agent 状态
status_agent() {
    echo ""
    echo "=== Agent 状态 ==="
    echo ""

    local pid=$(is_agent_running)
    if [ $? -eq 0 ]; then
        info "状态: 运行中"
        echo "  PID: $pid"
        echo "  启动时间: $(ps -p $pid -o lstart= 2>/dev/null || echo '未知')"
        echo "  CPU: $(ps -p $pid -o %cpu= 2>/dev/null || echo '0')%"
        echo "  内存: $(ps -p $pid -o %mem= 2>/dev/null || echo '0')%"
        echo ""
        echo "  最近日志:"
        if [ -f "$SCRIPT_DIR/agent.log" ]; then
            tail -5 "$SCRIPT_DIR/agent.log" | sed 's/^/    /'
        fi
    else
        warn "状态: 未运行"
    fi

    echo ""
}

# 查看日志
logs_agent() {
    local lines=${1:-20}
    if [ -f "$SCRIPT_DIR/agent.log" ]; then
        tail -n "$lines" "$SCRIPT_DIR/agent.log"
    else
        warn "日志文件不存在: $SCRIPT_DIR/agent.log"
    fi
}

# 健康检查
health_agent() {
    info "运行系统健康检查..."
    echo ""

    if [ -f "$SCRIPT_DIR/health_check.py" ]; then
        $PYTHON_BIN "$SCRIPT_DIR/health_check.py"
    else
        error "健康检查脚本不存在: $SCRIPT_DIR/health_check.py"
        return 1
    fi
}

# 显示使用帮助
show_help() {
    cat << EOF
Agent 管理脚本

用法: $0 <command> [options]

命令:
    start       启动 Agent
    stop        停止 Agent
    restart     重启 Agent
    status      查看 Agent 状态
    logs [n]    查看最近 n 行日志 (默认 20 行)
    health      运行系统健康检查
    help        显示此帮助信息

环境变量:
    PYTHON_BIN  Python 可执行文件路径 (默认: python3)

示例:
    $0 start           # 启动 Agent
    $0 status          # 查看状态
    $0 logs 50         # 查看最近 50 行日志
    $0 health          # 健康检查
    PYTHON_BIN=python3.11 $0 start  # 使用指定 Python 版本

EOF
}

# 主函数
main() {
    local command="${1:-help}"

    case "$command" in
        start)
            start_agent
            ;;
        stop)
            stop_agent
            ;;
        restart)
            restart_agent
            ;;
        status)
            status_agent
            ;;
        logs)
            logs_agent "${2:-20}"
            ;;
        health)
            health_agent
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "未知命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
