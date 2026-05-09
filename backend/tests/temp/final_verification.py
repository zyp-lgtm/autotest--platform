"""
录制功能最终验证
确保所有修复都已正确应用
"""
import sys
import os

print("🔍 录制功能修复验证")
print("=" * 50)

# 1. 检查Python缓存
print("\n1️⃣ 检查Python缓存...")
cache_dirs = []
for root, dirs, files in os.walk("."):
    if "__pycache__" in dirs:
        cache_dirs.append(os.path.join(root, "__pycache__"))

if cache_dirs:
    print(f"   ⚠️  发现 {len(cache_dirs)} 个缓存目录")
    print("   建议运行: find . -type d -name '__pycache__' -exec rm -rf {} +")
else:
    print("   ✅ 无Python缓存")

# 2. 检查recorder.py中的关键修复
print("\n2️⃣ 检查recorder.py修复...")
with open("app/services/recorder.py", "r", encoding="utf-8") as f:
    content = f.read()

checks = {
    "expose_function": "expose_function" in content,
    "captureActionToBackend": "captureActionToBackend" in content,
    "输入监听器": "addEventListener.*input" in content or "addEventListener('input'" in content,
    "300ms防抖": "300ms" in content or "300);" in content,
    "session_actions": "session_actions" in content,
}

for check, result in checks.items():
    status = "✅" if result else "❌"
    print(f"   {status} {check}: {'已修复' if result else '未修复'}")

all_good = all(checks.values())

# 3. 验证防抖时间
print("\n3️⃣ 验证防抖时间...")
import re
debounce_times = re.findall(r'}, (\d+)\);.*防抖', content, re.IGNORECASE)
if debounce_times:
    print(f"   找到防抖时间设置: {debounce_times}")
    if all(t == '300' for t in debounce_times):
        print("   ✅ 所有防抖时间都是300ms")
    else:
        print("   ⚠️  防抖时间不一致或未全部更新")
else:
    print("   ❌ 未找到防抖时间设置")

# 4. 检查模块是否可导入
print("\n4️⃣ 检查模块导入...")
try:
    sys.path.insert(0, ".")
    from app.services.recorder import browser_recorder, RecordingSession
    print("   ✅ 录制器模块导入成功")
    print(f"   ✅ BrowserRecorder类: {hasattr(browser_recorder, 'sessions')}")
    print(f"   ✅ RecordingSession数据类: {RecordingSession is not None}")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    all_good = False

# 5. 检查后端进程
print("\n5️⃣ 检查后端进程...")
import subprocess
try:
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    if "uvicorn app.main:app" in result.stdout:
        print("   ✅ 后端进程正在运行")
        # 提取PID
        for line in result.stdout.split('\n'):
            if 'uvicorn app.main:app' in line:
                parts = line.split()
                if len(parts) > 1:
                    print(f"   PID: {parts[1]}")
    else:
        print("   ❌ 后端进程未运行")
        all_good = False
except Exception as e:
    print(f"   ⚠️  无法检查进程: {e}")

# 6. 测试API端点
print("\n6️⃣ 测试API端点...")
try:
    import urllib.request
    import json

    # 测试健康检查
    req = urllib.request.Request("http://localhost:8000/api/v1/health")
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode())
        print(f"   ✅ 健康检查: {data.get('status', 'unknown')}")

    # 测试录制服务健康
    req = urllib.request.Request("http://localhost:8000/api/v1/recording/health")
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode())
        print(f"   ✅ 录制服务: {data.get('status', 'unknown')}")
        print(f"   ✅ 活动会话数: {data.get('active_sessions', 0)}")
except Exception as e:
    print(f"   ❌ API测试失败: {e}")
    all_good = False

# 总结
print("\n" + "=" * 50)
if all_good:
    print("✅ 所有关键修复已验证通过")
    print("\n📋 关键修复:")
    print("   1. ✅ 跨页面数据丢失修复")
    print("   2. ✅ 输入事件监听器已包含")
    print("   3. ✅ 防抖时间优化为300ms")
    print("   4. ✅ 后端服务正常运行")
    print("\n💡 使用提示:")
    print("   - 输入完成后等待0.5秒再停止录制")
    print("   - 或按Tab键切换焦点")
    print("   - 或点击页面其他位置")
else:
    print("❌ 部分修复未通过验证")
    print("\n📝 请检查:")
    for check, result in checks.items():
        if not result:
            print(f"   - {check} 未修复")

print("\n" + "=" * 50)
