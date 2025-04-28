#!/usr/bin/env python3
"""验证修复脚本。"""

import sys
print(f"Python 版本: {sys.version}")
print("开始验证修复...")

try:
    print("1. 尝试导入 base_models...")
    from core.models.base_models import BaseModel
    print("✅ 成功导入 BaseModel")
    
    # 测试使用
    class TestModel(BaseModel):
        name: str
        
    test = TestModel(name="测试")
    print(f"✅ 成功创建 BaseModel 子类实例: {test}")
    
    print("2. 尝试导入 LogFireClient...")
    from monitoring.implementations.logfire_client import LogFireClient
    print("✅ 成功导入 LogFireClient")
    
    print("所有修复验证成功!")
except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
