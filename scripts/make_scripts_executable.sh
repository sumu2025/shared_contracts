#!/bin/bash
# 确保所有脚本具有执行权限

# 当前脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 找到所有.sh脚本以及Python脚本并添加执行权限
find "$SCRIPT_DIR" -name "*.sh" -type f -exec chmod +x {} \;
find "$SCRIPT_DIR" -name "*.py" -type f -exec chmod +x {} \;

# 也设置自身为可执行
chmod +x "$0"

# 列出所有脚本及其权限
echo "脚本权限设置完成:"
ls -la "$SCRIPT_DIR"/*.sh

echo "所有脚本已设置为可执行"
