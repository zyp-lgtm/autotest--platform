# 请在录制浏览器的控制台执行以下测试

## 步骤 1: 打开控制台
1. 启动一个新的录制
2. 当浏览器打开后，按 **F12** 打开控制台
3. 确保在 Console 标签页

## 步骤 2: 复制粘贴以下代码（一次性全部粘贴）

```javascript
// 检查录制脚本状态
console.log('=== 诊断测试 ===');
console.log('1. 录制脚本:', window.__recording ? '✅ 已加载' : '❌ 未加载');
console.log('2. 后端函数:', window.captureActionToBackend ? '✅ 可用' : '❌ 不可用');

// 检查是否有compositionend监听器
var hasCompositionListener = false;
var eventListeners = window.getEventListeners ? window.getEventListeners(document) : [];
console.log('3. 事件监听器数量:', eventListeners.length);

// 手动测试输入
var input = document.querySelector('#searchInput');
if (input) {
    console.log('4. 找到搜索框: ✅');

    // 保存初始值
    var initialValue = input.value;

    // 设置值并触发事件
    input.value = '测试手动输入';
    console.log('5. 已设置输入值为:', input.value);

    // 触发input事件
    input.dispatchEvent(new Event('input', { bubbles: true }));
    console.log('6. 已触发 input 事件');

    // 等待后检查
    setTimeout(function() {
        if (window.__recording) {
            var actions = window.__recording.actions;
            console.log('7. 捕获的操作数:', actions.length);

            var inputActions = actions.filter(a => a.action_type === 'input');
            console.log('8. 输入操作数:', inputActions.length);

            if (inputActions.length > 0) {
                console.log('✅ 成功！输入监听器工作正常');
                console.log('输入详情:', inputActions);
            } else {
                console.log('❌ 问题：没有捕获到输入操作');
                console.log('所有操作:', actions);
            }
        } else {
            console.log('❌ 录制脚本未加载');
        }

        // 恢复初始值
        input.value = initialValue;
    }, 500);
} else {
    console.log('❌ 未找到搜索框，请先导航到 Wikipedia');
}

console.log('=== 测试完成 ===');
```

## 步骤 3: 告诉我结果

请把控制台的输出结果（特别是标号7、8的那两行）告诉我。

特别是：
- **捕获的操作数**是多少？
- **输入操作数**是多少？
- 如果是0，说明输入监听器确实没有工作
- 如果大于0，说明功能正常

---

## 或者：更简单的测试

如果上面的测试太复杂，请直接告诉我：

1. **控制台有没有出现红色的错误？**
2. **在输入框中输入文字后，控制台有没有出现任何 `[录制]` 开头的日志？**
