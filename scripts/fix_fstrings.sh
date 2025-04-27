#!/bin/bash
# 修复f-string问题
for file in $(flake8 . --max-line-length=88 --extend-ignore=E203 --select=F541 --format="%(path)s" | sort -u); do
    echo "处理文件: $file"
    python scripts/fix_tools/fix_fstrings.py $file
done
