"""
元素选择器工具

提供交互式元素选择功能，帮助用户快速生成稳定的选择器
"""
from typing import Dict, Any, List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)


class ElementPickerTimeout(Exception):
    """元素选择器超时异常"""
    pass


class ElementPicker:
    """
    元素选择器工具

    功能：
    - 交互式选择页面元素
    - 生成多种选择器策略（ID、Name、Class、XPath等）
    - 评估选择器稳定性
    - 提取元素属性
    """

    def __init__(self, default_timeout: int = 30000):
        """
        初始化元素选择器

        Args:
            default_timeout: 默认超时时间（毫秒）
        """
        self.default_timeout = default_timeout

    async def pick_element(self, page) -> Dict[str, Any]:
        """
        交互式拾取元素

        Args:
            page: Playwright Page 对象

        Returns:
            {
                "success": bool,
                "element_info": {
                    "attributes": dict,
                    "selectors": list,
                    "recommended_selector": dict
                },
                "error": str (如果失败)
            }
        """
        try:
            # 1. 注入选择模式
            await self._inject_picker_mode(page)

            # 2. 等待用户选择元素
            await self._wait_for_element_selection(page)

            # 3. 获取选中的元素
            element_data = await page.evaluate("window.__pickedElement")

            if not element_data:
                return {
                    "success": False,
                    "error": "未获取到选中的元素"
                }

            # 4. 生成选择器
            selectors = self._generate_selectors(element_data)

            # 5. 评估稳定性
            stable_selectors = self._assess_stability(selectors["selectors"])

            # 6. 推荐最佳选择器
            recommended = self._recommend_best_selector(stable_selectors)

            # 7. 清理选择模式
            await self._cleanup_picker_mode(page)

            return {
                "success": True,
                "element_info": {
                    "attributes": element_data,
                    "selectors": stable_selectors,
                    "recommended_selector": recommended
                }
            }

        except asyncio.TimeoutError:
            logger.error("元素选择超时")
            await self._cleanup_picker_mode(page)
            return {
                "success": False,
                "error": "元素选择超时，请重试"
            }
        except Exception as e:
            logger.error(f"元素选择失败: {e}")
            await self._cleanup_picker_mode(page)
            return {
                "success": False,
                "error": str(e)
            }

    async def _inject_picker_mode(self, page) -> None:
        """
        注入元素选择模式到页面

        Args:
            page: Playwright Page 对象
        """
        injection_script = """
        () => {
            window.__elementPickerMode = true;

            // 清除之前的事件监听器
            if (window.__elementPickerCleanup) {
                window.__elementPickerCleanup();
            }

            // 创建高亮样式
            const style = document.createElement('style');
            style.id = '__elementPickerStyles';
            style.textContent = `
                __ELEMENT_PICKER_HIGHLIGHT {
                    outline: 2px solid #ff0000 !important;
                    outline-offset: 2px;
                    cursor: crosshair !important;
                    background-color: rgba(255, 0, 0, 0.1) !important;
                }
            `;
            document.head.appendChild(style);

            // 生成 XPath
            window.__getXPath = function(element) {
                if (element.id !== '') {
                    return "//*[@id='" + element.id + "']";
                }
                if (element === document.body) {
                    return element.tagName.toLowerCase();
                }

                const ix = Array.from(element.parentNode.children).indexOf(element) + 1;
                return (
                    window.__getXPath(element.parentNode) +
                    "/" +
                    element.tagName.toLowerCase() +
                    "[" +
                    ix +
                    "]"
                );
            };

            // 获取元素属性
            window.__getElementAttributes = function(element) {
                const attrs = {
                    tag: element.tagName.toLowerCase(),
                    id: element.id || null,
                    name: element.getAttribute('name') || null,
                    class: element.getAttribute('class') || null,
                    type: element.getAttribute('type') || null,
                    href: element.getAttribute('href') || null,
                    src: element.getAttribute('src') || null,
                    placeholder: element.getAttribute('placeholder') || null
                };

                // 获取所有 data-* 属性
                for (let attr of element.attributes) {
                    if (attr.name.startsWith('data-')) {
                        attrs[attr.name] = attr.value;
                    }
                }

                return attrs;
            };

            // 事件处理函数
            const handleMouseOver = (e) => {
                e.target.style.outline = '2px solid red';
                e.target.style.outlineOffset = '2px';
                e.target.style.cursor = 'crosshair';
                e.stopPropagation();
            };

            const handleMouseOut = (e) => {
                e.target.style.outline = '';
                e.target.style.outlineOffset = '';
                e.target.style.cursor = '';
                e.stopPropagation();
            };

            const handleClick = (e) => {
                e.preventDefault();
                e.stopPropagation();

                const element = e.target;

                // 存储选中的元素信息
                window.__pickedElement = window.__getElementAttributes(element);

                // 生成并存储 XPath
                window.__pickedElement.xpath = window.__getXPath(element);

                // 移除所有事件监听器
                document.removeEventListener('mouseover', handleMouseOver);
                document.removeEventListener('mouseout', handleMouseOut);
                document.removeEventListener('click', handleClick);

                // 移除样式
                const styleElement = document.getElementById('__elementPickerStyles');
                if (styleElement) {
                    styleElement.remove();
                }

                // 标记选择完成
                window.__elementPickingComplete = true;
            };

            // 添加事件监听器
            document.addEventListener('mouseover', handleMouseOver, true);
            document.addEventListener('mouseout', handleMouseOut, true);
            document.addEventListener('click', handleClick, true);

            // 清理函数
            window.__elementPickerCleanup = () => {
                document.removeEventListener('mouseover', handleMouseOver);
                document.removeEventListener('mouseout', handleMouseOut);
                document.removeEventListener('click', handleClick);

                const styleElement = document.getElementById('__elementPickerStyles');
                if (styleElement) {
                    styleElement.remove();
                }

                // 清理高亮样式
                document.querySelectorAll('*').forEach(el => {
                    el.style.outline = '';
                    el.style.outlineOffset = '';
                    el.style.cursor = '';
                });
            };
        }
        """

        await page.evaluate(injection_script)
        logger.info("✓ 元素选择模式已注入")

    async def _wait_for_element_selection(self, page, timeout: Optional[int] = None) -> None:
        """
        等待用户选择元素

        Args:
            page: Playwright Page 对象
            timeout: 超时时间（毫秒）

        Raises:
            ElementPickerTimeout: 超时异常
        """
        timeout = timeout or self.default_timeout

        try:
            await page.wait_for_function(
                "window.__elementPickingComplete === true",
                timeout=timeout
            )
            logger.info("✓ 元素选择完成")
        except Exception as e:
            raise ElementPickerTimeout(f"等待元素选择超时: {e}")

    def _generate_selectors(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成多种选择器策略

        Args:
            element_data: 元素数据

        Returns:
            {
                "selectors": [
                    {"type": "id", "value": "#element", "stability": 10},
                    {"type": "name", "value": "[name='element']", "stability": 8},
                    ...
                ]
            }
        """
        selectors = []
        tag = element_data.get("tag", "*")

        # 1. ID 选择器（最稳定）
        if element_data.get("id"):
            selectors.append({
                "type": "id",
                "value": f"#{element_data['id']}",
                "stability": 10
            })

        # 2. Name 选择器
        if element_data.get("name"):
            selectors.append({
                "type": "name",
                "value": f"[name='{element_data['name']}']",
                "stability": 8
            })

        # 3. Class 选择器
        if element_data.get("class"):
            classes = element_data['class'].split()
            # 选择第一个类名
            if classes:
                selectors.append({
                    "type": "class",
                    "value": f".{classes[0]}",
                    "stability": 6
                })

        # 4. Data 属性选择器
        data_attrs = {k: v for k, v in element_data.items() if k.startswith('data-')}
        for attr_name, attr_value in data_attrs.items():
            if attr_value:
                selectors.append({
                    "type": "data-attribute",
                    "value": f"[{attr_name}='{attr_value}']",
                    "stability": 9
                })

        # 5. Tag 选择器（最不稳定）
        selectors.append({
            "type": "tag",
            "value": tag,
            "stability": 2
        })

        # 6. XPath 选择器
        xpath = self._generate_xpath(element_data)
        if xpath:
            selectors.append({
                "type": "xpath",
                "value": xpath,
                "stability": 4
            })

        return {"selectors": selectors}

    def _generate_xpath(self, element_data: Dict[str, Any]) -> Optional[str]:
        """
        生成 XPath 选择器

        Args:
            element_data: 元素数据

        Returns:
            XPath 字符串
        """
        tag = element_data.get("tag", "*")

        # 优先使用 ID
        if element_data.get("id"):
            return f"//*[@id='{element_data['id']}']"

        # 使用 Name
        if element_data.get("name"):
            return f"//{tag}[@name='{element_data['name']}']"

        # 使用 Class
        if element_data.get("class"):
            classes = element_data['class'].split()
            if classes:
                return f"//{tag}[@class='{classes[0]}']"

        # 使用 Text 内容（如果有）
        if element_data.get("text"):
            return f"//{tag}[contains(text(), '{element_data['text']}]"

        # 默认使用标签
        return f"//{tag}"

    def _assess_stability(self, selectors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        评估选择器稳定性

        Args:
            selectors: 选择器列表

        Returns:
            带稳定性评分的选择器列表
        """
        # 稳定性评估规则
        stability_rules = {
            "id": 10,          # ID 最稳定
            "data-attribute": 9, # Data 属性很稳定
            "name": 8,         # Name 较稳定
            "class": 6,        # Class 中等稳定
            "xpath": 4,        # XPath 较不稳定
            "tag": 2           # Tag 最不稳定
        }

        for selector in selectors:
            selector_type = selector["type"]
            base_stability = selector.get("stability", 0)

            # 根据类型调整稳定性
            if selector_type in stability_rules:
                # 取设定的稳定性和类型稳定性的较大值
                selector["stability"] = max(base_stability, stability_rules[selector_type])

            # 添加稳定性描述
            if selector["stability"] >= 8:
                selector["stability_level"] = "high"
            elif selector["stability"] >= 5:
                selector["stability_level"] = "medium"
            else:
                selector["stability_level"] = "low"

        return selectors

    def _recommend_best_selector(self, selectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        推荐最佳选择器

        Args:
            selectors: 选择器列表

        Returns:
            稳定性最高的选择器
        """
        if not selectors:
            return {
                "type": "none",
                "value": "",
                "stability": 0
            }

        # 按稳定性排序，返回最高的
        sorted_selectors = sorted(selectors, key=lambda x: x["stability"], reverse=True)
        return sorted_selectors[0]

    async def _cleanup_picker_mode(self, page) -> None:
        """
        清理选择模式

        Args:
            page: Playwright Page 对象
        """
        cleanup_script = """
        () => {
            if (window.__elementPickerCleanup) {
                window.__elementPickerCleanup();
            }

            // 清理全局变量
            delete window.__elementPickerMode;
            delete window.__elementPickingComplete;
            delete window.__pickedElement;
            delete window.__getXPath;
            delete window.__getElementAttributes;
            delete window.__elementPickerCleanup;

            // 移除所有高亮样式
            document.querySelectorAll('*').forEach(el => {
                el.style.outline = '';
                el.style.outlineOffset = '';
                el.style.cursor = '';
            });
        }
        """

        try:
            await page.evaluate(cleanup_script)
            logger.info("✓ 元素选择模式已清理")
        except Exception as e:
            logger.warning(f"清理选择模式时出现警告: {e}")

    async def _extract_attributes(self, element) -> Dict[str, Any]:
        """
        提取元素属性（备用方法，如果页面脚本失败）

        Args:
            element: Playwright ElementHandle

        Returns:
            属性字典
        """
        try:
            attrs = {
                "tag": await element.evaluate("el => el.tagName.toLowerCase()"),
                "id": await element.get_attribute("id"),
                "name": await element.get_attribute("name"),
                "class": await element.get_attribute("class"),
                "type": await element.get_attribute("type"),
                "href": await element.get_attribute("href"),
                "src": await element.get_attribute("src"),
                "placeholder": await element.get_attribute("placeholder")
            }

            # 提取所有 data-* 属性
            all_attrs = await element.evaluate("""
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        if (attr.name.startsWith('data-')) {
                            attrs[attr.name] = attr.value;
                        }
                    }
                    return attrs;
                }
            """)

            attrs.update(all_attrs)

            return {k: v for k, v in attrs.items() if v is not None}

        except Exception as e:
            logger.error(f"提取元素属性失败: {e}")
            return {}
