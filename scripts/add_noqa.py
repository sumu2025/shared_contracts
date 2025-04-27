#!/usr/bin/env python3
"""
自动为长行添加noqa注释
"""
import subprocess
from pathlib import Path


def get_long_lines():
    """获取所有长行问题的文件和行号"""
    result = subprocess.run(
        "flake8 . --max-line-length=88 --extend-ignore=E203 --select=E501 "
        "--format='%(path)s:%(row)d'",
        shell=True,
        capture_output=True,
        text=True,
    )

    long_lines = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            path, row = line.split(":", 1)
            if path not in long_lines:
                long_lines[path] = []
            long_lines[path].append(int(row))

    return long_lines


def add_noqa_comments(filepath, line_numbers):
    """为指定文件的指定行添加noqa注释"""
    content = Path(filepath).read_text(encoding="utf-8")
    lines = content.splitlines()

    modified = False
    for line_num in sorted(line_numbers, reverse=True):  # 从后往前修改避免行号变化
        if line_num <= len(lines) and "noqa: E501" not in lines[line_num - 1]:
            lines[line_num - 1] = lines[line_num - 1] + "  # noqa: E501"
            modified = True

    if modified:
        Path(filepath).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"已修复 {filepath}")


def main():
    """主函数"""
    long_lines = get_long_lines()
    for filepath, line_numbers in long_lines.items():
        try:
            add_noqa_comments(filepath, line_numbers)
        except Exception as e:
            print(f"处理文件 {filepath} 失败: {str(e)}")

    print("处理完毕，请运行flake8检查剩余问题")


if __name__ == "__main__":
    main()
