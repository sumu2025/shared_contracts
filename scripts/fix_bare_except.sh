#!/bin/bash
# 修复裸异常问题
for file in $(flake8 . --max-line-length=88 --extend-ignore=E203 --select=E722 --format="%(path)s" | sort -u); do
    echo "处理文件: $file"
    python scripts/fix_tools/fix_bare_except.py $file
done
