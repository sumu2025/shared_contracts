#!/bin/bash
# 修复行过长问题
for file in $(flake8 . --max-line-length=88 --extend-ignore=E203 --select=E501 --format="%(path)s" | sort -u); do
    echo "处理文件: $file"
    python scripts/fix_tools/fix_long_lines.py $file
done
