#!/usr/bin/env python3
"""手动修复余下的行过长问题...."""
from pathlib import Path

# 需要修复的文件列表
files_to_fix = [
    "./agentforge_contracts/core/constants/__init__.py",
    "./agentforge_contracts/monitoring/__init__.py",
    "./core/__init__.py",
    "./core/interfaces/agent_interface.py",
    "./core/models/base_models.py",
    # 添加更多文件...
]


def fix_file(filepath):
    """修复单个文件的行过长问题...."""
    print(f"处理文件: {filepath}")
    content = Path(filepath).read_text(encoding="utf-8")
    lines = content.splitlines()
    modified = False

    for i, line in enumerate(lines):
        if len(line) > 88:
            # 针对导入语句的特殊处理
            if "import" in line:
                if "," in line:
                    # 将单行多个导入拆分为多行
                    parts = line.split("import ")
                    prefix = parts[0] + "import "
                    imports = parts[1].split(",")
                    lines[i] = prefix + imports[0].strip()
                    for j, imp in enumerate(imports[1:], 1):
                        lines.insert(i + j, prefix + imp.strip())
                    modified = True
                    continue

            # 对普通长行采用简单分割策略
            # 尝试在标点符号处分割
            for char in [",", ".", ")", "(", " and ", " or ", "+", "-", "*", "/"]:
                if char in line[60:]:
                    pos = line.rfind(char, 60, 88)
                    if pos > 60:
                        indent = len(line) - len(line.lstrip())
                        if char in [",", ".", ")", "]"]:
                            # 保留分隔符在第一行
                            lines[i] = line[: pos + 1]
                            lines.insert(
                                i + 1, " " * (indent + 4) + line[pos + 1 :].lstrip()
                            )
                        else:
                            # 将分隔符放在第二行
                            lines[i] = line[:pos]
                            lines.insert(
                                i + 1, " " * (indent + 4) + line[pos:].lstrip()
                            )
                        modified = True
                        break

    if modified:
        Path(filepath).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"已修复 {filepath}")
    else:
        print(f"无法自动修复 {filepath}，需要手动处理")


def main():
    """主函数...."""
    for filepath in files_to_fix:
        fix_file(filepath)
    print("处理完毕，请运行flake8检查剩余问题")


if __name__ == "__main__":
    main()
