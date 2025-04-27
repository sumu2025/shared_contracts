"""修复未使用全局声明问题"""
import sys
from pathlib import Path


def fix_unused_global(file_path):
    """修复指定文件中的未使用全局声明问题"""
    content = Path(file_path).read_text(encoding="utf-8")
    lines = content.splitlines()

    # 获取flake8报告
    import subprocess

    result = subprocess.run(
        f"flake8 {file_path} --select=F824 --format='%(row)d:%(col)d:%(code)s:%(text)s'",  # noqa: E501
        shell=True,
        capture_output=True,
        text=True,
    )

    # 解析结果
    line_fixes = {}
    for issue in result.stdout.splitlines():
        parts = issue.split(":")
        if len(parts) >= 4:
            line_num = int(parts[0])
            line_fixes[line_num] = True

    # 修复问题
    modified = False
    for line_num in line_fixes:
        if line_num <= len(lines):
            # 注释掉这一行
            lines[line_num - 1] = f"# {lines[line_num-1]}  # 未使用的全局声明"
            modified = True

    if modified:
        Path(file_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"修复了 {file_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_unused_global(sys.argv[1])
    else:
        print("请提供文件路径")
