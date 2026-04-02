# AI 驱动 UI 自动化测试设计文档

> **创建日期**: 2026-04-02
> **版本**: 1.0
> **状态**: 设计阶段

## 1. 概述

### 1.1 目标

在现有的关键字驱动测试自动化平台基础上，集成 AI 能力，实现通过自然语言描述测试目标，AI 自动理解、规划、适配并执行 UI 自动化测试。

### 1.2 核心价值

- **降低测试编写门槛**: 从需要编写代码/关键字 → 用自然语言描述测试需求
- **提升维护效率**: AI 自主适应页面变化，自动生成修复建议
- **增强测试智能**: AI 学习历史执行，持续优化元素定位和验证策略
- **控制使用成本**: 分层架构，大模型规划 + 小模型执行，成本可控

### 1.3 设计原则

- **插件化扩展**: AI 功能作为独立插件，不影响现有关键字系统
- **成本敏感**: 优先考虑本地模型和缓存，控制 API 调用成本
- **准确性优先**: 宁可慢一点，也要确保测试准确可靠
- **用户可控**: 所有关键决策点都提供用户确认机制

---

## 2. 系统架构

### 2.1 三层智能架构

```
┌─────────────────────────────────────────────────────────────────┐
│  规划层 (Planning Layer) - GPT-4 / Claude 3.5 Sonnet          │
│  • 理解用户测试目标                                             │
│  • 分解为抽象测试步骤                                           │
│  • 生成测试计划（action_type + description + intent）          │
│  • 一次性成本，高智能                                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  适配层 (Adaptation Layer) - GPT-4o-mini / Claude 3.5 Haiku   │
│  • 分析页面 DOM 结构                                             │
│  • 智能元素定位（多候选选择器）                                   │
│  • 动态策略调整                                                 │
│  • 每步操作，低成本，高频率                                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  执行层 (Execution Layer) - Playwright                        │
│  • 执行 UI 操作（navigate, click, fill）                        │
│  • 捕获页面状态（截图、DOM、日志）                                │
│  • 验证操作结果                                                 │
│  • 零 AI 成本，纯代码执行                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 学习系统

```
┌─────────────────────────────────────────────────────────────────┐
│                    页面学习历史 (Page Learning)                  │
│  • 元素映射缓存 (element_mappings)                               │
│  • 成功验证模式 (verification_patterns)                          │
│  • 成功/失败统计 (success/failure counts)                        │
│  • 页面签名检测 (page_signature for change detection)             │
└─────────────────────────────────────────────────────────────────┘
                            ↑
                            │ 每次执行后更新
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    适配层优化                                   │
│  • 复用历史成功的选择器                                           │
│  • 根据失败统计调整选择策略                                       │
│  • 页面变化时自动更新映射                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 与现有系统集成

```
┌─────────────────────────────────────────────────────────────┐
│         现有关键字驱动系统 (保持不变)                        │
│  • UITask / UIScenario / UICase / UIStep                   │
│  • 系统关键字 (NAVIGATE, CLICK, INPUT, WAIT_FOR_ELEMENT)    │
│  • 测试数据管理 ({variable_name} 引用)                     │
│  • KeywordEngine 执行引擎                                    │
└─────────────────────────────────────────────────────────────┘
              ↑
              │ AI 测试执行成功后可转换为关键字
              │
┌─────────────────────────────────────────────────────────────┐
│         AI 测试插件 (新增模块)                              │
│  • AITestTask: AI 测试任务                                   │
│  • AIAbstractStep: 抽象步骤                                  │
│  • PageLearning: 页面学习历史                                 │
│  • AIService: AI 模型管理和服务                               │
│  • AIModelUsage: 成本追踪                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型

### 3.1 核心数据表

```python
# AI 测试任务
class AITestTask(Base):
    __tablename__ = "ai_test_tasks"

    # 基础字段
    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id"))

    # 输入
    test_goal = Column(Text, nullable=False)  # 用户测试目标
    input_type = Column(String(20))  # "text", "document", "conversation"
    input_metadata = Column(JSON)  # 文档路径、对话历史等

    # 规划层输出
    abstract_plan = Column(JSON)  # 抽象测试计划
    planning_model = Column(String(50))
    planning_tokens = Column(Integer)

    # 执行状态
    status = Column(String(20))  # "planning", "adapting", "executing", "completed", "failed"
    execution_result = Column(JSON)

    # 转换为关键字
    converted_to_keyword = Column(Boolean, default=False)
    keyword_task_id = Column(UUID, ForeignKey("ui_tasks.id"))

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

# 抽象步骤（规划层输出）
class AIAbstractStep(Base):
    __tablename__ = "ai_abstract_steps"

    id = Column(UUID, primary_key=True)
    task_id = Column(UUID, ForeignKey("ai_test_tasks.id"))

    # 抽象描述
    step_order = Column(Integer)
    action_type = Column(String(50))  # "navigate", "interact", "verify", "extract"
    description = Column(Text)
    intent = Column(Text)
    expected_outcome = Column(Text)

    # 适配层输出
    concrete_selectors = Column(JSON)  # {"primary": "...", "fallbacks": [...]}
    adaptation_strategy = Column(String(50))

    # 执行结果
    execution_status = Column(String(20))
    actual_selector_used = Column(String(500))
    execution_time_ms = Column(Integer)

    created_at = Column(DateTime, default=func.now())

# 页面学习历史
class PageLearning(Base):
    __tablename__ = "page_learning"

    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id"))

    # 页面识别
    url_pattern = Column(String(500))
    page_signature = Column(Text)  # DOM 结构哈希，用于检测变化

    # 学习内容
    element_mappings = Column(JSON)  # {"login_button": ["#login", ".btn-primary"]}
    verification_patterns = Column(JSON)  # {"login_success": [".user-profile"]}

    # 统计
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_seen_at = Column(DateTime, default=func.now())

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

# AI 模型使用记录（成本追踪）
class AIModelUsage(Base):
    __tablename__ = "ai_model_usage"

    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id"))

    # 模型信息
    model_name = Column(String(50))  # "gpt-4", "claude-3.5-sonnet", "llama3.2:3b"
    layer = Column(String(20))  # "planning", "adapter", "verification"

    # Token 统计
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost_usd = Column(Float)

    # 请求信息
    request_type = Column(String(50))
    success = Column(Boolean)
    error_message = Column(Text)

    created_at = Column(DateTime, default=func.now())
```

### 3.2 扩展现有模型

```python
# 在 Keyword 模型中添加
class Keyword(Base):
    # ... 现有字段 ...

    # AI 相关字段
    generated_by_ai = Column(Boolean, default=False)
    ai_task_id = Column(UUID, ForeignKey("ai_test_tasks.id"))
    confidence_score = Column(Float)  # AI 置信度
    auto_generated_selectors = Column(JSON)  # AI 生成的选择器
```

---

## 4. API 接口设计

### 4.1 核心 API 端点

```python
# AI 测试任务管理
POST   /api/v1/ai/tests                    # 创建 AI 测试任务
GET    /api/v1/ai/tests/{task_id}          # 获取任务详情
POST   /api/v1/ai/tests/{task_id}/execute  # 执行测试
POST   /api/v1/ai/tests/{task_id}/convert  # 转换为关键字
GET    /api/v1/ai/tests/{task_id}/logs     # 获取执行日志

# 修复与维护
GET    /api/v1/ai/tests/{task_id}/repair-suggestions  # 获取修复建议
POST   /api/v1/ai/tests/{task_id}/confirm-repair      # 应用修复建议

# 成本与统计
GET    /api/v1/ai/projects/{project_id}/costs  # 成本统计
GET    /api/v1/ai/projects/{project_id}/usage  # 使用报告

# 对话接口（可选）
POST   /api/v1/ai/chat/start               # 开始对话会话
POST   /api/v1/ai/chat/{session_id}/message # 发送消息

# WebSocket
WS     /ws/ai-tests/{task_id}/execute     # 实时执行进度推送
```

### 4.2 关键接口详解

#### 创建 AI 测试任务

**请求**
```json
POST /api/v1/ai/tests
{
  "project_id": "uuid",
  "test_goal": "验证用户登录功能，包括成功登录和密码错误提示",
  "input_type": "text",
  "input_metadata": {
    "priority": "high",
    "test_data_ids": ["uuid1", "uuid2"]
  }
}
```

**响应**
```json
{
  "id": "uuid",
  "status": "planning",
  "abstract_plan": {
    "steps": [
      {
        "step_order": 1,
        "action_type": "navigate",
        "description": "导航到登录页面",
        "intent": "准备登录",
        "expected_outcome": "登录页加载完成"
      }
    ],
    "verification_points": ["用户信息显示", "错误提示显示"],
    "estimated_complexity": "medium"
  },
  "estimated_cost": 0.18,
  "estimated_time": "2-3 分钟"
}
```

#### 转换为关键字

**请求**
```json
POST /api/v1/ai/tests/{task_id}/convert
{
  "keyword_task_name": "用户登录功能验证",
  "save_selectors": true,
  "include_screenshots": false
}
```

**响应**
```json
{
  "keyword_task_id": "uuid",
  "created_scenario_count": 1,
  "created_case_count": 2,
  "created_step_count": 6,
  "conversion_summary": {
    "total_steps": 6,
    "successful_conversions": 6,
    "manual_review_required": 0
  }
}
```

---

## 5. 核心工作流程

### 5.1 完整执行流程

```
1. 用户输入测试目标
   ↓
2. 规划层 (GPT-4/Claude)
   - 理解目标
   - 生成抽象步骤 (6-10步)
   - 成本: ~$0.05
   ↓
3. 循环执行每个抽象步骤
   For each abstract_step:

   3.1 适配层 (GPT-4o-mini/Claude Haiku)
       - 查询学习历史
       - 分析页面 DOM
       - 生成具体选择器
       - 成本: ~$0.015/步
       ↓
   3.2 执行层 (Playwright)
       - 尝试 primary 选择器
       - 失败则尝试 fallbacks
       - 捕获状态和截图
       ↓
   3.3 验证层 (GPT-4o-mini)
       - 分析操作结果
       - 确认是否符合预期
       - 成本: ~$0.01/验证点
       ↓
   3.4 更新学习历史
       - 记录成功/失败
       - 更新元素映射
   ↓
4. 生成执行报告
   - 通过 WebSocket 推送进度
   - 汇总成功/失败统计
   - 提供修复建议（如有失败）
   ↓
5. 用户确认后转换为关键字
   - 创建 UITask/UIScenario/UICase/UIStep
   - 标记 AI 生成来源
   - 保存验证过的选择器
```

### 5.2 智能降级流程

```
步骤执行失败
   ↓
AI 分析失败原因
   ↓
生成修复建议 (2-3个方案)
   ↓
┌─────────────┬─────────────┬─────────────┐
│ 用户选择    │ 自动重试    │ 智能降级    │
│ 应用建议    │ 其他选择器  │ 跳过继续    │
└─────────────┴─────────────┴─────────────┘
```

### 5.3 学习优化流程

```
执行 N 次后
   ↓
统计分析
   - 成功率 < 70%: 标记为"不稳定"
   - 成功率 > 90%: 标记为"稳定"
   ↓
页面变化检测
   - page_signature 变化 > 30%
   - 触发重新适配
   ↓
自动优化
   - 淘汰失败率高的选择器
   - 晋升成功率高的选择器为 primary
   - 更新 PageLearning 表
```

---

## 6. AI 模型接入

### 6.1 支持的模型提供商

| 提供商 | 规划层 | 适配层 | 验证层 | 输入成本 | 输出成本 |
|--------|--------|--------|--------|----------|----------|
| OpenAI | GPT-4o | GPT-4o-mini | GPT-4o-mini | $5/1M | $15/1M |
| Anthropic | Claude 3.5 Sonnet | Claude 3.5 Haiku | Claude 3.5 Haiku | $3/1M | $15/1M |
| 本地 | - | Llama 3.2 3B | Llama 3.2 3B | $0 | $0 |

### 6.2 模型选择策略

```python
# 配置文件
AI_MODEL_STRATEGY = {
    "planning": {
        "primary": "anthropic",      # Claude 3.5 Sonnet
        "fallback": "openai",        # GPT-4o
        "local_alternative": None    # 规划层不使用本地模型
    },
    "adapter": {
        "primary": "openai",         # GPT-4o-mini
        "fallback": "local",         # Llama 3.2 3B
        "cost_optimization": True    # 启用成本优化
    },
    "verification": {
        "primary": "openai",         # GPT-4o-mini
        "fallback": "anthropic",     # Claude 3.5 Haiku
        "simple_cases": "local"      # 简单验证用本地模型
    }
}
```

### 6.3 Prompt 模板

#### 规划层 Prompt

```
你是一个测试规划专家。请理解用户的测试目标，将其分解为具体的测试步骤。

测试目标：{test_goal}

上下文：
- 项目类型：{project_type}
- 可用测试数据：{test_data}
- 约束条件：{constraints}

请输出 JSON 格式：
{
  "steps": [
    {
      "step_order": 1,
      "action_type": "navigate|interact|verify|extract",
      "description": "步骤描述",
      "intent": "测试意图",
      "expected_outcome": "期望结果"
    }
  ],
  "verification_points": ["验证点列表"],
  "estimated_complexity": "low|medium|high"
}
```

#### 适配层 Prompt

```
你是一个 Web 自动化测试专家。将抽象步骤转换为具体的浏览器操作。

抽象步骤：{abstract_step}

页面信息：
URL: {url}
DOM 结构：{dom_tree}
可交互元素：{interactive_elements}
历史成功选择器：{learning_history}

请输出 JSON：
{
  "concrete_selectors": {
    "primary": "推荐选择器",
    "fallbacks": ["备用1", "备用2"]
  },
  "action": "fill|click|select",
  "parameters": {"value": "..."},
  "confidence": 0.95,
  "reasoning": "选择理由"
}
```

#### 验证层 Prompt

```
判断实际结果是否符合预期。

预期：{expected_outcome}

实际状态：
URL: {actual_url}
页面标题：{title}
可见元素：{visible_elements}
截图描述：{screenshot_desc}

请输出 JSON：
{
  "passed": true/false,
  "confidence": 0.95,
  "reasoning": "判断理由",
  "suggestions": ["如失败的修复建议"]
}
```

### 6.4 成本控制机制

```python
class CostController:
    """成本控制器"""

    MAX_COST_PER_TEST = 1.0  # 单次测试最大成本
    MONTHLY_BUDGET = 50.0    # 月度预算

    async def check_budget(self, project_id: str) -> bool:
        """检查预算是否充足"""
        current_cost = await self.get_monthly_cost(project_id)
        return current_cost < self.MONTHLY_BUDGET

    async def estimate_test_cost(
        self,
        test_goal: str,
        estimated_steps: int
    ) -> float:
        """预估测试成本"""
        planning_cost = 0.05
        adapter_cost = estimated_steps * 0.015
        verification_cost = (estimated_steps // 2) * 0.01
        return planning_cost + adapter_cost + verification_cost

    def should_use_local_model(
        self,
        layer: str,
        complexity: str
    ) -> bool:
        """决策是否使用本地模型"""
        if layer == "planning":
            return False  # 规划层不用本地

        if complexity == "low":
            return True   # 简单任务用本地

        if self.current_cost > 0.8 * self.MAX_COST_PER_TEST:
            return True   # 即将超预算时用本地

        return False
```

---

## 7. 前端交互设计

### 7.1 页面结构

1. **AI 测试创建页面** (`/ai/tests/create`)
   - 输入模式选择：文本/文档/对话
   - 自然语言输入框
   - 成本预估展示
   - 生成的测试计划展示
   - 立即执行/保存为关键字按钮

2. **执行监控页面** (`/ai/tests/{id}/execute`)
   - 实时进度条
   - 日志流输出
   - 截图展示
   - 当前步骤指示
   - 执行时间统计

3. **修复建议页面** (`/ai/tests/{id}/repair`)
   - 失败原因分析
   - AI 生成的修复建议（2-3个方案）
   - 置信度显示
   - 应用按钮
   - 智能降级选项

4. **成本监控页面** (`/ai/projects/{id}/costs`)
   - 成本统计卡片
   - 月度预算进度
   - 按层级分解
   - 7天趋势图表
   - 使用详情列表

### 7.2 WebSocket 实时推送

```javascript
// 建立连接
const ws = new WebSocket(`ws://localhost:8000/ws/ai-tests/${taskId}/execute`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'step_start':
      updateProgress(message.step, message.description);
      break;

    case 'step_success':
      addLog('SUCCESS', `步骤 ${message.step} 完成`);
      addScreenshot(message.screenshot);
      break;

    case 'step_fail':
      addLog('ERROR', `步骤 ${message.step} 失败: ${message.error}`);
      showRepairSuggestions(message.suggestions);
      break;

    case 'test_complete':
      showResult(message.result, message.summary);
      break;
  }
};
```

### 7.3 成本可视化

```javascript
// 成本预算组件
<AICostMonitor
  projectId={projectId}
  budget={50.0}
  usedCost={18.45}
  breakdown={{
    planning: 8.20,
    adapter: 7.62,
    verification: 2.63
  }}
/>
```

---

## 8. 实现优先级

### 8.1 MVP 阶段 (2-3 个月)

**Phase 1: 核心框架 (4 周)**
- [ ] AI 模型管理器 (AIService, Provider 抽象)
- [ ] 数据模型创建 (AITestTask, AIAbstractStep, PageLearning)
- [ ] 规划层实现 (GPT-4/Claude 集成)
- [ ] 适配层实现 (GPT-4o-mini 集成)
- [ ] 执行层集成 (Playwright)

**Phase 2: 学习系统 (3 周)**
- [ ] PageLearning 实现
- [ ] 选择器缓存机制
- [ ] 成功/失败统计
- [ ] 自动优化逻辑

**Phase 3: API 和前端 (4 周)**
- [ ] 核心 API 端点
- [ ] WebSocket 实时推送
- [ ] AI 测试创建页面
- [ ] 执行监控页面
- [ ] 成本统计页面

**Phase 4: 修复和维护 (3 周)**
- [ ] 失败分析机制
- [ ] 修复建议生成
- [ ] 用户确认流程
- [ ] 智能降级策略

### 8.2 优化阶段 (2-3 个月)

**Phase 5: 本地模型 (4 周)**
- [ ] Ollama/vLLM 集成
- [ ] Llama 3.2 模型部署
- [ ] 成本优化策略
- [ ] 混合模型路由

**Phase 6: 高级特性 (4 周)**
- [ ] 文档导入解析
- [ ] 对话式测试规划
- [ ] 多模态理解（截图分析）
- [ ] 批量测试执行

**Phase 7: 生态集成 (4 周)**
- [ ] CI/CD 集成
- [ ] 报告导出
- [ ] 第三方平台集成
- [ ] API 开放平台

### 8.3 实施时间表

```
Month 1-2:  MVP 核心功能
Month 3-4:  优化和本地模型
Month 5-6:  高级特性和集成
```

---

## 9. 风险与挑战

### 9.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI API 不稳定 | 高 | 实现重试机制、多提供商支持 |
| 成本超预算 | 中 | 实时成本追踪、预算熔断机制 |
| 元素定位不准确 | 高 | 学习历史、多候选选择器 |
| 页面结构变化大 | 中 | 定期重新适配、智能降级 |
| 本地模型性能差 | 低 | 作为备选方案，非主要路径 |

### 9.2 成本控制

**策略 1: 智能缓存**
- 规划结果缓存 7 天
- 适配层结果缓存 24 小时
- 相同测试目标复用计划

**策略 2: 批处理**
- 多个测试步骤合并适配请求
- 减少 API 调用次数

**策略 3: 本地优先**
- 简单页面用本地模型
- 复杂页面用云端模型

**策略 4: 用户控制**
- 成本预警机制
- 预算超限时暂停执行
- 提供成本估算供用户决策

### 9.3 数据隐私

- 测试数据可能包含敏感信息
- 截图和 DOM 树可能泄露业务逻辑
- **解决方案**:
  - 脱敏处理后再发送给 AI
  - 提供"私有化部署"选项（本地模型）
  - 用户可选择数据保留策略

---

## 10. 成功指标

### 10.1 技术指标

- **准确率**: AI 生成测试的准确率 ≥ 85%
- **成功率**: 首次执行成功率 ≥ 75%
- **自修复率**: 失败后自动修复成功率 ≥ 60%
- **响应时间**: 规划层 < 10 秒，适配层 < 3 秒/步

### 10.2 成本指标

- **单次测试成本**: ≤ $0.20（6 步测试）
- **月度成本**: ≤ $50（中小团队）
- **成本节省**: 相比手工编写降低 ≥ 30%

### 10.3 用户指标

- **时间节省**: 从 30 分钟编写测试 → 5 分钟描述需求
- **学习曲线**: 15 分钟上手
- **满意度**: NPS ≥ 50

---

## 11. 未来扩展

### 11.1 短期 (6-12 个月)

- **API 测试支持**: 扩展到 API 自动化测试
- **移动端支持**: iOS/Android Appium 集成
- **性能测试**: 集成 Locust 进行性能测试
- **视觉回归**: 截图对比和视觉差异检测

### 11.2 长期 (12-24 个月)

- **自主探索**: AI 自主发现测试场景
- **缺陷分析**: AI 分析失败根因并生成 Bug 报告
- **测试优化**: AI 建议测试用例优化和去重
- **智能报告**: 自动生成测试报告和趋势分析

---

## 12. 附录

### 12.1 配置示例

```yaml
# config/ai.yaml
ai:
  enabled: true

  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      models:
        planning: "gpt-4o"
        adapter: "gpt-4o-mini"
        verification: "gpt-4o-mini"

    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
      models:
        planning: "claude-3-5-sonnet-20241022"
        adapter: "claude-3-5-haiku-20241022"
        verification: "claude-3-5-haiku-20241022"

    local:
      base_url: "http://localhost:11434"
      models:
        adapter: "llama3.2:3b"
        verification: "llama3.2:3b"

  cost_control:
    max_cost_per_test: 1.0
    monthly_budget: 50.0
    alert_threshold: 0.8  # 80% 时预警

  cache:
    planning_ttl: 604800  # 7 天
    adapter_ttl: 86400    # 24 小时

  learning:
    enabled: true
    min_samples: 5        # 至少 5 次后才学习
    success_threshold: 0.9  # 90% 成功率才标记为稳定
```

### 12.2 交互原型

可交互的原型已创建在: `/docs/ai-test-prototype.html`

包含 4 个主要页面：
- AI 测试创建
- 执行监控
- 修复建议
- 成本监控

### 12.3 术语表

| 术语 | 定义 |
|------|------|
| 规划层 | AI 理解测试目标并生成抽象步骤的层级 |
| 适配层 | AI 将抽象步骤转换为具体操作的层级 |
| 执行层 | Playwright 执行 UI 操作的层级 |
| 抽象步骤 | 描述"做什么"但不包含具体选择器的步骤 |
| 具体选择器 | 实际用于定位元素的选择器（如 #username） |
| 学习历史 | 页面元素映射和验证模式的累积记录 |
| 智能降级 | 跳过失败步骤继续执行的策略 |

---

## 文档变更历史

| 版本 | 日期 | 变更说明 | 作者 |
|------|------|----------|------|
| 1.0 | 2026-04-02 | 初始版本 | AI 设计团队 |
