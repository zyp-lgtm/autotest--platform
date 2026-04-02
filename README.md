# 测试自动化平台 MVP

关键字驱动测试自动化平台，支持 API 和 UI 测试。

## 功能特性

- 🎯 **关键字驱动** - 可复用的系统和业务关键字
- 📊 **四层结构** - 任务 → 场景 → 用例 → 步骤
- 🔀 **类型分离** - UI 和接口测试独立管理
- 💾 **可视化数据** - 界面管理测试数据
- 📝 **变量系统** - 通过 `{变量名}` 引用
- 🔍 **详细日志** - 步骤级日志记录
- 🖼️ **截图支持** - 可配置 UI 步骤截图
- 📈 **结构化报告** - 完整的测试报告

## 快速开始

```bash
# 克隆仓库
git clone <repo-url>
cd test-platform

# 复制环境文件
cp .env.example .env

# 启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 访问前端
open http://localhost:3000

# 访问后端 API 文档
open http://localhost:8000/docs
```

## 技术栈

- 后端: Python 3.11+、FastAPI、SQLAlchemy、PostgreSQL、Redis
- 前端: React 19、TypeScript、Vite、Tailwind CSS
- 测试: pytest、Playwright、requests
- 基础设施: Docker、Docker Compose

## 开发指南

```bash
# 后端开发
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端开发
cd frontend
npm install
npm run dev

# 运行测试
cd backend
pytest

# 种植系统关键字
python scripts/seed_keywords.py
```

## 项目结构

详见 [设计文档](docs/superpowers/specs/2026-04-02-test-automation-platform-design.md)。

## 许可证

MIT