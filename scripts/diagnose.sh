#!/bin/bash

####################################################################
# 测试平台 - 诊断脚本
#
# 用于排查本地浏览器连接问题
####################################################################

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "  测试平台 - 本地浏览器诊断"
echo "=========================================="
echo ""

# 1. 检查 Chrome 是否安装
echo -n "1. 检查 Google Chrome 安装..."
if [ -d "/Applications/Google Chrome.app" ]; then
    echo -e " ${GREEN}✓ 已安装${NC}"
else
    echo -e " ${RED}✗ 未安装${NC}"
    echo "   请安装 Google Chrome:"
    echo "   brew install --cask google-chrome"
    echo ""
    exit 1
fi

# 2. 检查 Chrome 进程
echo -n "2. 检查 Chrome 进程..."
CHROME_PIDS=$(pgrep -f "Google Chrome" | grep -v grep)
if [ -n "$CHROME_PIDS" ]; then
    echo -e " ${GREEN}✓ 运行中 (PID: $CHROME_PIDS)${NC}"
else
    echo -e " ${YELLOW}○ 未运行${NC}"
fi

# 3. 检查端口 9222
echo -n "3. 检查端口 9222..."
if lsof -i :9222 > /dev/null 2>&1; then
    echo -e " ${GREEN}✓ 监听中${NC}"
    lsof -i :9222 | grep LISTEN
else
    echo -e " ${RED}✗ 未监听${NC}"
    echo "   请运行: ./scripts/start-local-browser.sh"
    echo ""
fi

# 4. 检查守护进程
echo -n "4. 检查浏览器守护进程..."
if [ -f "/tmp/chrome-daemon.pid" ]; then
    DAEMON_PID=$(cat /tmp/chrome-daemon.pid)
    if ps -p $DAEMON_PID > /dev/null 2>&1; then
        echo -e " ${GREEN}✓ 运行中 (PID: $DAEMON_PID)${NC}"
    else
        echo -e " ${YELLOW}○ PID 文件存在但进程不存在${NC}"
    fi
else
    echo -e " ${YELLOW}○ 未运行${NC}"
fi

# 5. 检查 Docker 容器
echo -n "5. 检查 Docker 容器..."
if command -v docker > /dev/null 2>&1; then
    BACKEND_RUNNING=$(docker ps --filter "name=test-platform-backend" --format "{{.Status}}" 2>/dev/null)
    if [ -n "$BACKEND_RUNNING" ]; then
        echo -e " ${GREEN}✓ 运行中${NC}"
        echo "   状态: $BACKEND_RUNNING"
    else
        echo -e " ${RED}✗ 未运行${NC}"
        echo "   请启动容器: cd docker && docker compose up -d"
    fi
else
    echo -e " ${YELLOW}○ Docker 未安装或未运行${NC}"
fi

# 6. 测试 Docker 访问宿主机
echo ""
echo "6. 测试 Docker 容器访问宿主机..."
if command -v docker > /dev/null 2>&1; then
    echo "   从容器内测试访问 host.docker.internal:9222..."
    docker exec test-platform-backend sh -c "nc -zv host.docker.internal 9222 2>&1" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "   ${GREEN}✓ 可以访问${NC}"
    else
        echo -e "   ${RED}✗ 无法访问${NC}"
        echo "   可能的原因："
        echo "   - Docker Desktop 未运行"
        echo "   - 防火墙阻止了连接"
    fi
else
    echo "   ${YELLOW}○ Docker 不可用，跳过测试${NC}"
fi

# 7. 检查代码挂载
echo ""
echo "7. 检查 Docker 代码挂载..."
if command -v docker > /dev/null 2>&1; then
    docker exec test-platform-backend ls -la /app/app/services/executor.py > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e " ${GREEN}✓ 代码已挂载${NC}"
    else
        echo -e " ${RED}✗ 代码未挂载${NC}"
        echo "   请检查 docker-compose.yml 中的 volumes 配置"
    fi
fi

# 8. 显示后端日志
echo ""
echo "8. 后端日志（最后 20 行）..."
if command -v docker > /dev/null 2>&1; then
    docker logs test-platform-backend --tail 20 2>&1 || echo "   无法获取日志"
else
    echo "   Docker 不可用"
fi

# 总结
echo ""
echo "=========================================="
echo "  诊断完成"
echo "=========================================="
echo ""

# 修复建议
echo "修复建议："
echo ""
echo "1. 启动本地浏览器服务："
echo "   ./scripts/start-local-browser.sh"
echo ""
echo "2. 重启 Docker 容器（应用代码更改）："
echo "   cd docker && docker compose restart backend"
echo ""
echo "3. 查看 Docker 日志："
echo "   docker logs test-platform-backend -f"
echo ""
echo "4. 如果问题仍然存在，请提供："
echo "   - 执行任务的 task_id"
echo "   - Docker 日志输出"
echo "   - 本诊断脚本的完整输出"
echo ""
