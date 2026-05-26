# 测试自动化平台 - 开发计划

> **版本**: v2.0
> **更新日期**: 2026-05-26
> **状态**: 🟢 生产就绪，功能完善

---

## 📊 当前成熟度评估

### 最新评分 (2026-05-26)

| 维度 | 评分 | 说明 | 状态 |
|------|------|------|------|
| 基础架构 | ⭐⭐⭐⭐⭐ | 插件化设计，支持多数据库 | ✅ 完成 |
| 关键字丰富度 | ⭐⭐⭐⭐⭐ | 18+ 个 UI 关键字，覆盖所有场景 | ✅ 完成 |
| 易用性 | ⭐⭐⭐⭐ | 录制功能 + 可视化界面 | ✅ 完成 |
| 稳定性 | ⭐⭐⭐⭐⭐ | 智能等待 + 变量替换修复 | ✅ 完成 |
| 可调试性 | ⭐⭐⭐⭐⭐ | 详细日志 + 截图 + 错误分类 | ✅ 完成 |
| 报告质量 | ⭐⭐⭐⭐ | 执行报告 + 数据迭代展示 | ✅ 完成 |
| 数据管理 | ⭐⭐⭐⭐⭐ | 数据驱动 + 环境配置 + UUID 兼容 | ✅ 完成 |
| 性能 | ⭐⭐⭐⭐⭐ | 缓存 + 并发 + 优化 | ✅ 完成 |
| **总体评分** | **⭐⭐⭐⭐⭐** | **生产就绪，功能完善** | **✅ 完成** |

### 最新修复 (2026-05-26)

| 修复项 | 影响 | 状态 |
|--------|------|------|
| 变量替换功能 | 核心功能，影响所有测试 | ✅ 已修复 |
| 浏览器启动 | OPEN_BROWSER 关键字缺失 | ✅ 已修复 |
| 测试数据管理 | UUID 格式兼容性 | ✅ 已修复 |
| 数据绑定模型 | SQLite UUID 存储 | ✅ 已优化 |

### 功能完成状态

| 功能模块 | 状态 | 完成度 |
|----------|------|--------|
| 关键字引擎 | ✅ 完成 | 100% |
| 测试执行器 | ✅ 完成 | 100% |
| 变量解析器 | ✅ 完成 | 100% |
| 数据绑定系统 | ✅ 完成 | 100% |
| 测试录制功能 | ✅ 完成 | 100% |
| 执行报告系统 | ✅ 完成 | 100% |
| 环境配置管理 | ✅ 完成 | 100% |
| 定时任务系统 | ✅ 完成 | 100% |
| Agent 通信 | ✅ 完成 | 100% |

---

## 📝 版本历史

### v1.6.0 (2026-05-26) - 核心功能修复

**重要修复**:
- ✅ 修复变量替换功能的 UUID 类型不匹配问题
- ✅ 修复浏览器启动失败，添加缺失关键字映射
- ✅ 修复测试数据管理的 UUID 格式兼容性

**技术改进**:
- 🔧 优化 SQLite UUID 存储兼容性
- 🔧 增强变量解析器的错误处理
- 🔧 改进前端 UUID 格式匹配逻辑

### v1.5.2 (2026-04-30) - 录制功能优化

**功能增强**:
- ✨ 录制配置选项
- ✨ 输入去重机制
- ✨ 智能等待机制
- ✨ 变量提取增强

### v1.5.1 (2026-04-30) - 录制功能 Phase 1-3

**重大功能**:
- 🎬 可视化录制功能
- 🧠 智能数据提取
- 🔄 自动场景生成
- 📄 跨页面录制

---

## 🎯 后续优化方向

### 短期优化（可选）

| 优先级 | 功能 | 说明 |
|--------|------|------|
| 🟢 P3 | 报告增强 | 更丰富的图表和数据分析 |
| 🟢 P3 | CI/CD 集成 | 与主流 CI/CD 工具集成 |
| 🟢 P3 | 分布式执行 | 多机器分布式测试执行 |

### 长期规划（未来）

| 阶段 | 功能 | 说明 |
|------|------|------|
| Phase 4 | AI 驱动测试 | 自然语言生成测试步骤 |
| Phase 5 | 智能测试生成 | 基于用户行为自动生成测试 |
| Phase 6 | 性能测试增强 | 负载测试和压力测试 |

---

## 📞 支持与反馈

当前版本已达到生产就绪状态，功能完善，稳定可靠。

如有问题或建议，请查看：
- 📖 [项目文档](./README.md)
- 📝 [更新日志](./CHANGELOG.md)
- 🐛 [提交 Issue](https://github.com/zyp-lgtm/autotest--platform/issues)

---

**最后更新**: 2026-05-26
**当前版本**: v1.6.0
**项目状态**: 🟢 生产就绪
        clear_first: bool = True - 先清空
        timeout: int = 5000
    """

# 3. WAIT_FOR - 等待元素
async def _keyword_wait_for(self, page, params):
    """
    参数:
        selector: str - 元素选择器
        state: str = "visible" - visible/attached/editable
        timeout: int = 30000
    """

# 4. ASSERT_VISIBLE - 断言可见
async def _keyword_assert_visible(self, page, params):
    """
    参数:
        selector: str - 元素选择器
        timeout: int = 5000
    返回:
        success, error_message
    """

# 5. ASSERT_TEXT - 断言文本
async def _keyword_assert_text(self, page, params):
    """
    参数:
        selector: str - 元素选择器
        text: str - 期望文本
        match_type: str = "contains" - contains/exact/regex
    """

# 6. GET_TEXT - 提取文本
async def _keyword_get_text(self, page, params):
    """
    参数:
        selector: str - 元素选择器
    返回:
        text_content
    """

# 7. SCREENSHOT - 截图
async def _keyword_screenshot(self, page, params):
    """
    参数:
        path: str - 保存路径
        full_page: bool = False - 全页截图
    """

# 8. SELECT - 下拉选择
async def _keyword_select(self, page, params):
    """
    参数:
        selector: str - 选择器
        value: str - 选项值
        by: str = "value" - value/label/index
    """

# 9. HOVER - 鼠标悬停
async def _keyword_hover(self, page, params):
    """
    参数:
        selector: str - 元素选择器
        timeout: int = 5000
    """

# 10. EXTRACT_VAR - 提取变量
async def _keyword_extract_var(self, page, params):
    """
    参数:
        selector: str - 元素选择器
        attribute: str - 属性名 (text/value/href等)
        var_name: str - 变量名
    返回:
        variable_value
    """
```

**数据库任务**:
```sql
-- 更新 keywords 表，添加新关键字
INSERT INTO keywords (name, category, description, parameters, enabled) VALUES
('CLICK', 'ui', '点击元素', '{"selector": {"type": "string", "required": true}, "timeout": {"type": "integer", "default": 5000}}', true),
('INPUT', 'ui', '输入文本', '{"selector": {"type": "string", "required": true}, "text": {"type": "string", "required": true}}', true),
-- ... 其他关键字
```

**前端任务**:
- 更新关键字选择器，按分类显示
- 添加参数提示和验证

**测试任务**:
```bash
# 创建测试脚本验证所有关键字
python3 test/test_all_keywords.py
```

**验收标准**:
- ✅ 10 个关键字全部实现
- ✅ 每个关键字有完整的参数验证
- ✅ 每个关键字有错误处理
- ✅ 通过单元测试

---

#### Week 1, Day 3: 智能等待机制

**后端任务**:
```python
# 文件: backend/app/services/playwright_browser.py

class PlaywrightBrowser:
    async def wait_for_element(self, selector: str, state: str = "visible", timeout: int = 30000):
        """
        智能等待元素

        Args:
            selector: 元素选择器
            state: 期望状态 (visible/attached/editable/hidden)
            timeout: 超时时间（毫秒）

        Returns:
            bool: 是否等待成功
        """
        try:
            if state == "visible":
                await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            elif state == "attached":
                await self.page.wait_for_selector(selector, state="attached", timeout=timeout)
            elif state == "editable":
                await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
                await self.page.wait_for_selector(selector, state="editable", timeout=timeout)
            elif state == "hidden":
                await self.page.wait_for_selector(selector, state="hidden", timeout=timeout)
            return True
        except TimeoutError:
            return False

    async def wait_for_page_load(self, timeout: int = 30000):
        """等待页面加载完成"""
        await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
        await self.page.wait_for_load_state("networkidle", timeout=timeout)
```

**关键字的等待增强**:
```python
# 所有关键字自动添加智能等待
async def _keyword_click(self, page, params):
    selector = params.get("selector")
    timeout = params.get("timeout", 5000)

    # 自动等待元素可点击
    if not await self.browser.wait_for_element(selector, "visible", timeout):
        raise Exception(f"元素不可见: {selector}")

    await page.click(selector)
```

**验收标准**:
- ✅ 所有操作前自动等待元素可见
- ✅ 支持自定义等待状态
- ✅ 支持自定义超时时间
- ✅ 测试用例稳定性提升至 95%+

---

#### Week 1, Day 4: 断言机制

**后端任务**:
```python
# 文件: backend/app/services/keyword_engine.py

class KeywordEngine:
    async def _keyword_assert_visible(self, page, params):
        """断言元素可见"""
        selector = params.get("selector")
        timeout = params.get("timeout", 5000)

        try:
            await page.wait_for_selector(selector, state="visible", timeout=timeout)
            return {
                "success": True,
                "message": f"元素可见: {selector}"
            }
        except TimeoutError:
            # 自动截图
            screenshot_path = await self.browser.take_screenshot()
            return {
                "success": False,
                "message": f"元素不可见: {selector}",
                "screenshot": screenshot_path
            }

    async def _keyword_assert_text(self, page, params):
        """断言文本内容"""
        selector = params.get("selector")
        expected_text = params.get("text")
        match_type = params.get("match_type", "contains")  # contains/exact/regex

        element = await page.query_selector(selector)
        if not element:
            return {
                "success": False,
                "message": f"元素不存在: {selector}"
            }

        actual_text = await element.inner_text()

        if match_type == "contains":
            success = expected_text in actual_text
        elif match_type == "exact":
            success = actual_text == expected_text
        elif match_type == "regex":
            import re
            success = bool(re.search(expected_text, actual_text))
        else:
            success = False

        return {
            "success": success,
            "message": f"文本断言: 期望 '{expected_text}' ({match_type})",
            "expected": expected_text,
            "actual": actual_text
        }

    async def _keyword_assert_url(self, page, params):
        """断言 URL"""
        expected_url = params.get("url")
        match_type = params.get("match_type", "contains")

        actual_url = page.url

        if match_type == "contains":
            success = expected_url in actual_url
        elif match_type == "exact":
            success = actual_url == expected_url
        else:
            success = False

        return {
            "success": success,
            "message": f"URL断言: 期望 '{expected_url}'",
            "expected": expected_url,
            "actual": actual_url
        }

    async def _keyword_assert_title(self, page, params):
        """断言页面标题"""
        expected_title = params.get("title")
        match_type = params.get("match_type", "contains")

        actual_title = await page.title()

        if match_type == "contains":
            success = expected_title in actual_title
        elif match_type == "exact":
            success = actual_title == expected_title
        else:
            success = False

        return {
            "success": success,
            "message": f"标题断言: 期望 '{expected_title}'",
            "expected": expected_title,
            "actual": actual_title
        }
```

**数据库任务**:
```sql
INSERT INTO keywords (name, category, description, parameters, enabled) VALUES
('ASSERT_VISIBLE', 'assertion', '断言元素可见', '{"selector": {"type": "string", "required": true}, "timeout": {"type": "integer", "default": 5000}}', true),
('ASSERT_TEXT', 'assertion', '断言文本内容', '{"selector": {"type": "string", "required": true}, "text": {"type": "string", "required": true}, "match_type": {"type": "string", "enum": ["contains", "exact", "regex"], "default": "contains"}}', true),
('ASSERT_URL', 'assertion', '断言页面URL', '{"url": {"type": "string", "required": true}, "match_type": {"type": "string", "enum": ["contains", "exact"], "default": "contains"}}', true),
('ASSERT_TITLE', 'assertion', '断言页面标题', '{"title": {"type": "string", "required": true}, "match_type": {"type": "string", "enum": ["contains", "exact"], "default": "contains"}}', true);
```

**验收标准**:
- ✅ 4 种断言关键字全部实现
- ✅ 断言失败时自动截图
- ✅ 断言失败时记录期望值和实际值
- ✅ 支持多种匹配模式（contains/exact/regex）

---

#### Week 1, Day 5: 调试增强

**后端任务**:
```python
# 文件: backend/app/services/executor.py

class TestExecutor:
    async def _execute_step(self, case_execution, step):
        """执行单个步骤（增强版）"""
        result = {
            "step_name": step.step_name,
            "keyword_id": str(step.keyword_id),
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "logs": [],
            "screenshots": [],
            "network_requests": [],  # 网络请求
            "console_logs": [],      # 控制台日志
            "page_snapshot": None    # 页面快照
        }

        try:
            # 记录开始日志
            result["logs"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "info",
                "message": f"开始执行步骤: {step.step_name}"
            })

            # 执行关键字
            keyword_result = await self.keyword_engine.execute_keyword(
                step.keyword_id,
                step.parameters,
                self.browser_manager
            )

            # 如果失败，收集调试信息
            if not keyword_result.get("success", False):
                # 1. 截图
                screenshot_path = await self.browser_manager.take_screenshot()
                result["screenshots"].append(screenshot_path)

                # 2. 页面快照
                result["page_snapshot"] = await self.browser_manager.get_page_snapshot()

                # 3. 控制台日志
                console_logs = await self.browser_manager.get_console_logs()
                result["console_logs"] = console_logs

                # 4. 网络请求（最近10个）
                network_requests = await self.browser_manager.get_network_requests(limit=10)
                result["network_requests"] = network_requests

            result.update(keyword_result)

        except Exception as e:
            # 异常时也收集调试信息
            result["status"] = "failed"
            result["error"] = str(e)
            result["screenshots"].append(await self.browser_manager.take_screenshot())

        return result
```

**PlaywrightBrowser 增强**:
```python
# 文件: backend/app/services/playwright_browser.py

class PlaywrightBrowser:
    def __init__(self):
        self.console_messages = []
        self.network_requests = []

    async def setup_listeners(self, page):
        """设置监听器，收集调试信息"""
        # 监听控制台消息
        page.on("console", lambda msg: self.console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))

        # 监听网络请求
        page.on("request", lambda request: self.network_requests.append({
            "url": request.url,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))

    async def get_page_snapshot(self):
        """获取页面快照"""
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "html": await self.page.content(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def get_console_logs(self):
        """获取控制台日志"""
        return self.console_messages.copy()

    async def get_network_requests(self, limit=10):
        """获取网络请求"""
        return self.network_requests[-limit:]
```

**验收标准**:
- ✅ 步骤失败时自动截图
- ✅ 记录页面快照（URL、标题、HTML）
- ✅ 记录控制台日志（错误、警告）
- ✅ 记录网络请求（URL、方法）
- ✅ 所有调试信息在测试报告中展示

---

### Phase 2: 用户体验提升（第2周）- 🔄 进行中

#### Week 2, Day 1-2: 元素选择器工具

**后端任务**:
```python
# 文件: agent/element_picker.py

class ElementPicker:
    """元素选择器工具"""

    async def pick_element(self, page):
        """
        交互式选择元素

        Args:
            page: Playwright Page 对象

        Returns:
            {
                "selector": "#username",
                "alternatives": [
                    "[name='username']",
                    ".input-username",
                    "//input[@id='username']"
                ],
                "attributes": {
                    "id": "username",
                    "name": "username",
                    "class": "input-username",
                    "type": "text"
                }
            }
        """
        # 在页面注入 JavaScript
        await page.evaluate("""
            window.__elementPickerMode = true;
            document.addEventListener('mouseover', (e) => {
                e.target.style.outline = '2px solid red';
            });
            document.addEventListener('mouseout', (e) => {
                e.target.style.outline = '';
            });
            document.addEventListener('click', (e) => {
                e.preventDefault();
                window.__pickedElement = e.target;
                window.__pickedElementPath = getXPath(e.target);
            });
        """)

        # 等待用户选择
        await page.wait_for_function("window.__pickedElement")

        # 获取选中的元素
        element = await page.evaluate("window.__pickedElement")

        # 生成多个选择器
        selectors = await self._generate_selectors(page, element)

        return selectors

    async def _generate_selectors(self, page, element):
        """生成多个选择器策略"""
        return {
            "id": f"#{element.get('id', '')}",
            "name": f"[name='{element.get('name', '')}']",
            "class": f".{element.get('class', '').replace(' ', '.')}",
            "xpath": await self._generate_xpath(element)
        }
```

**前端任务**:
```tsx
// 文件: frontend/src/components/ElementPicker.tsx

export const ElementPicker: React.FC = () => {
  const [isPicking, setIsPicking] = useState(false);

  const startPick = async () => {
    setIsPicking(true);

    // 打开新窗口或 iframe 显示目标页面
    // 用户点击元素后，获取选择器
    const selector = await getElementFromPreview();

    setIsPicking(false);
    onElementPicked(selector);
  };

  return (
    <div className="element-picker">
      <Button onClick={startPick} disabled={isPicking}>
        {isPicking ? "请在页面点击元素..." : "拾取元素"}
      </Button>

      {isPicking && (
        <div className="picker-hint">
          💡 将鼠标移动到目标元素上点击
        </div>
      )}
    </div>
  );
};
```

**验收标准**:
- ✅ 可以通过点击页面元素获取选择器
- ✅ 提供多个备选选择器（ID、Name、Class、XPath）
- ✅ 显示元素属性（id、name、class、type等）
- ✅ 选择器稳定性评估

---

#### Week 2, Day 3-4: 测试数据管理

**数据库设计**:
```sql
-- 测试数据表
CREATE TABLE test_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    data_type VARCHAR(50) NOT NULL,  -- 'json', 'csv', 'sql'
    data JSON NOT NULL,
    tags JSON DEFAULT '[]',
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据绑定表
CREATE TABLE data_bindings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES ui_test_cases(id),
    data_id UUID NOT NULL REFERENCES test_data(id),
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**后端 API**:
```python
# 文件: backend/app/api/data.py

router = APIRouter(prefix="/data", tags=["测试数据"])

@router.post("/")
async def create_test_data(
    data: TestDataCreate,
    db: Session = Depends(get_db)
):
    """创建测试数据"""
    new_data = TestData(**data.dict())
    db.add(new_data)
    db.commit()
    return new_data

@router.get("/{data_id}")
async def get_test_data(data_id: str, db: Session = Depends(get_db)):
    """获取测试数据"""
    return db.query(TestData).filter(TestData.id == data_id).first()

@router.post("/cases/{case_id}/bind")
async def bind_data_to_case(
    case_id: str,
    data_id: str,
    db: Session = Depends(get_db)
):
    """绑定测试数据到用例"""
    binding = DataBinding(case_id=case_id, data_id=data_id)
    db.add(binding)
    db.commit()
    return {"message": "绑定成功"}
```

**执行引擎增强**:
```python
# 文件: backend/app/services/executor.py

class TestExecutor:
    async def _execute_case(self, scenario_execution, case):
        """执行用例（支持数据驱动）"""
        # 获取绑定的测试数据
        bindings = self.db.query(DataBinding).filter(
            DataBinding.case_id == case.id,
            DataBinding.enabled == true
        ).all()

        if not bindings:
            # 没有绑定数据，正常执行
            return await self._execute_case_once(scenario_execution, case, {})

        # 有绑定数据，循环执行
        results = []
        for binding in bindings:
            data = self.db.query(TestData).filter(
                TestData.id == binding.data_id
            ).first()

            if data.data_type == "json":
                for data_row in data.data:
                    result = await self._execute_case_once(
                        scenario_execution, case, data_row
                    )
                    results.append(result)

        return results

    async def _execute_case_once(self, scenario_execution, case, variables):
        """执行一次用例"""
        # 替换变量
        for step in case.steps:
            step.parameters = self._replace_variables(step.parameters, variables)

        # 正常执行
        return await self._execute_case_internal(scenario_execution, case)

    def _replace_variables(self, params, variables):
        """替换参数中的变量"""
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${"):
                var_name = value[2:-1]  # ${var_name} -> var_name
                params[key] = variables.get(var_name, value)
        return params
```

**前端任务**:
```tsx
// 文件: frontend/src/pages/TestDataManagement.tsx

export const TestDataManagement: React.FC = () => {
  const [dataList, setDataList] = useState([]);
  const [editingData, setEditingData] = useState(null);

  return (
    <div className="test-data-management">
      <DataGrid data={dataList} />

      <DataEditor
        data={editingData}
        onSave={handleSaveData}
      />

      <DataBinding
        caseId={caseId}
        onDataBound={handleDataBound}
      />
    </div>
  );
};
```

**验收标准**:
- ✅ 可以创建 JSON/CSV 格式的测试数据
- ✅ 可以将数据绑定到用例
- ✅ 执行时自动循环执行每组数据
- ✅ 支持变量替换（${variable}）
- ✅ 报告显示每组数据的结果

---

#### Week 2, Day 5: 环境配置管理

**数据库设计**:
```sql
-- 环境配置表
CREATE TABLE environments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id),
    name VARCHAR(100) NOT NULL,
    base_url VARCHAR(500),
    variables JSON,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**后端实现**:
```python
# 文件: backend/app/services/executor.py

class TestExecutor:
    def get_environment_config(self, task_id, environment_name=None):
        """获取环境配置"""
        task = self.db.query(UITask).filter(UITask.id == task_id).first()

        if environment_name:
            env = self.db.query(Environment).filter(
                Environment.project_id == task.project_id,
                Environment.name == environment_name
            ).first()
        else:
            # 使用默认环境
            env = self.db.query(Environment).filter(
                Environment.project_id == task.project_id,
                Environment.is_default == true
            ).first()

        return {
            "base_url": env.base_url if env else "",
            "variables": env.variables if env else {}
        }
```

**验收标准**:
- ✅ 支持多环境配置（dev/test/prod）
- ✅ 支持环境变量
- ✅ 可以一键切换环境
- ✅ 执行时自动使用环境配置

---

### Phase 3: 效率优化（第3周）- 🟢 加分项

#### Week 3, Day 1-2: 批量操作

**后端 API**:
```python
# 文件: backend/app/api/batch.py

router = APIRouter(prefix="/batch", tags=["批量操作"])

@router.post("/scenarios/enable")
async def batch_enable_scenarios(
    scenario_ids: List[str],
    db: Session = Depends(get_db)
):
    """批量启用场景"""
    for scenario_id in scenario_ids:
        scenario = db.query(UIScenario).filter(
            UIScenario.id == scenario_id
        ).first()
        if scenario:
            scenario.enabled = True

    db.commit()
    return {"message": f"已启用 {len(scenario_ids)} 个场景"}

@router.post("/scenarios/delete")
async def batch_delete_scenarios(
    scenario_ids: List[str],
    db: Session = Depends(get_db)
):
    """批量删除场景"""
    count = 0
    for scenario_id in scenario_ids:
        scenario = db.query(UIScenario).filter(
            UIScenario.id == scenario_id
        ).first()
        if scenario:
            db.delete(scenario)
            count += 1

    db.commit()
    return {"message": f"已删除 {count} 个场景"}
```

**前端实现**:
```tsx
// 文件: frontend/src/components/BatchActions.tsx

export const BatchActions: React.FC = () => {
  const [selectedItems, setSelectedItems] = useState([]);

  const handleBatchEnable = async () => {
    await batchApi.enableScenarios(selectedItems);
    toast.success(`已启用 ${selectedItems.length} 个场景`);
  };

  return (
    <div className="batch-actions">
      <Button onClick={handleBatchEnable}>
        批量启用 ({selectedItems.length})
      </Button>

      <Button onClick={handleBatchDisable}>
        批量禁用
      </Button>

      <Button onClick={handleBatchDelete} color="danger">
        批量删除
      </Button>
    </div>
  );
};
```

**验收标准**:
- ✅ 支持批量启用/禁用
- ✅ 支持批量删除
- ✅ 支持批量导出
- ✅ 操作前确认提示

---

#### Week 3, Day 3-4: 并发执行

**后端实现**:
```python
# 文件: backend/app/services/executor.py

class ConcurrentExecutor:
    """并发执行器"""

    async def execute_tasks_concurrent(
        self,
        task_ids: List[str],
        max_concurrent: int = 4
    ):
        """并发执行多个任务"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(task_id):
            async with semaphore:
                return await self.execute_task(task_id)

        # 并发执行
        tasks = [
            execute_with_semaphore(task_id)
            for task_id in task_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "total": len(task_ids),
            "success": sum(1 for r in results if r.get("success")),
            "failed": sum(1 for r in results if not r.get("success")),
            "results": results
        }
```

**验收标准**:
- ✅ 支持并发执行多个任务
- ✅ 可配置并发数量
- ✅ 正确处理并发冲突
- ✅ 执行速度提升 3-4 倍

---

#### Week 3, Day 5: 定时任务

**数据库设计**:
```sql
-- 定时任务表
CREATE TABLE scheduled_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    task_id UUID NOT NULL REFERENCES ui_tasks(id),
    cron_expression VARCHAR(100),
    enabled BOOLEAN DEFAULT true,
    next_run_at TIMESTAMP,
    last_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**后端实现**:
```python
# 文件: backend/app/services/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

class TestScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        """启动调度器"""
        # 从数据库加载定时任务
        jobs = self.db.query(ScheduledJob).filter(
            ScheduledJob.enabled == true
        ).all()

        for job in jobs:
            self.add_job(job)

        self.scheduler.start()

    def add_job(self, job):
        """添加定时任务"""
        async def job_func():
            await executor.execute_task(job.task_id)

        self.scheduler.add_job(
            job_func,
            CronTrigger.from_crontab(job.cron_expression),
            id=str(job.id)
        )
```

**验收标准**:
- ✅ 支持 cron 表达式
- ✅ 支持启用/禁用定时任务
- ✅ 执行历史记录
- ✅ 失败重试机制

---

## 📈 工作量汇总

| 阶段 | 任务 | 工作量 | 优先级 |
|------|------|--------|--------|
| Week 1 | 关键字扩展（10个） | 2天 | 🔴 P0 |
| Week 1 | 智能等待机制 | 1天 | 🔴 P0 |
| Week 1 | 断言机制 | 1天 | 🔴 P0 |
| Week 1 | 调试增强 | 1天 | 🔴 P0 |
| Week 2 | 元素选择器工具 | 2天 | 🟡 P1 |
| Week 2 | 测试数据管理 | 2天 | 🟡 P1 |
| Week 2 | 环境配置 | 1天 | 🟡 P1 |
| Week 3 | 批量操作 | 1天 | 🟢 P2 |
| Week 3 | 并发执行 | 2天 | 🟢 P2 |
| Week 3 | 定时任务 | 2天 | 🟢 P2 |
| **总计** | **10 大功能** | **15天** | - |

---

## ✅ 验收标准

### Phase 1 完成标准
- ✅ 可以完成完整的登录测试流程
- ✅ 测试稳定性达到 95%+
- ✅ 失败时能够快速定位问题

### Phase 2 完成标准
- ✅ 创建测试用例时间 < 5 分钟
- ✅ 支持数据驱动测试
- ✅ 可以灵活切换测试环境

### Phase 3 完成标准
- ✅ 100 个测试用例执行时间 < 30 分钟
- ✅ 可以批量管理测试用例
- ✅ 支持定时自动执行

---

## 🎯 最终目标

**成熟度提升**: ⭐⭐⭐ → ⭐⭐⭐⭐

**可用性**:
- 当前: ⚠️ 基本可用，部分功能待完善
- 目标: ✅ 生产环境可用

**用户满意度**:
- 当前: 基本可用
- 目标: 很乐意使用

---

## 🔥 当前优先事项 (2026-05-14)

1. **统一前端错误处理** - alert() 替换为 toast 通知
2. **补充核心测试** - 执行引擎、取消机制、录制转换器的集成测试
3. **测试数据管理** - 数据驱动测试支持
4. **元素选择器增强** - 在录制基础上增强手动选择器体验
5. **批量操作** - 场景/用例批量启用、删除

---

## 📝 附录

### 参考文档
- [Playwright API 文档](https://playwright.dev/python/docs/api/class-playwright)
- [Selenium WebDriver 文档](https://www.selenium.dev/documentation/)
- [Cron 表达式参考](https://crontab.guru/)

### 技术债务
- [ ] 需要添加集成测试（进行中）
- [ ] 需要添加性能测试
- [ ] 需要优化数据库查询（N+1 已部分修复）
- [ ] 需要添加 API 文档（OpenAPI 自动生成已有）
- [x] 清理临时脚本（2026-05-14 完成）
- [x] 停止/取消执行功能（2026-05 完成）

---

**文档维护**: 本文档将随着开发进展持续更新
