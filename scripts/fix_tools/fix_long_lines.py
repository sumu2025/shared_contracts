"""修复行过长问题的脚本...."""
import sys
from pathlib import Path


def fix_long_lines(file_path):
    """修复指定文件中的行过长问题...."""
    content = Path(file_path).read_text(encoding="utf-8")
    lines = content.splitlines()
    modified = False

    for i, line in enumerate(lines):
        if len(line) > 88 and not line.lstrip().startswith("#"):
            # 尝试简单的行分割策略
            if "," in line[70:]:
                # 在逗号处分割
                split_pos = line.rindex(",", 70, 88) + 1
                indent = len(line) - len(line.lstrip())
                lines[i] = line[:split_pos].rstrip()
                lines.insert(i + 1, " " * (indent + 4) + line[split_pos:].lstrip())
                modified = True

    if modified:
        Path(file_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"修复了 {file_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_long_lines(sys.argv[1])
    else:
        print("请提供文件路径")
