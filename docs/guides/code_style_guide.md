# 代码风格指南

本文档提供了shared_contracts项目的代码风格规范和最佳实践，帮助所有贡献者保持一致的编码风格。

## 风格约定

我们使用以下工具和配置来保证代码质量和一致性：

### Black

- 行长度限制: 88字符
- 使用双引号作为字符串默认引号
- 自动格式化，无需手动调整大多数格式问题

```bash
# 检查格式
black . --check --line-length=88

# 自动修复格式
black . --line-length=88
```

### isort

- 使用与Black兼容的配置 (profile=black)
- 行长度限制: 88字符
- 按照标准库、第三方库、本地库的顺序排序导入

```bash
# 检查导入排序
isort . --check --profile black --line-length=88

# 自动修复导入排序
isort . --profile black --line-length=88
```

### flake8

- 行长度限制: 88字符
- 忽略E203错误（与Black冲突的空格相关错误）
- 检查代码样式和潜在错误

```bash
# 运行flake8检查
flake8 . --max-line-length=88 --extend-ignore=E203
```

### mypy

- 使用严格类型检查
- 支持命名空间包
- 要求显式类型注解

```bash
# 运行类型检查
mypy --namespace-packages --explicit-package-bases .
```

## 命名规范

- **类名**: 使用驼峰命名法 (例如: `BaseModel`, `AgentConfig`)
- **函数和变量**: 使用蛇形命名法 (例如: `get_agent`, `user_id`)
- **常量**: 使用大写蛇形命名法 (例如: `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **私有成员**: 使用单下划线前缀 (例如: `_internal_method`)

## 注释规范

- 使用docstring为所有公共函数、类和模块提供文档
- 使用Google风格的docstring格式
- 包含参数、返回值和异常的描述

```python
def function_name(param1: str, param2: int) -> bool:
    """简短描述函数功能.
    
    详细描述函数功能和使用场景。多行描述应该对齐。
    
    Args:
        param1: 第一个参数的描述
        param2: 第二个参数的描述
        
    Returns:
        返回值的描述
        
    Raises:
        ValueError: 可能引发的异常及条件
    """
    # 函数实现
    ...
```

## 自动化工具

我们提供了多个自动化工具来简化代码风格管理：

### 本地自动格式化

使用以下命令在提交前自动格式化代码：

```bash
./scripts/auto_format.sh
```

### 修复特定问题

我们提供了针对特定问题的修复脚本：

- `./scripts/fix_long_lines.sh`: 修复过长的代码行
- `./scripts/fix_bare_except.sh`: 修复裸异常语句
- `./scripts/fix_fstrings.sh`: 将旧式字符串格式转换为f-strings
- `./scripts/fix_all_flake8.sh`: 修复所有flake8报告的问题

### pre-commit钩子

在本地开发时，始终使用pre-commit钩子来自动检查代码：

```bash
# 安装pre-commit钩子
pre-commit install

# 手动运行所有钩子
pre-commit run --all-files
```

## 最佳实践

1. **始终使用类型注解**: 明确函数参数和返回值的类型
2. **保持函数简短**: 每个函数应该只做一件事
3. **避免深度嵌套**: 保持代码的平坦结构，避免多层嵌套
4. **模块化设计**: 将相关功能组织到独立模块中
5. **测试覆盖**: 为所有新代码编写单元测试
6. **定期运行验证脚本**: 使用`./scripts/validate.sh`检查代码质量
