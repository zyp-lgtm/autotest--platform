#!/bin/bash

####################################################################
# 完整的 Agent 测试脚本
####################################################################

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0;'

echo ""
echo "=========================================="
echo "  测试平台 - Agent 完整测试"
echo "=========================================="
echo ""

# 1. 检查 Docker
echo -n "1. 检查 Docker... "
if docker ps > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Docker 未运行${NC}"
    echo "请启动 Docker Desktop"
    exit 1
fi

# 2. 检查容器
echo -n "2. 检查后端容器... "
BACKEND_STATUS=$(docker ps --filter "name=test-platform-backend" --format "{{.Status}}" 2>/dev/null)
if [ -n "$BACKEND_STATUS" ]; then
    echo -e "${GREEN}✓ 运行中${NC} ($BACKEND_STATUS)"
else
    echo -e "${YELLOW}○ 未运行${NC}"
    echo "启动容器..."
    cd /Users/apple/aicode/.worktrees/test-platform/docker
    docker compose up -d
    echo "等待容器启动..."
    sleep 10
fi

# 3. 检查服务器健康
echo -n "3. 检查服务器健康... "
for i in {1..20}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        HEALTH=$(curl -s http://localhost:8000/health)
        echo "   $HEALTH"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${RED}✗ 超时${NC}"
        echo ""
        echo "查看日志:"
        docker logs test-platform-backend --tail 20
        exit 1
    fi
    echo -n "."
    sleep 2
done

# 4. 登录获取 token
echo ""
echo -n "4. 登录... "
TOKEN=$(curl -s 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-raw 'username=demo&password=demo123' | jq -r '.access_token' 2>/dev/null)

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ 登录失败${NC}"
    exit 1
fi

# 5. 检查 Agent API
echo ""
echo -n "5. 检查 Agent API... "
AGENTS=$(curl -s 'http://localhost:8000/api/v1/agents' \
  -H "Authorization: Bearer $TOKEN")

if [ $? -eq 0 ]; then
    AGENT_COUNT=$(echo "$AGENTS" | jq -r '.count // 0')
    echo -e "${GREEN}✓${NC} (已连接: $AGENT_COUNT 个 Agent)"
else
    echo -e "${RED}✗ API 不可用${NC}"
    exit 1
fi

# 6. 准备 Agent 测试
echo ""
echo "=========================================="
echo "  准备启动本地 Agent"
echo "=========================================="
echo ""

AGENT_DIR="/Users/apple/aicode/.worktrees/test-platform/agent"

# 检查 Agent 目录
if [ ! -d "$AGENT_DIR" ]; then
    echo -e "${RED}错误: Agent 目录不存在${NC}"
    exit 1
fi

echo "Agent 目录: $AGENT_DIR"
echo ""

# 检查依赖
echo "检查 Agent 依赖..."
cd "$AGENT_DIR"

if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "安装依赖..."
source venv/bin/activate
pip install -q -r requirements.txt

# 检查 Playwright
echo "检查 Playwright 浏览器..."
if ! playwright install chromium --dry-run > /dev/null 2>&1; then
    echo -e "${YELLOW}需要安装 Playwright 浏览器${NC}"
    echo "运行: playwright install chromium"
    echo ""
fi

echo -e "${GREEN}✓ 依赖就绪${NC}"
echo ""

# 7. 启动说明
echo "=========================================="
echo "  下一步：启动 Agent"
echo "=========================================="
echo ""
echo "在新的终端窗口中运行以下命令启动 Agent："
echo ""
echo -e "${BLUE}cd $AGENT_DIR${NC}"
echo -e "${BLUE}source venv/bin/activate${NC}"
echo -e "${BLUE}python3 agent.py --server ws://localhost:8000/agent${NC}"
echo ""
echo "或者使用启动脚本："
echo ""
echo -e "${BLUE}./scripts/start-agent.sh${NC}"
echo ""
echo "=========================================="
echo ""

# 8. 测试命令
echo "Agent 启动后，使用以下命令测试："
echo ""
echo "# 查看已连接的 Agent"
echo "curl 'http://localhost:8000/api/v1/agents' \\"
echo "  -H 'Authorization: Bearer $TOKEN' | jq"
echo ""
echo "# 下发测试任务（替换 AGENT_ID）"
echo "curl 'http://localhost:8000/api/v1/agents/dispatch' \\"
echo "  -H 'Authorization: Bearer $TOKEN' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  --data-raw '{"
echo "    \"agent_id\": \"YOUR_AGENT_ID\","
echo "    \"task_id\": \"test-001\","
echo "    \"browser_type\": \"chromium\","
echo "    \"headless\": false,"
echo "    \"steps\": ["
echo "      {\"action\": \"navigate\", \"parameters\": {\"url\": \"https://www.baidu.com\"}},"
echo "      {\"action\": \"screenshot\", \"parameters\": {\"path\": \"test.png\"}}"
echo "    ]"
echo "  }' | jq"
echo ""
