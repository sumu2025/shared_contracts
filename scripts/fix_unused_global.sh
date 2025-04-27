#!/bin/bash
# 修复未使用全局声明问题
for file in $(flake8 . --max-line-length=88 --extend-ignore=E203 --select=F824 --format="%(path)s" | sort -u); do
    echo "处理文件: $file"
    python scripts/fix_tools/fix_unused_global.py $file
done
