# 错误分类系统集成文档

## 修改日期
2026-04-09

## 修改目的
完善直接执行路径（Direct Execution Path）的错误分类功能，确保所有执行路径都提供统一的错误建议。

## 修改内容

### 1. 文件修改
**文件**: `/Users/apple/aicode/.worktrees/test-platform/backend/app/services/executor.py`

### 2. 修改位置
**位置**: 异常处理程序（Exception Handler）
**行数**: 第 729-742 行

### 3. 修改前
```python
step_execution.error_message = str(e)
# 直接进入截图逻辑
```

### 4. 修改后
```python
step_execution.error_message = str(e)

# 使用错误分类器丰富异常信息
error_info = ErrorClassifier.enrich_error_info(str(e))
logger.info(f"异常分类: {error_info['category']}, 严重程度: {error_info['severity']}")

# 将错误分类信息添加到output中
if not step_execution.output:
    step_execution.output = {}
step_execution.output['error_category'] = error_info['category']
step_execution.output['error_severity'] = error_info['severity']
step_execution.output['error_suggestion'] = error_info['suggestion']

# 在日志中记录错误建议
suggestion = error_info['suggestion']
logger.info(f"💡 异常建议: {suggestion['title']} - {suggestion['description']}")
```

## 功能说明

### 1. 执行路径覆盖
现在**所有执行路径**都包含错误分类：

#### ✅ Agent 执行路径
- **位置**: `_execute_via_agent` 方法
- **状态**: 已实现（之前完成）

#### ✅ 直接执行路径 - 关键字失败
- **位置**: `_execute_step` 方法，第 616-640 行
- **触发条件**: `result.get("success") == False`
- **状态**: 已实现（之前完成）

#### ✅ 直接执行路径 - 异常捕获（本次修复）
- **位置**: `_execute_step` 方法，第 729-742 行
- **触发条件**: 发生未预期的 Python 异常
- **状态**: **本次修复完成**

### 2. 错误分类类型
系统支持 8 种错误类型：

| 错误类型 | 严重程度 | 示例 |
|---------|---------|------|
| timeout | medium | Timeout waiting for selector |
| element_not_found | high | Element not found: #submit |
| network | high | Network error: ECONNREFUSED |
| assertion | medium | AssertionError: Expected 200 |
| script | critical | SyntaxError: invalid syntax |
| browser | critical/high | Browser crashed: SIGSEGV |
| permission | high | Permission denied: /var/log |
| unknown | medium | Unknown error occurred |

### 3. 前端展示
错误信息会在以下位置展示：

#### 1. 步骤详情组件
- **组件**: `StepDetail.tsx`
- **显示内容**:
  - 错误消息（红色背景）
  - 错误严重程度（徽章）
  - 错误建议（蓝色背景）
    - 标题
    - 描述
    - 解决方案列表

#### 2. 执行日志
- **显示内容**:
  - 错误分类信息
  - 错误严重程度
  - 建议标题和描述

## 测试验证

### 1. 后端服务状态
```bash
# 检查健康状态
curl http://localhost:8000/api/v1/health

# 结果: ✅ Backend is healthy
```

### 2. ErrorClassifier 功能测试
```bash
# 测试命令
cd /Users/apple/aicode/.worktrees/test-platform/backend
python3 -c "
from app.services.error_classifier import ErrorClassifier

# 测试不同错误类型
test_errors = [
    'Timeout waiting for selector',
    'Element not found: #submit',
    'Network error: ECONNREFUSED',
    'AssertionError: Expected 200',
    'SyntaxError: invalid syntax',
    'Browser crashed: SIGSEGV',
    'Permission denied: /var/log',
    'Unknown error'
]

for error_msg in test_errors:
    enriched = ErrorClassifier.enrich_error_info(error_msg)
    print(f'{error_msg[:30]}... → {enriched[\"category\"]} ({enriched[\"severity\"]})')
"
```

### 3. 集成测试
运行一个测试任务，验证失败步骤是否包含错误分类信息：
1. 访问前端：http://localhost:3000
2. 执行一个测试任务
3. 查看失败步骤的详情
4. 验证是否显示：
   - ✅ 错误消息
   - ✅ 错误严重程度徽章
   - ✅ 错误建议（标题 + 描述 + 解决方案）

## 数据库结构

### StepExecution 表
```sql
-- error_message 字段（已存在）
error_message TEXT

-- output 字段（JSON，已存在）
output JSON DEFAULT '{}'

-- output 包含的错误分类信息：
{
  "error_category": "timeout",           -- 错误类别
  "error_severity": "medium",            -- 严重程度
  "error_suggestion": {                  -- 建议信息
    "title": "超时错误",
    "description": "操作在规定时间内未完成",
    "solutions": [
      "1. 增加等待时间",
      "2. 检查网络连接",
      "3. 优化等待策略"
    ]
  }
}
```

## API 响应示例

### GET /api/v1/executions/{execution_id}
```json
{
  "id": "b716ef75-3bb6-4ee8-acbb-ee41a86eaa9e",
  "scenario_executions": [
    {
      "case_executions": [
        {
          "step_executions": [
            {
              "step_name": "点击按钮",
              "result": "fail",
              "error_message": "Timeout waiting for selector",
              "output": {
                "error_category": "timeout",
                "error_severity": "medium",
                "error_suggestion": {
                  "title": "超时错误",
                  "description": "操作在规定时间内未完成",
                  "solutions": [
                    "1. 增加等待时间：在参数中设置更长的timeout值",
                    "2. 检查网络连接：确认网络延迟是否过高"
                  ]
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## 影响范围

### 1. 后端服务
- ✅ 代码修改完成
- ✅ 测试验证通过
- ✅ 服务已重启

### 2. 前端展示
- ✅ StepDetail 组件已实现
- ✅ 支持错误分类展示
- ✅ 支持建议列表显示

### 3. 用户体验
- ✅ 所有执行路径统一错误提示
- ✅ 智能错误诊断
- ✅ 具体解决方案建议

## 后续建议

### 短期（已完成）
- ✅ Agent 执行路径错误分类
- ✅ 直接执行路径关键字失败错误分类
- ✅ 直接执行路径异常错误分类（本次修复）

### 中期（建议）
- [ ] 添加错误统计和趋势分析
- [ ] 实现错误知识库搜索
- [ ] 支持自定义错误分类规则
- [ ] 添加错误自动修复建议

### 长期（建议）
- [ ] AI 辅助错误诊断
- [ ] 基于历史数据的错误预测
- [ ] 自动化问题修复

## 总结

本次修改完成了**直接执行路径异常处理**的错误分类集成，确保了：

1. ✅ **统一性**: 所有执行路径都提供错误分类和建议
2. ✅ **完整性**: 覆盖关键字失败和异常捕获两种场景
3. ✅ **可用性**: 前端组件已支持完整展示
4. ✅ **可靠性**: 经过测试验证，功能正常

**状态**: ✅ 完成
**测试状态**: ✅ 通过
**部署状态**: ✅ 已部署

---

*最后更新: 2026-04-09*
*作者: Claude Code*
*版本: 1.0*
