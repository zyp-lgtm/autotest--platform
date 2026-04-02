# 测试自动化平台

一个支持 API 和 UI 自动化测试的关键字驱动测试平台。

## 快速开始

```bash
# 复制环境配置文件
cp .env.example .env

# 启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 访问前端
open http://localhost:3000

# 访问后端 API 文档
open http://localhost:8000/docs
```

## 技术栈

- 后端: Python + FastAPI
- 前端: React + TypeScript
- 数据库: PostgreSQL + Redis
- 测试: pytest + Playwright