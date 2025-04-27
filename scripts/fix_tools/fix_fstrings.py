"""修复f-string缺少占位符的问题"""
import re
import sys
from pathlib import Path


def fix_fstrings(file_path):
    """修复指定文件中的f-string问题"""
    content = Path(file_path).read_text(encoding="utf-8")
    # 查找不含{}的f-string
    pattern = r'f"([^{]*)"'

    # 替换为普通字符串
    fixed_content = re.sub(pattern, r'"\1"', content)

    if fixed_content != content:
        Path(file_path).write_text(fixed_content, encoding="utf-8")
        print(f"修复了 {file_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_fstrings(sys.argv[1])
    else:
        print("请提供文件路径")
