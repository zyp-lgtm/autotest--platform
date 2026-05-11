# 录制功能数据结构设计

## 🏗️ 核心数据结构

### 1. 统一的场景数据模型

无论手动创建还是录制生成，都使用相同的数据结构：

```typescript
// 场景数据结构（完全统一）
interface Scenario {
  id: string
  name: string
  description?: string
  scenario_type: "manual" | "recorded"  // 新增：标识创建方式
  case_ids: string[]
  created_at: string
  updated_at: string
  metadata?: {
    created_by: "manual" | "recording"
    recording_session_id?: string  // 录制会话ID（可选）
    confidence_score?: number       // 录制识别的置信度
  }
}

// 用例数据结构（完全统一）
interface TestCase {
  id: string
  scenario_id: string
  name: string
  description?: string
  step_ids: string[]
}

// 步骤数据结构（完全统一）
interface TestStep {
  id: string
  case_id: string
  step_name: string
  keyword_id: string
  parameters: Record<string, any>
  enabled: boolean
  continue_on_failure: boolean
  step_order: number
}
```

**关键点**:
- ✅ 录制生成的场景与手动创建的场景数据结构100%相同
- ✅ 唯一区别是 `metadata.created_by` 字段
- ✅ 编辑界面完全相同，无需区分处理

### 2. 录制会话数据结构

录制过程中的临时数据：

```typescript
interface RecordingSession {
  id: string
  project_id: string
  scenario_name: string
  status: "preparing" | "recording" | "paused" | "processing" | "completed"
  started_at: string
  completed_at?: string

  // 捕获的操作
  captured_actions: CapturedAction[]

  // 提取的数据模式
  data_patterns: DataPattern[]

  // 生成的场景（临时）
  generated_scenario?: Scenario
}

interface CapturedAction {
  id: string
  timestamp: number
  type: "click" | "input" | "navigate" | "select" | "scroll" | "wait"
  selector: string
  selector_strategy: "css" | "xpath" | "text"
  value?: string

  // 元素信息
  element_info: {
    tag: string
    text?: string
    attributes?: Record<string, string>
  }

  // 页面信息
  page_info: {
    url: string
    title: string
  }
}

interface DataPattern {
  id: string
  field_name: string
  pattern_type: "input" | "url" | "assertion"
  values: any[]
  confidence: number
  selected: boolean
  suggested_variations?: any[]
}
```

### 3. 转换过程数据流

```
录制会话数据 → 转换器 → 标准场景数据 → 保存到数据库
     ↓              ↓           ↓
CapturedAction   ConvertTo   Scenario
DataPattern     TestStep    TestCase
```

## 🔄 数据转换逻辑

### 1. 操作 → 步骤转换

```typescript
// 转换器将录制操作转换为标准步骤
function convertActionToStep(action: CapturedAction): TestStep {
  const keywordMapping = {
    "click": "CLICK",
    "input": "INPUT",
    "navigate": "NAVIGATE",
    "select": "SELECT_OPTION",
    "wait": "WAIT_FOR_ELEMENT"
  }

  const keyword = keywordMapping[action.type]

  // 构建标准步骤参数
  const parameters = {
    selector: action.selector,
    timeout: 30000  // 默认超时
  }

  // 根据操作类型添加特定参数
  if (action.type === "input" && action.value) {
    parameters.text = action.value
  }

  if (action.type === "navigate") {
    parameters.url = action.page_info.url
  }

  return {
    id: generateId(),
    case_id: currentCaseId,
    step_name: generateStepDescription(action),
    keyword_id: findKeywordId(keyword),
    parameters,
    enabled: true,
    continue_on_failure: false,
    step_order: action.order
  }
}

// 自动生成步骤描述
function generateStepDescription(action: CapturedAction): string {
  const templates = {
    "click": `点击 ${action.element_info.text || action.selector}`,
    "input": `在 ${action.selector} 输入 "${action.value}"`,
    "navigate": `导航到 ${action.page_info.url}`,
    "select": `在下拉框 ${action.selector} 选择 "${action.value}"`
  }

  return templates[action.type] || `执行 ${action.type} 操作`
}
```

### 2. 数据模式提取

```typescript
// 从录制操作中提取测试数据模式
function extractDataPatterns(actions: CapturedAction[]): DataPattern[] {
  const patterns: DataPattern[] = []

  // 1. 分析输入操作
  actions.filter(a => a.type === "input").forEach((action, index) => {
    const value = action.value
    if (isVariableData(value)) {
      patterns.push({
        id: generateId(),
        field_name: guessFieldName(action, index),
        pattern_type: "input",
        values: [value],
        confidence: calculateConfidence(action),
        selected: true,
        suggested_variations: generateVariations(value)
      })
    }
  })

  // 2. 分析URL参数
  actions.filter(a => a.type === "navigate").forEach(action => {
    const urlParams = extractUrlParams(action.page_info.url)
    Object.entries(urlParams).forEach(([param, value]) => {
      patterns.push({
        id: generateId(),
        field_name: param,
        pattern_type: "url",
        values: [value],
        confidence: 0.9,
        selected: true
      })
    })
  })

  return mergeSimilarPatterns(patterns)
}

// 判断是否为可变数据
function isVariableData(value: string): boolean {
  // 邮箱、用户名、电话等
  const patterns = [
    /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,  // 邮箱
    /^1[3-9]\d{9}$/,  // 手机号
    /^[a-zA-Z0-9]{4,16}$/,  // 用户名
  ]

  return patterns.some(p => p.test(value)) || value.length < 20
}

// 猜测字段名
function guessFieldName(action: CapturedAction, index: number): string {
  const elementText = action.element_info.text?.toLowerCase() || ""
  const selector = action.selector.toLowerCase()

  // 基于元素文本猜测
  if (elementText.includes("用户") || selector.includes("user")) {
    return "username"
  }
  if (elementText.includes("密码") || selector.includes("pass")) {
    return "password"
  }
  if (elementText.includes("邮箱") || selector.includes("email")) {
    return "email"
  }

  // 默认字段名
  return `field_${index + 1}`
}
```

### 3. 生成测试数据集

```typescript
// 从数据模式生成测试数据
function generateTestData(patterns: DataPattern[]): TestData {
  const testData = {
    id: generateId(),
    project_id: currentProjectId,
    name: `${scenarioName}_测试数据`,
    description: "从录制中自动提取",
    data_type: "json",
    data: [],
    tags: ["auto-generated", "recorded"]
  }

  // 生成基础行（原始值）
  const baseRow = {}
  patterns.forEach(pattern => {
    if (pattern.selected) {
      baseRow[pattern.field_name] = pattern.values[0]
    }
  })
  testData.data.push(baseRow)

  // 生成变体行
  patterns.forEach(pattern => {
    if (pattern.selected && pattern.suggested_variations) {
      pattern.suggested_variations.forEach(variation => {
        const variantRow = { ...baseRow }
        variantRow[pattern.field_name] = variation
        testData.data.push(variantRow)
      })
    }
  })

  return testData
}
```

## 🎨 界面组件设计

### 1. 创建方式选择组件

```tsx
// components/creation-mode-selector.tsx
export function CreationModeSelector({ onSelect }) {
  return (
    <div className="grid grid-cols-2 gap-6">
      {/* 手动创建 */}
      <Card onClick={() => onSelect("manual")}
            className="cursor-pointer hover:shadow-lg transition">
        <CardHeader>
          <div className="text-5xl mb-2">✏️</div>
          <CardTitle>手动创建</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-4">
            逐步创建用例和步骤，精确控制每个细节
          </p>
          <ul className="text-sm space-y-1">
            <li>✓ 完全控制每个步骤</li>
            <li>✓ 适合复杂测试逻辑</li>
            <li>✓ 支持所有高级功能</li>
            <li>✓ 可复用测试数据</li>
          </ul>
        </CardContent>
        <CardFooter>
          <Button className="w-full">选择手动创建</Button>
        </CardFooter>
      </Card>

      {/* 录制创建 */}
      <Card onClick={() => onSelect("recording")}
            className="cursor-pointer hover:shadow-lg transition">
        <CardHeader>
          <div className="text-5xl mb-2">🎬</div>
          <CardTitle>录制创建</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-4">
            在浏览器中操作流程，自动生成测试步骤
          </p>
          <ul className="text-sm space-y-1">
            <li>✓ 快速生成基础步骤</li>
            <li>✓ 自动识别元素选择器</li>
            <li>✓ 智能提取测试数据</li>
            <li>✓ 可后续手工调整</li>
          </ul>
        </CardContent>
        <CardFooter>
          <Button className="w-full">选择录制创建</Button>
        </CardFooter>
      </Card>
    </div>
  )
}
```

### 2. 录制向导组件

```tsx
// components/recording-wizard.tsx
export function RecordingWizard({ onComplete, onCancel }) {
  const [currentStep, setCurrentStep] = useState(1)
  const [recordingSession, setRecordingSession] = useState<RecordingSession>()

  const steps = [
    { title: "录制准备", component: RecordingPreparation },
    { title: "录制中", component: RecordingInProgress },
    { title: "智能提取", component: DataExtraction },
    { title: "预览调整", component: PreviewAndAdjust }
  ]

  return (
    <Dialog open>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>录制创建场景</DialogTitle>
          <DialogDescription>
            按照向导完成录制，系统将自动生成测试场景
          </DialogDescription>
        </DialogHeader>

        {/* 步骤指示器 */}
        <Stepper currentStep={currentStep} steps={steps} />

        {/* 当前步骤内容 */}
        <div className="mt-4">
          {React.createElement(steps[currentStep - 1].component, {
            recordingSession,
            onNext: () => setCurrentStep(s => s + 1),
            onPrevious: () => setCurrentStep(s => s - 1),
            onComplete,
            onCancel
          })}
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

## 🔄 完整流程图

```
用户操作流程:
┌─────────────────────────────────────────────────────────┐
│ 1. 在场景管理页面点击"创建场景"                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 弹出"创建方式选择"对话框                              │
│    [手动创建] [录制创建]                                  │
└─────────────────────────────────────────────────────────┘
           ↓                           ↓
┌──────────────────────┐    ┌──────────────────────────┐
│ 手动创建模式           │    │ 录制创建模式             │
│ (现有功能，保持不变)   │    │ (新增功能)               │
└──────────────────────┘    └──────────────────────────┘
                                     ↓
                          ┌──────────────────────────┐
                          │ 步骤1: 录制准备           │
                          │ - 输入场景名称            │
                          │ - 阅读录制说明            │
                          │ - 点击"开始录制"          │
                          └──────────────────────────┘
                                     ↓
                          ┌──────────────────────────┐
                          │ 步骤2: 录制进行中         │
                          │ - 打开录制浏览器          │
                          │ - 执行测试操作            │
                          │ - 实时捕获操作            │
                          │ - 点击"停止录制"          │
                          └──────────────────────────┘
                                     ↓
                          ┌──────────────────────────┐
                          │ 步骤3: 智能数据提取       │
                          │ - 显示识别的数据模式      │
                          │ - 选择测试数据字段        │
                          │ - 生成变体数据            │
                          └──────────────────────────┘
                                     ↓
                          ┌──────────────────────────┐
                          │ 步骤4: 预览和调整         │
                          │ - 查看生成的场景          │
                          │ - 手工编辑步骤            │
                          │ - 添加断言验证            │
                          │ - 调整测试数据            │
                          └──────────────────────────┘
                                     ↓
                          ┌──────────────────────────┐
                          │ 保存到数据库              │
                          │ - 标准场景数据结构        │
                          │ - 与手动创建完全兼容      │
                          │ - 可正常编辑执行           │
                          └──────────────────────────┘
```

## ✅ 关键优势

### 1. 完全向后兼容
- 现有手动创建功能完全不变
- 新功能不影响现有用户
- 数据库表结构无需修改

### 2. 统一数据模型
- 录制和手动创建的场景数据结构完全相同
- 编辑界面完全相同
- 执行引擎无需修改

### 3. 用户友好
- 清晰的创建方式选择
- 渐进式向导引导
- 实时反馈和预览

### 4. 灵活性
- 录制后完全可编辑
- 可在两种模式间切换
- 支持混合方式（部分录制+部分手动）

这种设计确保了录制功能的完美集成，同时保持了系统的稳定性和易用性！