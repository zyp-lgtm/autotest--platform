# MVP 验证清单

## 环境验证

- [ ] Docker 服务启动正常
- [ ] 后端健康检查通过: `curl http://localhost:8000/health`
- [ ] 前端可访问: http://localhost:3000

## 后端验证

- [ ] API 文档可访问: http://localhost:8000/docs
- [ ] 系统关键字已种植: 9+ 个关键字
- [ ] 用户注册/登录功能正常

## 前端验证

- [ ] 仪表盘页面显示正常
- [ ] API 代理工作正常

## 数据库验证

- [ ] PostgreSQL 连接正常
- [ ] Redis 连接正常
- [ ] 表结构创建成功

## 集成测试

- [ ] 完整用户流程测试