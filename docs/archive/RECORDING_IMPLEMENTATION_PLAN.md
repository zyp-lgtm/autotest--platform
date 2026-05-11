# 录制功能完整实施计划

## 🎯 核心目标

在保持现有手工创建功能完全不变的前提下，增加录制创建分支，实现两种创建方式的完美融合。

---

## ✅ 已完成：基础框架（当前状态）

### 1. 场景创建方式选择界面
✅ 在场景管理页面添加了创建方式选择对话框
✅ 两种创建方式：手动创建 vs 录制创建
✅ 清晰的UI设计，帮助用户理解不同方式的用途

### 2. 录制向导界面框架
✅ 4步录制向导：录制准备 → 录制中 → 智能提取 → 预览调整
✅ 进度指示器和步骤导航
✅ 响应式界面设计

### 3. 数据结构设计
✅ 统一的场景数据模型（手动/录制完全相同）
✅ 录制会话数据结构
✅ 数据模式提取设计

---

## 📋 剩余实施阶段

### 阶段一：录制器后端服务（1-2周）

#### 1.1 录制器API服务
```python
# app/api/recording.py
from fastapi import APIRouter, BackgroundTasks
from app.services.recorder import BrowserRecorder

router = APIRouter(prefix="/recording", tags=["录制管理"])

@router.post("/start")
async def start_recording(request: RecordingStartRequest):
    """启动录制会话"""
    recorder = BrowserRecorder()
    session_id = await recorder.start_session(
        project_id=request.project_id,
        scenario_name=request.scenario_name
    )
    return {
        "session_id": session_id,
        "browser_url": recorder.get_browser_url(),
        "instructions": "请在打开的浏览器中执行您的测试流程"
    }

@router.post("/stop")
async def stop_recording(session_id: str):
    """停止录制并处理结果"""
    recorder = BrowserRecorder()
    result = await recorder.stop_session(session_id)
    return {
        "session_id": session_id,
        "actions_count": len(result.actions),
        "processing": True
    }

@router.get("/actions/{session_id}")
async def get_captured_actions(session_id: str):
    """实时获取捕获的操作（WebSocket替代方案）"""
    recorder = BrowserRecorder()
    actions = await recorder.get_captured_actions(session_id)
    return {"actions": actions}

@router.post("/extract-data")
async def extract_test_data(request: DataExtractionRequest):
    """智能提取测试数据"""
    extractor = DataExtractor()
    patterns = await extractor.extract_patterns(request.actions)
    return {"patterns": patterns}

@router.post("/generate-scenario")
async def generate_scenario(request: ScenarioGenerationRequest):
    """生成场景结构"""
    generator = ScenarioGenerator()
    scenario = await generator.generate_from_recording(
        actions=request.actions,
        data_patterns=request.data_patterns,
        project_id=request.project_id
    )
    return {"scenario": scenario}
```

#### 1.2 浏览器录制器服务
```python
# app/services/recorder.py
from playwright.async_api import async_playwright
import asyncio
from typing import Dict, List
from datetime import datetime

class BrowserRecorder:
    def __init__(self):
        self.sessions: Dict[str, RecordingSession] = {}

    async def start_session(self, project_id: str, scenario_name: str) -> str:
        """启动录制会话"""
        session_id = str(uuid.uuid4())

        # 启动Playwright浏览器
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--auto-open-devtools-for-tabs']
        )

        # 创建上下文和页面
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            record_video_dir=f"recordings/{session_id}"
        )

        page = await context.new_page()

        # 注入录制脚本
        await page.add_init_script("""
            window.__recording = {
                actions: [],
                captureAction: (action) => {
                    window.__recording.actions.push(action);
                }
            };

            // 监听各种事件
            document.addEventListener('click', (e) => {
                window.__recording.captureAction({
                    type: 'click',
                    selector: getSelector(e.target),
                    timestamp: Date.now()
                });
            }, true);

            document.addEventListener('input', (e) => {
                window.__recording.captureAction({
                    type: 'input',
                    selector: getSelector(e.target),
                    value: e.target.value,
                    timestamp: Date.now()
                });
            }, true);
        """)

        # 保存会话
        self.sessions[session_id] = RecordingSession(
            id=session_id,
            project_id=project_id,
            scenario_name=scenario_name,
            status="recording",
            started_at=datetime.now(),
            browser=self.browser,
            context=context,
            page=page,
            captured_actions=[]
        )

        return session_id

    async def stop_session(self, session_id: str) -> RecordingSession:
        """停止录制会话"""
        session = self.sessions[session_id]

        # 获取捕获的操作
        actions = await session.page.evaluate("""
            window.__recording ? window.__recording.actions : []
        """)

        session.captured_actions = [
            CapturedAction(**action) for action in actions
        ]
        session.status = "completed"
        session.completed_at = datetime.now()

        # 关闭浏览器
        await session.browser.close()
        await session.context.close()

        return session
```

### 阶段二：数据转换引擎（1周）

#### 2.1 操作转换器
```python
# app/services/recording/converter.py
class RecordingConverter:
    def __init__(self):
        self.keyword_mapping = {
            "click": "CLICK",
            "input": "INPUT",
            "navigate": "NAVIGATE",
            "select": "SELECT_OPTION",
            "wait": "WAIT_FOR_ELEMENT",
            "scroll": "SCROLL_TO_ELEMENT"
        }

    def convert_to_scenario(self, recording_session: RecordingSession) -> dict:
        """将录制会话转换为标准场景结构"""
        scenario = {
            "name": recording_session.scenario_name,
            "description": "通过录制创建",
            "scenario_type": "recorded",
            "metadata": {
                "created_by": "recording",
                "recording_session_id": recording_session.id
            },
            "cases": []
        }

        # 创建主用例
        main_case = {
            "name": "主流程",
            "description": "录制的主要操作流程",
            "steps": []
        }

        # 转换操作为步骤
        for index, action in enumerate(recording_session.captured_actions):
            step = self._convert_action_to_step(action, index)
            main_case["steps"].append(step)

        # 自动生成断言
        assertions = self._generate_assertions(recording_session.captured_actions)
        main_case["steps"].extend(assertions)

        scenario["cases"].append(main_case)
        return scenario

    def _convert_action_to_step(self, action: CapturedAction, index: int) -> dict:
        """转换单个操作为步骤"""
        keyword_name = self.keyword_mapping.get(action.type, "CLICK")

        # 查找关键字ID
        keyword_id = self._find_keyword_id(keyword_name)

        # 构建参数
        parameters = {
            "selector": action.selector,
            "timeout": 30000
        }

        if action.type == "input" and action.value:
            parameters["text"] = action.value

        if action.type == "navigate":
            parameters["url"] = action.page_info.get("url", "")

        return {
            "step_name": self._generate_step_name(action),
            "keyword_id": keyword_id,
            "parameters": parameters,
            "enabled": True,
            "continue_on_failure": False,
            "step_order": index + 1
        }
```

#### 2.2 数据提取器
```python
# app/services/recording/data_extractor.py
import re
from typing import List, Dict, Any

class DataExtractor:
    def extract_patterns(self, actions: List[CapturedAction]) -> List[DataPattern]:
        """从操作中提取数据模式"""
        patterns = []

        # 分析输入操作
        input_actions = [a for a in actions if a.type == "input"]
        for idx, action in enumerate(input_actions):
            value = action.value
            if self._is_variable_data(value):
                patterns.append(DataPattern(
                    id=str(uuid.uuid4()),
                    field_name=self._guess_field_name(action, idx),
                    pattern_type="input",
                    values=[value],
                    confidence=0.8,
                    selected=True,
                    suggested_variations=self._generate_variations(value)
                ))

        # 分析URL参数
        nav_actions = [a for a in actions if a.type == "navigate"]
        for action in nav_actions:
            url = action.page_info.get("url", "")
            url_params = self._extract_url_params(url)
            for param, value in url_params.items():
                patterns.append(DataPattern(
                    id=str(uuid.uuid4()),
                    field_name=param,
                    pattern_type="url",
                    values=[value],
                    confidence=0.9,
                    selected=True
                ))

        return self._merge_similar_patterns(patterns)

    def _is_variable_data(self, value: str) -> bool:
        """判断是否为可变数据"""
        patterns = [
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # 邮箱
            r'^1[3-9]\d{9}$',  # 手机号
            r'^[a-zA-Z0-9]{4,16}$'  # 用户名
        ]
        return any(re.match(p, value) for p in patterns)

    def _generate_variations(self, value: str) -> List[str]:
        """生成数据变体"""
        variations = [value]

        # 根据类型生成边界值
        if '@' in value:  # 邮箱
            variations.extend([
                "test@example.com",
                "invalid-email",
                ""
            ])
        elif len(value) < 20:  # 用户名/短文本
            variations.extend([
                value + "_test",
                "admin",
                ""
            ])

        return variations
```

### 阶段三：API集成与测试（1周）

#### 3.1 创建录制相关API文件
```typescript
// src/api/recording.ts
import apiClient from './client'

export interface RecordingStartRequest {
  project_id: string
  scenario_name: string
}

export interface CapturedAction {
  id: string
  timestamp: number
  type: string
  selector: string
  value?: string
  element_info: any
  page_info: any
}

export const recordingApi = {
  startRecording: async (request: RecordingStartRequest) => {
    const response = await apiClient.post('/recording/start', request)
    return response.data
  },

  stopRecording: async (sessionId: string) => {
    const response = await apiClient.post(`/recording/stop?session_id=${sessionId}`)
    return response.data
  },

  getCapturedActions: async (sessionId: string) => {
    const response = await apiClient.get(`/recording/actions/${sessionId}`)
    return response.data
  },

  extractTestData: async (actions: CapturedAction[]) => {
    const response = await apiClient.post('/recording/extract-data', { actions })
    return response.data
  },

  generateScenario: async (request: any) => {
    const response = await apiClient.post('/recording/generate-scenario', request)
    return response.data
  }
}
```

#### 3.2 完善录制向导集成
```typescript
// 更新 RecordingWizard.tsx 中的实现
import { recordingApi } from '../api/recording'

// 在实际实现中替换模拟数据
const handleStartRecording = async () => {
  try {
    const result = await recordingApi.startRecording({
      project_id: taskId,
      scenario_name: scenarioName
    })

    // 打开录制浏览器或提供连接信息
    console.log('录制已启动:', result)
    setIsRecording(true)
    setCurrentStep(2)

    // 开始轮询捕获的操作
    pollCapturedActions(result.session_id)
  } catch (error) {
    alert('启动录制失败: ' + error)
  }
}
```

### 阶段四：编辑功能集成（1周）

#### 4.1 录制结果编辑界面
- 确保录制生成的场景可以在现有界面中完全编辑
- 添加录制标识显示
- 提供重新录制选项

### 阶段五：测试与优化（1周）

#### 5.1 功能测试
- 端到端录制流程测试
- 数据提取准确性验证
- 编辑功能完整性测试

#### 5.2 性能优化
- 录制器资源管理
- 大量操作处理优化
- 前端响应速度优化

---

## 🎯 关键技术要点

### 1. 数据一致性保证
```typescript
// 录制和手动创建的场景使用相同接口
interface Scenario {
  // 完全相同的字段
  id: string
  name: string
  description?: string
  scenario_type: "manual" | "recorded"  // 唯一标识
  case_ids: string[]

  // 录制专用元数据（可选）
  metadata?: {
    created_by: "manual" | "recording"
    recording_session_id?: string
  }
}
```

### 2. 编辑功能兼容性
```typescript
// 场景编辑界面无需区分创建方式
function ScenarioEditor({ scenario }: { scenario: Scenario }) {
  // 无论手动还是录制创建，都使用相同的编辑逻辑
  return (
    <div>
      {/* 完全相同的编辑界面 */}
      <button>添加用例</button>
      <button>编辑步骤</button>

      {/* 录制创建的显示额外提示 */}
      {scenario.metadata?.created_by === 'recording' && (
        <div className="text-xs text-green-600">
          ✓ 录制创建 | 可继续编辑
        </div>
      )}
    </div>
  )
}
```

### 3. 用户体验连贯性
- 录制结果可立即编辑
- 编辑后的场景可重新录制
- 支持混合模式（部分录制+部分手动）

---

## 📊 实施优先级

### 高优先级（必须实现）
1. ✅ 创建方式选择界面
2. 🔴 录制器后端服务
3. 🔴 数据转换引擎
4. 🔴 API集成

### 中优先级（重要功能）
5. 🔴 智能数据提取
6. 🔴 编辑功能集成
7. 🔴 录制结果预览

### 低优先级（增强功能）
8. 🟡 回放验证功能
9. 🟡 高级断言生成
10. 🟡 录制质量分析

---

## ⏱️ 时间估算

- **当前已完成**: 基础框架（UI界面）
- **剩余工作量**: 4-6周
- **总计**: 5-7周完成完整功能

---

## 🎉 预期效果

### 用户体验
- 新用户：快速上手，5分钟生成第一个测试
- 高级用户：灵活选择，提高效率50%+
- 业务人员：参与测试创建，降低技术门槛

### 技术优势
- 完全向后兼容，零风险
- 统一数据模型，易维护
- 扩展性强，支持更多录制模式

### 业务价值
- 测试创建效率提升10倍
- 测试覆盖度显著提高
- 降低测试维护成本

这个融合架构确保了录制功能的完美集成，同时保持了系统的稳定性和现有用户的零影响！