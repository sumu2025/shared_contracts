#!/bin/bash
# 运行所有测试并生成覆盖率报告的脚本

set -e  # 错误时退出

echo "=== 开始测试和覆盖率分析 ==="

# 确保脚本权限
# 首先运行使所有脚本可执行
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
chmod +x "$CURRENT_DIR/make_scripts_executable.sh"
"$CURRENT_DIR/make_scripts_executable.sh"

# 确保环境变量设置
export TESTING=1
export PYTHONPATH=.

# 命令行参数处理
COVERAGE=1
TEST_TYPE="all"
TEST_PATTERN=""

# 帮助信息
function show_help {
    echo "使用: $0 [选项]"
    echo "选项:"
    echo "  -t, --type        测试类型: unit, integration, all (默认: all)"
    echo "  -p, --pattern     测试模式，用于过滤测试"
    echo "  -c, --coverage    是否生成覆盖率报告: 0, 1 (默认: 1)"
    echo "  -h, --help        显示此帮助信息"
    exit 1
}

# 解析参数
while [[ $# -gt 0 ]]; do
  case $1 in
    -t|--type)
      TEST_TYPE="$2"
      shift 2
      ;;
    -p|--pattern)
      TEST_PATTERN="$2"
      shift 2
      ;;
    -c|--coverage)
      COVERAGE="$2"
      shift 2
      ;;
    -h|--help)
      show_help
      ;;
    *)
      echo "未知选项: $1"
      show_help
      ;;
  esac
done

# 根据测试类型设置命令
if [ "$TEST_TYPE" = "unit" ]; then
    TEST_CMD="tests/"
    echo "运行单元测试"
elif [ "$TEST_TYPE" = "integration" ]; then
    TEST_CMD="integration_tests/"
    echo "运行集成测试"
else
    TEST_CMD="tests/ integration_tests/"
    echo "运行所有测试"
fi

# 添加测试模式
if [ -n "$TEST_PATTERN" ]; then
    TEST_CMD="$TEST_CMD -k '$TEST_PATTERN'"
    echo "使用测试模式: $TEST_PATTERN"
fi

# 设置覆盖率参数
if [ "$COVERAGE" = "1" ]; then
    COV_ARGS="--cov=agentforge_contracts --cov-report=term --cov-report=xml:coverage.xml --cov-report=html:htmlcov"
    echo "将生成覆盖率报告"
else
    COV_ARGS=""
    echo "不生成覆盖率报告"
fi

# 运行测试
echo "运行命令: pytest $TEST_CMD $COV_ARGS -v"
eval "poetry run pytest $TEST_CMD $COV_ARGS -v"

# 显示覆盖率摘要
if [ "$COVERAGE" = "1" ]; then
    echo "=== 覆盖率摘要 ==="
    poetry run coverage report

    # 计算并显示总覆盖率
    TOTAL_COV=$(poetry run coverage report | grep TOTAL | awk '{print $NF}' | tr -d '%')
    echo "总覆盖率: $TOTAL_COV%"

    # 检查覆盖率是否达到阈值
    THRESHOLD=80
    if (( $(echo "$TOTAL_COV < $THRESHOLD" | bc -l) )); then
        echo "警告: 测试覆盖率 ($TOTAL_COV%) 低于阈值 ($THRESHOLD%)"
    else
        echo "测试覆盖率 ($TOTAL_COV%) 达到或超过阈值 ($THRESHOLD%)"
    fi

    echo "详细HTML报告生成在: htmlcov/index.html"
fi

echo "=== 测试和覆盖率分析完成 ==="
