"""
元素选择器工具测试 - TDD 方法

测试驱动开发实现元素选择器功能

原则：
1. 先写测试，测试必须失败
2. 观察失败原因，确保测试正确
3. 编写最小化代码使测试通过
4. 重构优化
"""
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.element_picker import ElementPicker


class TestElementPicker:
    """测试元素选择器工具"""

    @pytest.fixture
    def picker(self):
        """创建元素选择器实例"""
        return ElementPicker()

    @pytest.fixture
    def mock_page(self):
        """创建模拟页面"""
        page = AsyncMock()
        page.evaluate = AsyncMock()
        page.wait_for_function = AsyncMock()
        page.query_selector = AsyncMock()
        page.query_selector_all = AsyncMock()
        return page

    @pytest.mark.asyncio
    async def test_pick_element_injects_mode(self, picker, mock_page):
        """测试：拾取元素时应该注入选择模式"""
        # Arrange
        selector = "#submit-button"

        # Act
        await picker._inject_picker_mode(mock_page)

        # Assert
        mock_page.evaluate.assert_called()
        call_args = str(mock_page.evaluate.call_args)
        assert "__elementPickerMode" in call_args
        assert "mouseover" in call_args
        assert "click" in call_args

    @pytest.mark.asyncio
    async def test_pick_element_waits_for_selection(self, picker, mock_page):
        """测试：拾取元素时应该等待用户选择"""
        # Arrange
        mock_page.wait_for_function = AsyncMock(return_value=True)

        # Act
        await picker._wait_for_element_selection(mock_page)

        # Assert
        mock_page.wait_for_function.assert_called_once_with("window.__pickedElement")

    @pytest.mark.asyncio
    async def test_generate_selectors_creates_multiple_strategies(self, picker):
        """测试：应该生成多种选择器策略"""
        # Arrange
        element_data = {
            "id": "username-input",
            "name": "username",
            "class": "form-control input-primary",
            "tag": "input"
        }

        # Act
        selectors = picker._generate_selectors(element_data)

        # Assert
        assert "selectors" in selectors
        assert len(selectors["selectors"]) >= 3  # 至少3种策略

        # 验证包含 ID 选择器
        id_selector = next((s for s in selectors["selectors"] if s["type"] == "id"), None)
        assert id_selector is not None
        assert "#username-input" in id_selector["value"]

        # 验证包含 Name 选择器
        name_selector = next((s for s in selectors["selectors"] if s["type"] == "name"), None)
        assert name_selector is not None
        assert "[name='username']" in name_selector["value"]

        # 验证包含 Class 选择器
        class_selector = next((s for s in selectors["selectors"] if s["type"] == "class"), None)
        assert class_selector is not None

    @pytest.mark.asyncio
    async def test_assess_selector_stability(self, picker):
        """测试：应该评估选择器稳定性"""
        # Arrange
        selectors = [
            {"type": "id", "value": "#submit-button", "stability": 0},
            {"type": "class", "value": ".btn-primary", "stability": 0},
            {"type": "xpath", "value": "//div/button", "stability": 0}
        ]

        # Act
        stable_selectors = picker._assess_stability(selectors)

        # Assert
        # ID 选择器应该最稳定
        id_selector = next((s for s in stable_selectors if s["type"] == "id"), None)
        assert id_selector is not None
        assert id_selector["stability"] >= 8  # 高稳定性

        # XPath 选择器稳定性较低
        xpath_selector = next((s for s in stable_selectors if s["type"] == "xpath"), None)
        assert xpath_selector is not None
        assert xpath_selector["stability"] <= 5  # 低稳定性

    @pytest.mark.asyncio
    async def test_extract_element_attributes(self, picker, mock_page):
        """测试：应该提取元素属性"""
        # Arrange
        element = AsyncMock()
        element.get_attribute = AsyncMock(side_effect=lambda x: {
            "id": "email-input",
            "name": "email",
            "class": "form-control",
            "type": "email",
            "placeholder": "Enter email"
        }.get(x))

        element.evaluate = AsyncMock(return_value="input")

        # Act
        attributes = await picker._extract_attributes(element)

        # Assert
        assert attributes["id"] == "email-input"
        assert attributes["name"] == "email"
        assert attributes["class"] == "form-control"
        assert attributes["type"] == "email"
        assert attributes["placeholder"] == "Enter email"

    @pytest.mark.asyncio
    async def test_generate_xpath(self, picker):
        """测试：应该生成 XPath 选择器"""
        # Arrange
        element_data = {
            "tag": "button",
            "id": "submit-btn",
            "class": "btn-primary"
        }

        # Act
        xpath = picker._generate_xpath(element_data)

        # Assert
        assert "//" in xpath
        assert "button" in xpath.lower()

    @pytest.mark.asyncio
    async def test_full_pick_workflow(self, picker, mock_page):
        """测试：完整的拾取元素工作流"""
        # Arrange
        mock_page.evaluate = AsyncMock()
        mock_page.wait_for_function = AsyncMock(return_value=True)
        mock_page.evaluate.side_effect = [
            None,  # 注入模式
            {"id": "search-box", "name": "search", "tag": "input"},  # 选中的元素
            None  # 清理模式
        ]

        # Act
        result = await picker.pick_element(mock_page)

        # Assert
        assert result["success"] is True
        assert "element_info" in result
        assert "selectors" in result["element_info"]
        assert result["element_info"]["attributes"]["id"] == "search-box"

    @pytest.mark.asyncio
    async def test_recommend_best_selector(self, picker):
        """测试：应该推荐最佳选择器"""
        # Arrange
        selectors = [
            {"type": "id", "value": "#unique-id", "stability": 10},
            {"type": "class", "value": ".common-class", "stability": 5},
            {"type": "xpath", "value": "//div[1]/input", "stability": 3}
        ]

        # Act
        best = picker._recommend_best_selector(selectors)

        # Assert
        assert best["type"] == "id"
        assert best["stability"] == 10

    @pytest.mark.asyncio
    async def test_handle_missing_element(self, picker, mock_page):
        """测试：应该处理元素不存在的情况"""
        # Arrange
        mock_page.wait_for_function = AsyncMock(side_effect=Exception("Timeout"))

        # Act
        result = await picker.pick_element(mock_page)

        # Assert
        assert result["success"] is False
        assert "error" in result


class TestSelectorGenerationStrategies:
    """测试选择器生成策略"""

    @pytest.fixture
    def picker(self):
        return ElementPicker()

    @pytest.mark.asyncio
    async def test_id_selector_generation(self, picker):
        """测试：ID 选择器生成"""
        element = {"id": "unique-element"}

        selectors = picker._generate_selectors(element)
        id_selector = next((s for s in selectors["selectors"] if s["type"] == "id"), None)

        assert id_selector is not None
        assert id_selector["value"] == "#unique-element"

    @pytest.mark.asyncio
    async def test_name_selector_generation(self, picker):
        """测试：Name 选择器生成"""
        element = {"name": "username"}

        selectors = picker._generate_selectors(element)
        name_selector = next((s for s in selectors["selectors"] if s["type"] == "name"), None)

        assert name_selector is not None
        assert name_selector["value"] == "[name='username']"

    @pytest.mark.asyncio
    async def test_class_selector_generation(self, picker):
        """测试：Class 选择器生成"""
        element = {"class": "btn-primary btn-large"}

        selectors = picker._generate_selectors(element)
        class_selector = next((s for s in selectors["selectors"] if s["type"] == "class"), None)

        assert class_selector is not None
        assert ".btn-primary" in class_selector["value"] or ".btn-large" in class_selector["value"]

    @pytest.mark.asyncio
    async def test_data_attribute_selector_generation(self, picker):
        """测试：Data 属性选择器生成"""
        element = {
            "data-test-id": "submit-button",
            "data-cy": "login-submit"
        }

        selectors = picker._generate_selectors(element)

        # 应该包含 data 属性选择器
        data_selectors = [s for s in selectors["selectors"] if s["type"] == "data-attribute"]
        assert len(data_selectors) >= 1


class TestElementPickerIntegration:
    """测试元素选择器与浏览器集成"""

    @pytest.fixture
    def picker(self):
        return ElementPicker()

    @pytest.mark.asyncio
    async def test_cleanup_after_picking(self, picker):
        """测试：拾取后应该清理注入的代码"""
        # Arrange
        mock_page = AsyncMock()

        # Act
        await picker._cleanup_picker_mode(mock_page)

        # Assert
        mock_page.evaluate.assert_called()
        call_args = str(mock_page.evaluate.call_args)
        assert "__elementPickerMode" in call_args
        assert "false" in call_args.lower()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, picker):
        """测试：应该处理超时情况"""
        # Arrange
        import asyncio
        from app.services.element_picker import ElementPickerTimeout

        mock_page = AsyncMock()
        mock_page.wait_for_function = AsyncMock(
            side_effect=asyncio.TimeoutError("Element selection timeout")
        )

        # Act & Assert
        with pytest.raises(ElementPickerTimeout):
            await picker._wait_for_element_selection(mock_page, timeout=1000)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
