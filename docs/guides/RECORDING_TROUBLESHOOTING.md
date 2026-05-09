# 录制功能诊断检查清单

**日期**: 2026-04-30
**版本**: v1.5.3

---

## 📋 诊断步骤

### 第一步：确认后端正常运行

```bash
# 检查后端进程
ps aux | grep uvicorn | grep -v grep

# 检查后端健康状态
curl http://localhost:8000/api/v1/health

# 应该返回:
# {"status":"healthy","database":"connected","cache_status":"active"}
```

### 第二步：启动一个新的录制会话

1. 打开前端: http://localhost:3000
2. 登录 (demo/demo123)
3. 进入录制功能
4. 输入场景名称: "测试输入捕获"
5. 点击"开始录制"
6. 浏览器会自动打开

### 第三步：执行测试操作（**重要：按顺序**）

```
1. 在浏览器地址栏输入: https://www.wikipedia.org/
2. 等待页面完全加载（2-3秒）
3. 点击搜索框（中间的大搜索框）
4. 输入: hello
5. ⏰ 等待 1 秒（重要！）
6. 点击页面其他位置（或按Tab键）
7. 再等待 1 秒（重要！）
8. 回到前端，点击"停止录制"
```

### 第四步：检查捕获结果

应该看到：
```
✅ 导航到: https://www.wikipedia.org/
✅ 点击: #searchInput
✅ 输入: #searchInput = 'hello'    ← 这个必须有！
```

---

## 🐛 如果还是没有输入操作

### 可能原因1: 防抖时间未到

**症状**: 只看到导航和点击，没有输入

**解决**:
```
✅ 输入完成后等待 1 秒（而不是立即停止）
✅ 或按 Tab 键切换焦点
✅ 或点击页面其他位置
```

### 可能原因2: 输入速度太快

**症状**: 部分输入被捕获

**解决**:
```
✅ 慢一点输入，每字之间间隔 100ms
✅ 输入完成后等待 2 秒
```

### 可能原因3: 浏览器控制台有错误

**检查**:
```
1. 按 F12 打开开发者工具
2. 切换到 Console 标签
3. 查看是否有红色错误
4. 应该看到: [录制] ✅ 录制脚本已加载
```

### 可能原因4: 使用了旧的浏览器实例

**解决**:
```
✅ 完全关闭所有浏览器窗口
✅ 重新启动录制
✅ 使用新的浏览器实例
```

---

## 🔍 手动测试脚本

在浏览器控制台执行以下代码，手动测试输入捕获：

```javascript
// 1. 检查录制脚本是否加载
console.log('录制脚本状态:', window.__recording ? '✅ 已加载' : '❌ 未加载');

// 2. 检查expose_function是否可用
console.log('后端函数状态:', window.captureActionToBackend ? '✅ 可用' : '❌ 不可用');

// 3. 手动触发一个输入操作
if (window.__recording) {
    window.__recording.captureAction({
        action_type: 'input',
        selector: '#test',
        value: '手动测试',
        page_url: window.location.href,
        page_title: document.title
    });
    console.log('✅ 已手动触发输入操作');
}

// 4. 检查捕获的操作
setTimeout(() => {
    if (window.__recording) {
        console.log('捕获的操作数:', window.__recording.actions.length);
        console.log('操作列表:', window.__recording.actions);
    }
}, 100);
```

---

## 📞 联系支持

如果以上步骤都试过了还是不行：

1. **截图**: 提供前端显示的捕获操作列表
2. **控制台日志**: F12 → Console 标签，截图所有日志
3. **后端日志**: `tail -100 /tmp/backend.log`
4. **具体操作**: 描述您执行了哪些操作

---

## ✅ 成功案例

参考这个成功的测试：

```
✅ 成功！捕获了 2 个输入操作
📋 输入操作详情:
   1. #searchInput = 'hello'
   2. #searchInput = 'hello world'
```

**关键操作**:
1. 输入 'hello'
2. 等待 400ms
3. 继续输入 ' world'
4. 等待 400ms
5. 停止录制

**总耗时**: 约 5-6 秒

---

**最后更新**: 2026-04-30
**测试状态**: ✅ 后端功能正常
**常见问题**: 等待时间不足
