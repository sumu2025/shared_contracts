"""修复裸异常问题"""
import re
import sys
from pathlib import Path


def fix_bare_except(file_path):
    """修复指定文件中的裸异常问题"""
    content = Path(file_path).read_text(encoding="utf-8")
    lines = content.splitlines()

    modified = False
    for i, line in enumerate(lines):
        if re.search(r"^\s*except\s*:", line):
            # 用Exception替换裸异常
            lines[i] = re.sub(r"except\s*:", "except Exception:", line)
            modified = True

    if modified:
        Path(file_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"修复了 {file_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_bare_except(sys.argv[1])
    else:
        print("请提供文件路径")
