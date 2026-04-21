"""
UI 关键字测试 - TDD 方法

测试驱动开发实现核心 UI 关键字功能

原则：
1. 先写测试，测试必须失败
2. 观察失败原因，确保测试正确
3. 编写最小化代码使测试通过
4. 重构优化
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from app.services.keywords.ui_keywords import UIKeywordEngine
from playwright.async_api import TimeoutError as PlaywrightTimeoutError


class TestAssertVisibleKeyword:
    """测试 ASSERT_VISIBLE 关键字"""

    @pytest.fixture
    def engine(self):
        """创建 UI 关键字引擎实例"""
        browser_manager = Mock()
        engine = UIKeywordEngine(browser_manager)
        return engine

    @pytest.fixture
    def mock_page(self):
        """创建模拟页面"""
        page = AsyncMock()
        page.wait_for_selector = AsyncMock()
        return page

    @pytest.mark.asyncio
    async def test_assert_visible_element_exists(self, engine, mock_page):
        """测试：断言存在的元素可见应该成功"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)
        engine.browser_manager.wait_for_element = AsyncMock(return_value={
            "success": True
        })
        engine.browser_manager.take_screenshot = AsyncMock(return_value="/path/to/screenshot.png")

        params = {
            "selector": "#submit-button",
            "timeout": 5000
        }

        # Act
        result = await engine._assert_visible(params)

        # Assert
        assert result["success"] is True
        assert "visible" in result["message"].lower()
        assert "#submit-button" in result["message"]

    @pytest.mark.asyncio
    async def test_assert_visible_element_not_exists_timeout(self, engine, mock_page):
        """测试：元素不存在时应该超时失败"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)
        engine.browser_manager.wait_for_element = AsyncMock(return_value={
            "success": False,
            "error": "元素超时"
        })
        engine.browser_manager.take_screenshot = AsyncMock(return_value="/path/to/screenshot.png")

        params = {
            "selector": "#missing-element",
            "timeout": 3000
        }

        # Act
        result = await engine._assert_visible(params)

        # Assert
        assert result["success"] is False
        assert "not visible" in result["message"].lower() or "timeout" in result["message"].lower()
        assert "screenshot" in result

    @pytest.mark.asyncio
    async def test_assert_visible_missing_selector_param(self, engine):
        """测试：缺少 selector 参数应该返回错误"""
        # Arrange
        params = {"timeout": 5000}  # 缺少 selector

        # Act
        result = await engine._assert_visible(params)

        # Assert
        assert result["success"] is False
        assert "selector" in result["error"].lower()


class TestAssertTextKeyword:
    """测试 ASSERT_TEXT 关键字"""

    @pytest.fixture
    def engine(self):
        """创建 UI 关键字引擎实例"""
        browser_manager = Mock()
        engine = UIKeywordEngine(browser_manager)
        return engine

    @pytest.fixture
    def mock_element(self):
        """创建模拟元素"""
        element = AsyncMock()
        element.inner_text = AsyncMock(return_value="Welcome to the application")
        return element

    @pytest.fixture
    def mock_page(self, mock_element):
        """创建模拟页面"""
        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=mock_element)
        return page

    @pytest.mark.asyncio
    async def test_assert_text_contains_match(self, engine, mock_page):
        """测试：包含匹配模式应该成功"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": ".welcome-message",
            "text": "Welcome",
            "match_type": "contains"
        }

        # Act
        result = await engine._assert_text(params)

        # Assert
        assert result["success"] is True
        assert result["expected"] == "Welcome"
        assert result["actual"] == "Welcome to the application"

    @pytest.mark.asyncio
    async def test_assert_text_exact_match(self, engine, mock_page):
        """测试：精确匹配模式应该成功"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": ".welcome-message",
            "text": "Welcome to the application",
            "match_type": "exact"
        }

        # Act
        result = await engine._assert_text(params)

        # Assert
        assert result["success"] is True
        assert result["expected"] == "Welcome to the application"
        assert result["actual"] == "Welcome to the application"

    @pytest.mark.asyncio
    async def test_assert_text_exact_match_fails(self, engine, mock_page):
        """测试：精确匹配不包含应该失败"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": ".welcome-message",
            "text": "Different text",
            "match_type": "exact"
        }

        # Act
        result = await engine._assert_text(params)

        # Assert
        assert result["success"] is False
        assert result["expected"] == "Different text"
        assert result["actual"] == "Welcome to the application"

    @pytest.mark.asyncio
    async def test_assert_text_regex_match(self, engine, mock_page):
        """测试：正则表达式匹配应该成功"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": ".welcome-message",
            "text": r"Welcome\s+to",
            "match_type": "regex"
        }

        # Act
        result = await engine._assert_text(params)

        # Assert
        assert result["success"] is True
        assert result["expected"] == r"Welcome\s+to"
        assert result["actual"] == "Welcome to the application"

    @pytest.mark.asyncio
    async def test_assert_text_element_not_found(self, engine, mock_page):
        """测试：元素不存在应该失败"""
        # Arrange
        mock_page.query_selector = AsyncMock(return_value=None)
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": ".missing-element",
            "text": "Some text"
        }

        # Act
        result = await engine._assert_text(params)

        # Assert
        assert result["success"] is False
        assert "not found" in result["message"].lower() or "not exist" in result["message"].lower()


class TestAssertUrlKeyword:
    """测试 ASSERT_URL 关键字"""

    @pytest.fixture
    def engine(self):
        browser_manager = Mock()
        engine = UIKeywordEngine(browser_manager)
        return engine

    @pytest.fixture
    def mock_page(self):
        page = AsyncMock()
        page.url = "https://example.com/dashboard"
        return page

    @pytest.mark.asyncio
    async def test_assert_url_contains_match(self, engine, mock_page):
        """测试：URL 包含匹配应该成功"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "url": "dashboard",
            "match_type": "contains"
        }

        # Act
        result = await engine._assert_url(params)

        # Assert
        assert result["success"] is True
        assert result["expected"] == "dashboard"
        assert result["actual"] == "https://example.com/dashboard"

    @pytest.mark.asyncio
    async def test_assert_url_exact_match(self, engine, mock_page):
        """测试：URL 精确匹配应该成功"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "url": "https://example.com/dashboard",
            "match_type": "exact"
        }

        # Act
        result = await engine._assert_url(params)

        # Assert
        assert result["success"] is True
        assert result["expected"] == "https://example.com/dashboard"
        assert result["actual"] == "https://example.com/dashboard"

    @pytest.mark.asyncio
    async def test_assert_url_contains_fails(self, engine, mock_page):
        """测试：URL 不包含应该失败"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "url": "admin",
            "match_type": "contains"
        }

        # Act
        result = await engine._assert_url(params)

        # Assert
        assert result["success"] is False
        assert result["expected"] == "admin"
        assert result["actual"] == "https://example.com/dashboard"


class TestAssertTitleKeyword:
    """测试 ASSERT_TITLE 关键字"""

    @pytest.fixture
    def engine(self):
        browser_manager = Mock()
        engine = UIKeywordEngine(browser_manager)
        return engine

    @pytest.fixture
    def mock_page(self):
        page = AsyncMock()
        page.title = AsyncMock(return_value="Dashboard - My App")
        return page

    @pytest.mark.asyncio
    async def test_assert_title_contains_match(self, engine, mock_page):
        """测试：标题包含匹配应该成功"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "title": "Dashboard",
            "match_type": "contains"
        }

        # Act
        result = await engine._assert_title(params)

        # Assert
        assert result["success"] is True
        assert result["expected"] == "Dashboard"
        assert result["actual"] == "Dashboard - My App"

    @pytest.mark.asyncio
    async def test_assert_title_exact_match(self, engine, mock_page):
        """测试：标题精确匹配应该成功"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "title": "Dashboard - My App",
            "match_type": "exact"
        }

        # Act
        result = await engine._assert_title(params)

        # Assert
        assert result["success"] is True
        assert result["expected"] == "Dashboard - My App"
        assert result["actual"] == "Dashboard - My App"


class TestGetTextKeyword:
    """测试 GET_TEXT 关键字"""

    @pytest.fixture
    def engine(self):
        browser_manager = Mock()
        engine = UIKeywordEngine(browser_manager)
        return engine

    @pytest.fixture
    def mock_element(self):
        element = AsyncMock()
        element.inner_text = AsyncMock(return_value="Sample text content")
        return element

    @pytest.fixture
    def mock_page(self, mock_element):
        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=mock_element)
        return page

    @pytest.mark.asyncio
    async def test_get_text_success(self, engine, mock_page):
        """测试：成功获取元素文本"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": ".content"
        }

        # Act
        result = await engine._get_text(params)

        # Assert
        assert result["success"] is True
        assert result["text"] == "Sample text content"

    @pytest.mark.asyncio
    async def test_get_text_element_not_found(self, engine, mock_page):
        """测试：元素不存在应该失败"""
        # Arrange
        mock_page.query_selector = AsyncMock(return_value=None)
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": ".missing"
        }

        # Act
        result = await engine._get_text(params)

        # Assert
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestScreenshotKeyword:
    """测试 SCREENSHOT 关键字"""

    @pytest.fixture
    def engine(self):
        browser_manager = Mock()
        engine = UIKeywordEngine(browser_manager)
        return engine

    @pytest.mark.asyncio
    async def test_screenshot_default_viewport(self, engine):
        """测试：默认视口截图"""
        # Arrange
        engine.browser_manager.take_screenshot = AsyncMock(
            return_value="/screenshots/test_screenshot.png"
        )

        params = {
            "path": "/screenshots/test_screenshot.png"
        }

        # Act
        result = await engine._screenshot(params)

        # Assert
        assert result["success"] is True
        assert "screenshot_path" in result
        assert result["screenshot_path"] == "/screenshots/test_screenshot.png"

    @pytest.mark.asyncio
    async def test_screenshot_full_page(self, engine):
        """测试：全页截图"""
        # Arrange
        engine.browser_manager.take_screenshot = AsyncMock(
            return_value="/screenshots/full_page.png"
        )

        params = {
            "path": "/screenshots/full_page.png",
            "full_page": True
        }

        # Act
        result = await engine._screenshot(params)

        # Assert
        assert result["success"] is True
        assert result["screenshot_path"] == "/screenshots/full_page.png"


class TestSelectKeyword:
    """测试 SELECT 关键字"""

    @pytest.fixture
    def engine(self):
        browser_manager = Mock()
        engine = UIKeywordEngine(browser_manager)
        return engine

    @pytest.fixture
    def mock_page(self):
        page = AsyncMock()
        page.select_option = AsyncMock()
        return page

    @pytest.mark.asyncio
    async def test_select_by_value(self, engine, mock_page):
        """测试：通过 value 选择下拉选项"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": "#country",
            "value": "CN",
            "by": "value"
        }

        # Act
        result = await engine._select(params)

        # Assert
        assert result["success"] is True
        mock_page.select_option.assert_called_once_with("#country", value="CN")

    @pytest.mark.asyncio
    async def test_select_by_label(self, engine, mock_page):
        """测试：通过 label 选择下拉选项"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": "#country",
            "value": "China",
            "by": "label"
        }

        # Act
        result = await engine._select(params)

        # Assert
        assert result["success"] is True
        mock_page.select_option.assert_called_once_with("#country", label="China")

    @pytest.mark.asyncio
    async def test_select_by_index(self, engine, mock_page):
        """测试：通过 index 选择下拉选项"""
        # Arrange
        engine.browser_manager.get_page = AsyncMock(return_value=mock_page)

        params = {
            "selector": "#country",
            "value": "1",
            "by": "index"
        }

        # Act
        result = await engine._select(params)

        # Assert
        assert result["success"] is True
        mock_page.select_option.assert_called_once_with("#country", index=1)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
