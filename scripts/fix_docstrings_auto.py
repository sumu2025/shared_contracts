#!/usr/bin/env python3
"""自动修复文档字符串问题的脚本...."""
import ast
import os
import re
from pathlib import Path


def fix_file_docstrings(file_path):
    """修复文件中的文档字符串问题...."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加句点到文档字符串第一行结尾
        def add_period(match):
            docstring = match.group(1)
            lines = docstring.split('\n')
            if lines[0].strip() and not lines[0].strip().endswith('.'):
                lines[0] = lines[0].rstrip() + '.'
            return '"""' + '\n'.join(lines) + '...."""'
        
        # 修复文档字符串格式
        pattern = r'"""(.*?)...."""'
        new_content = re.sub(pattern, add_period, content, flags=re.DOTALL)
        
        # 修复一行式文档字符串格式问题
        new_content = re.sub(r'"""\s*(.*?)\s*...."""', r'"""\1...."""', new_content)
        
        # 如果内容有变化，写回文件
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"修复了 {file_path}")
            return True
        return False
    except Exception as e:
        print(f"处理 {file_path} 时出错: {e}")
        return False

def main():
    """主函数，遍历项目文件并修复文档字符串...."""
    root_dir = Path(__file__).parent.parent
    fixed_count = 0
    total_count = 0
    
    for path in root_dir.glob('**/*.py'):
        if not any(p in str(path) for p in ['.venv', '__pycache__', '.git']):
            total_count += 1
            if fix_file_docstrings(path):
                fixed_count += 1
    
    print(f"总共处理了 {total_count} 个文件，修复了 {fixed_count} 个文件")

if __name__ == "__main__":
    main()
