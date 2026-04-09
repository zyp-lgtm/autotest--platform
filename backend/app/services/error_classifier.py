"""
错误分类器
对测试执行过程中的错误进行分类，并提供针对性的解决建议
"""
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """错误类别"""
    TIMEOUT = "timeout"  # 超时错误
    ELEMENT_NOT_FOUND = "element_not_found"  # 元素未找到
    NETWORK = "network"  # 网络错误
    ASSERTION = "assertion"  # 断言失败
    SCRIPT = "script"  # 脚本错误
    BROWSER = "browser"  # 浏览器错误
    PERMISSION = "permission"  # 权限错误
    UNKNOWN = "unknown"  # 未知错误


class ErrorSeverity(str, Enum):
    """错误严重程度"""
    LOW = "low"  # 低：可以忽略或临时性问题
    MEDIUM = "medium"  # 中：需要关注但不阻塞
    HIGH = "high"  # 高：需要立即解决
    CRITICAL = "critical"  # 严重：阻塞测试执行


class ErrorSuggestion:
    """错误建议"""
    def __init__(
        self,
        title: str,
        description: str,
        solutions: List[str],
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        reference_links: List[str] = None
    ):
        self.title = title
        self.description = description
        self.solutions = solutions
        self.severity = severity
        self.reference_links = reference_links or []


class ErrorClassifier:
    """错误分类器"""

    # 错误分类规则
    ERROR_PATTERNS = {
        ErrorCategory.TIMEOUT: [
            "timeout",
            "超时",
            "Timeout",
            "exceeded"
        ],
        ErrorCategory.ELEMENT_NOT_FOUND: [
            "not found",
            "无法找到",
            "no such element",
            "NoSuchElement",
            "visible",
            "attached"
        ],
        ErrorCategory.NETWORK: [
            "network",
            "connection",
            "ECONNREFUSED",
            "ETIMEDOUT",
            "fetch failed"
        ],
        ErrorCategory.ASSERTION: [
            "assert",
            "断言",
            "expected",
            "实际值"
        ],
        ErrorCategory.SCRIPT: [
            "SyntaxError",
            "TypeError",
            "AttributeError",
            "NameError",
            "ReferenceError",
            "脚本错误"
        ],
        ErrorCategory.BROWSER: [
            "browser",
            "浏览器",
            "chrome",
            "chromium",
            "playwright",
            "Browser crashed"
        ],
        ErrorCategory.PERMISSION: [
            "permission",
            "权限",
            "denied",
            "unauthorized",
            "forbidden"
        ]
    }

    # 错误建议库
    ERROR_SUGGESTIONS = {
        ErrorCategory.TIMEOUT: ErrorSuggestion(
            title="超时错误",
            description="操作在规定时间内未完成",
            solutions=[
                "1. 增加等待时间：在参数中设置更长的timeout值",
                "2. 检查网络连接：确认网络延迟是否过高",
                "3. 优化等待策略：使用条件等待而非固定时间等待",
                "4. 检查页面性能：页面加载缓慢可能导致超时",
                "5. 使用重试机制：启用自动重试功能"
            ],
            severity=ErrorSeverity.MEDIUM
        ),

        ErrorCategory.ELEMENT_NOT_FOUND: ErrorSuggestion(
            title="元素未找到",
            description="无法定位到指定的页面元素",
            solutions=[
                "1. 检查选择器：确认CSS选择器或XPath是否正确",
                "2. 等待元素出现：元素可能尚未加载完成，增加等待时间",
                "3. 检查iframe：元素可能在iframe中，需要切换上下文",
                "4. 检查元素属性：确认元素的class、id等属性是否正确",
                "5. 使用浏览器开发者工具：在Elements面板中验证元素定位",
                "6. 检查页面跳转：确认是否跳转到了其他页面"
            ],
            severity=ErrorSeverity.HIGH
        ),

        ErrorCategory.NETWORK: ErrorSuggestion(
            title="网络错误",
            description="网络连接或请求失败",
            solutions=[
                "1. 检查网络连接：确认网络是否正常",
                "2. 验证URL地址：确认API端点或页面URL是否正确",
                "3. 检查代理设置：如果使用代理，确认代理配置正确",
                "4. 查看防火墙：防火墙可能阻止了请求",
                "5. 检查服务器状态：目标服务器可能宕机",
                "6. 增加重试次数：网络波动时可自动重试"
            ],
            severity=ErrorSeverity.HIGH
        ),

        ErrorCategory.ASSERTION: ErrorSuggestion(
            title="断言失败",
            description="实际结果与预期不符",
            solutions=[
                "1. 检查断言条件：确认断言逻辑是否正确",
                "2. 验证预期值：预期的值是否合理",
                "3. 检查数据格式：实际数据的格式是否符合预期",
                "4. 添加详细日志：记录实际值和预期值用于调试",
                "5. 检查测试数据：测试数据可能不符合测试场景"
            ],
            severity=ErrorSeverity.MEDIUM
        ),

        ErrorCategory.SCRIPT: ErrorSuggestion(
            title="脚本错误",
            description="测试脚本执行出错",
            solutions=[
                "1. 检查语法：查看代码是否有语法错误",
                "2. 验证变量：确认变量已定义且类型正确",
                "3. 查看完整错误堆栈：定位错误的具体位置",
                "4. 使用代码检查工具：如pylint、eslint等",
                "5. 单元测试：对问题代码编写单元测试"
            ],
            severity=ErrorSeverity.CRITICAL
        ),

        ErrorCategory.BROWSER: ErrorSuggestion(
            title="浏览器错误",
            description="浏览器进程或操作失败",
            solutions=[
                "1. 重启浏览器：浏览器进程可能已损坏",
                "2. 清除浏览器缓存：缓存或Cookie可能导致问题",
                "3. 更新浏览器驱动：确保Playwright/ChromeDriver版本匹配",
                "4. 检查系统资源：内存或CPU不足可能导致浏览器崩溃",
                "5. 关闭其他浏览器实例：端口冲突可能导致失败"
            ],
            severity=ErrorSeverity.HIGH
        ),

        ErrorCategory.PERMISSION: ErrorSuggestion(
            title="权限错误",
            description="操作权限不足",
            solutions=[
                "1. 检查文件权限：确认文件/目录具有读写权限",
                "2. 验证API访问令牌：token可能已过期或无效",
                "3. 检查用户角色：确认用户具有执行操作的权限",
                "4. 查看访问控制列表：ACL或IAM配置是否正确",
                "5. 联系管理员：某些操作需要特定权限"
            ],
            severity=ErrorSeverity.HIGH
        ),

        ErrorCategory.UNKNOWN: ErrorSuggestion(
            title="未知错误",
            description="未能识别的错误类型",
            solutions=[
                "1. 查看完整错误日志：获取更多错误上下文",
                "2. 启用调试模式：增加日志详细程度",
                "3. 检查系统日志：操作系统或应用日志可能有更多信息",
                "4. 联系技术支持：提供完整的错误堆栈和重现步骤",
                "5. 搜索错误信息：在错误追踪系统或搜索引擎中查找"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    }

    @classmethod
    def classify_error(cls, error_message: str) -> tuple[ErrorCategory, ErrorSeverity]:
        """
        分类错误

        Args:
            error_message: 错误消息

        Returns:
            (错误类别, 严重程度)
        """
        if not error_message:
            return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

        error_lower = error_message.lower()

        # 遍历所有错误类别
        for category, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in error_lower:
                    # 确定严重程度
                    severity = cls._determine_severity(category, error_message)
                    return category, severity

        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

    @classmethod
    def _determine_severity(cls, category: ErrorCategory, error_message: str) -> ErrorSeverity:
        """确定错误严重程度"""
        # 脚本错误通常是严重的
        if category == ErrorCategory.SCRIPT:
            return ErrorSeverity.CRITICAL

        # 权限错误严重
        if category == ErrorCategory.PERMISSION:
            return ErrorSeverity.HIGH

        # 浏览器崩溃严重
        if category == ErrorCategory.BROWSER and "crashed" in error_message.lower():
            return ErrorSeverity.CRITICAL

        # 元素未找到通常是高严重程度
        if category == ErrorCategory.ELEMENT_NOT_FOUND:
            return ErrorSeverity.HIGH

        # 超时通常是中等严重程度
        if category == ErrorCategory.TIMEOUT:
            return ErrorSeverity.MEDIUM

        # 网络错误严重程度取决于具体情况
        if category == ErrorCategory.NETWORK:
            if "timeout" in error_message.lower():
                return ErrorSeverity.MEDIUM
            return ErrorSeverity.HIGH

        return ErrorSeverity.MEDIUM

    @classmethod
    def get_suggestion(cls, error_message: str) -> ErrorSuggestion:
        """
        获取错误的解决建议

        Args:
            error_message: 错误消息

        Returns:
            ErrorSuggestion: 错误建议
        """
        category, _ = cls.classify_error(error_message)
        return cls.ERROR_SUGGESTIONS.get(category, cls.ERROR_SUGGESTIONS[ErrorCategory.UNKNOWN])

    @classmethod
    def enrich_error_info(cls, error_message: str) -> Dict[str, Any]:
        """
        丰富错误信息，添加分类和建议

        Args:
            error_message: 原始错误消息

        Returns:
            包含分类、严重程度、建议等的字典
        """
        category, severity = cls.classify_error(error_message)
        suggestion = cls.get_suggestion(error_message)

        return {
            "category": category.value,
            "severity": severity.value,
            "suggestion": {
                "title": suggestion.title,
                "description": suggestion.description,
                "solutions": suggestion.solutions
            }
        }
