"""修复未使用变量问题...."""
import re
import sys
from pathlib import Path


def fix_unused_vars(file_path):
    """修复指定文件中的未使用变量问题...."""
    content = Path(file_path).read_text(encoding="utf-8")
    lines = content.splitlines()

    # 获取flake8报告的未使用变量
    import subprocess

    result = subprocess.run(
        f"flake8 {file_path} --select=F841 --format='%(row)d:%(col)d:%(code)s:%(text)s'",  # noqa: E501
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
            var_match = re.search(r"local variable '(\w+)' is", parts[3])
            if var_match:
                var_name = var_match.group(1)
                line_fixes[line_num] = var_name

    # 修复问题
    modified = False
    for line_num, var_name in line_fixes.items():
        if line_num <= len(lines):
            line = lines[line_num - 1]
            # 注释掉这一行
            lines[line_num - 1] = f"# {line}  # 未使用变量: {var_name}"
            modified = True

    if modified:
        Path(file_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"修复了 {file_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_unused_vars(sys.argv[1])
    else:
        print("请提供文件路径")
