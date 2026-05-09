"""
测试 JWT_SECRET 配置
"""
import sys
sys.path.insert(0, '.')

import os

# 确保没有设置 JWT_SECRET 环境变量
if 'JWT_SECRET' in os.environ:
    del os.environ['JWT_SECRET']

from app.core.config import get_settings

print('=== 测试配置加载 ===')
settings = get_settings()

print(f'JWT_SECRET 长度: {len(settings.JWT_SECRET)}')
print(f'JWT_SECRET 类型: {type(settings.JWT_SECRET)}')
print(f'JWT_SECRET (前8字符): {settings.JWT_SECRET[:8]}...')
print(f'JWT_ALGORITHM: {settings.JWT_ALGORITHM}')

# 验证密钥是安全的
if settings.JWT_SECRET == 'secret-key':
    print('❌ 错误: 仍在使用不安全的默认密钥')
elif len(settings.JWT_SECRET) < 32:
    print(f'❌ 错误: JWT_SECRET 太短（{len(settings.JWT_SECRET)} < 32）')
else:
    print('✅ JWT_SECRET 配置安全（自动生成）')

print('\n=== 测试环境变量设置 ===')
os.environ['JWT_SECRET'] = 'my-production-secret-key-32-chars-long-secure'

# 清除缓存
from app.core import config
import importlib
importlib.reload(config)

from app.core.config import get_settings
settings2 = get_settings()

print(f'环境变量设置后: {settings2.JWT_SECRET}')
if settings2.JWT_SECRET == 'my-production-secret-key-32-chars-long-secure':
    print('✅ 环境变量优先级正确')
else:
    print('❌ 环境变量优先级不正确')
