#!/bin/bash
# 本地构建脚本
set -e

echo "=== 清理先前构建 ==="
rm -rf dist/ build/ *.egg-info

echo "=== 运行验证 ==="
bash scripts/validate.sh

echo "=== 构建包 ==="
poetry build

echo "=== 构建完成 ==="
ls -la dist/
