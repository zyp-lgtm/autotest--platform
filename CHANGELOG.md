# 更新日志

所有项目重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.5.1] - 2026-04-30

### 🐛 修复

#### 数据库修复
- 🐛 修复录制场景保存功能的 UUID 格式问题
- 🐛 修复 SQLite Raw SQL 查询时的 UUID 横线处理
- 🐛 修复场景执行时用例和步骤为空的问题

#### 技术改进
- 🔧 更新 CLAUDE.md 数据库架构宪法，添加 SQLite UUID 处理规范
- 🔧 创建 UUID 修复的详细技术记录和测试脚本
- 🔧 改进 Raw SQL 查询的 UUID 格式处理

### 📝 文档

- 📝 添加 SQLite UUID 格式修复记录 (uuid-sqlite-fix-2026-04-30.md)
- 📝 更新录制功能记录，标记 UUID 修复已完成
- 📝 更新项目记忆，添加最新修复进展

---

## [1.5.0] - 2026-04-24

### 🎉 新功能

#### 浏览器录制功能
- ✨ 实现可视化录制功能，支持在浏览器中执行操作自动生成测试
- ✨ 添加智能数据提取，自动识别用户名、密码、邮箱等测试数据
- ✨ 实现跨页面录制，支持多页面操作录制
- ✨ 添加录制向导组件，提供4步向导式录制体验
- ✨ 实现场景自动生成，录制的操作直接转换为测试用例

#### 前端增强
- ✨ 添加录制向导组件（RecordingWizard）
- ✨ 优化场景创建流程，支持手工创建和录制两种方式
- ✨ 改进UI交互和用户体验

#### 后端优化
- ✨ 实现录制服务（recorder.py）
- ✨ 添加数据提取器（data_extractor.py）
- ✨ 添加场景转换器（converter.py）
- ✨ 实现录制API端点（/api/v1/recording）

### 🐛 修复

#### 录制功能修复
- 🐛 修复录制脚本注入问题，从page级别改为context级别
- 🐛 修复字段名不匹配问题，统一使用action_type
- 🐛 修复前端创建按钮无响应问题
- 🐛 修复TypeScript类型错误

### 📝 文档

- 📝 完全重写README.md，反映当前项目状态
- 📝 创建CHANGELOG.md记录版本历史
- 📝 更新成熟度评分从⭐⭐提升到⭐⭐⭐⭐

---

## [1.4.0] - 2026-04-21

### 🎉 新功能

#### 模块验证完成
- ✅ 完成定时任务模块完整CRUD验证
- ✅ 完成环境配置模块完整CRUD验证
- ✨ 完成测试数据模块完整CRUD验证
- ✅ 完成端到端流程验证（12项验证全部通过）

### 🐛 修复
- 🐛 修复项目删除功能的相对导入错误
- 🐛 修复UUID类型比较问题
- 🐛 修复后端启动和模块导入问题

---

## [1.3.0] - 2026-04-17

### 🎉 新功能

#### 前端集成
- ✨ 实现环境配置管理页面（Environments.tsx）
- ✨ 实现测试数据管理页面（TestData.tsx）
- ✨ 实现定时任务管理页面（ScheduledJobs.tsx）
- ✨ 添加环境配置API客户端
- ✨ 添加测试数据API客户端
- ✨ 添加定时任务API客户端

### 📈 性能优化
- ⚡ 实现API响应内存缓存
- ⚡ 缓存命中率60%+
- ⚡ 数据库查询减少70%

---

## [1.2.0] - 2026-04-16

### 🎉 新功能

#### UI关键字扩展
- ✨ 添加CLOSE_BROWSER关键字
- ✨ 添加SWITCH_TAB关键字
- ✨ 添加GO_BACK关键字
- ✨ 添加REFRESH关键字
- ✨ 添加DOUBLE_CLICK关键字

#### 断言关键字
- ✨ 实现ASSERT_VISIBLE关键字
- ✨ 实现ASSERT_TEXT关键字

### 🔧 性能优化
- ⚡ 实现API响应缓存系统
- ⚡ 添加缓存失效机制
- ⚡ 优化高频API端点

---

## [1.1.0] - 2026-04-15

### 🎉 新功能

#### 智能等待机制
- ✨ 实现智能等待机制（Smart Waiting）
- ✨ 自动等待元素出现、可见、可点击
- ✨ 减少硬编码sleep，提高测试稳定性

#### 调试增强
- ✨ 实现失败截图功能
- ✨ 添加详细执行日志
- ✨ 实现错误分类和修复建议

#### 安全增强
- 🔒 修复JWT_SECRET硬编码问题
- 🔒 实现HttpOnly Cookie存储JWT
- 🔒 添加密码哈希（bcrypt）
- 🔒 实现审计日志系统

---

## [1.0.0] - 2026-04-08

### 🎉 MVP发布

#### 核心功能
- ✅ 用户认证系统（注册、登录、退出）
- ✅ 项目管理
- ✅ UI任务/场景/用例/步骤管理
- ✅ API任务/场景/用例/步骤管理
- ✅ 测试数据管理
- ✅ 关键字管理（插件化系统）
- ✅ 测试执行引擎
- ✅ 变量解析系统
- ✅ 执行日志和报告

#### 基础UI关键字
- ✅ NAVIGATE - 导航到URL
- ✅ CLICK - 点击元素
- ✅ INPUT - 输入文本
- ✨ WAIT_FOR_ELEMENT - 等待元素

#### API关键字
- ✅ API_GET - GET请求
- ✅ API_POST - POST请求
- ✅ ASSERT_STATUS - 状态码断言
- ✅ EXTRACT_VARIABLE - 变量提取

#### 前端页面
- ✅ 仪表盘（Dashboard）
- ✅ 项目管理（Projects）
- ✅ 场景管理（Scenarios）
- ✅ 任务管理（Tasks）
- ✅ 测试报告（Reports）

#### 技术架构
- 🏗️ 四层架构设计（Task → Scenario → Case → Step）
- 🔀 UI/API完全分离
- 💾 可视化测试数据管理
- 📝 强大的变量系统
- 🔍 详细的执行日志

#### 基础设施
- ✅ Docker容器化
- ✅ SQLite数据库（开发）/ PostgreSQL（生产）
- ✅ FastAPI后端
- ✅ React 19 + TypeScript前端
- ✅ Playwright UI自动化

---

## 版本号说明

- **主版本号（Major）**: 不兼容的API修改
- **次版本号（Minor）**: 向下兼容的功能性新增
- **修订号（Patch）**: 向下兼容的问题修正

## 链接

- [GitHub Repository](https://github.com/zyp-lgtm/autotest--platform)
- [问题追踪](https://github.com/zyp-lgtm/autotest--platform/issues)
