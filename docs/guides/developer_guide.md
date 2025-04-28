# 开发者指南

本指南旨在帮助开发者正确设置环境，并解决使用shared_contracts时可能遇到的常见问题。

## 目录

- [环境设置](#环境设置)
- [依赖管理](#依赖管理)
- [代码风格](#代码风格)
- [测试指南](#测试指南)
- [CI/CD流程](#cicd流程)
- [常见问题排查](#常见问题排查)

## 环境设置

### 基本环境要求

- Python 3.10 或更高版本
- Poetry 1.2.0 或更高版本（依赖管理工具）
- Git

### 设置开发环境

1. 克隆仓库：
   ```bash
   git clone <repository-url>
   cd shared_contracts
   ```

2. 使用Poetry安装依赖：
   ```bash
   poetry install --with dev
   ```

3. 激活虚拟环境：
   ```bash
   poetry shell
   ```

4. 设置pre-commit钩子：
   ```bash
   pre-commit install
   ```

## 依赖管理

### 重要版本要求

- **Pydantic**: 必须使用2.0.0或更高版本。该项目使用了Pydantic v2的API功能。
- **Python**: 需要3.10或更高版本，以支持所有语言特性。

### 解决依赖冲突

如果你遇到了依赖版本冲突，特别是与Pydantic相关的冲突，请按照以下步骤解决：

1. 检查当前安装的Pydantic版本：
   ```python
   python -c "import pydantic; print(pydantic.__version__)"
   ```

2. 如果版本低于2.0.0，请更新：
   ```bash
   poetry add pydantic@^2.5.2
   ```

3. 如果仍然有冲突，可能需要检查其他包的依赖：
   ```bash
   poetry show --tree
   ```

4. 对于顽固的依赖冲突，考虑使用独立的虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   pip install -e .
   ```

## 代码风格

本项目使用以下代码风格工具：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码样式检查
- **mypy**: 类型检查

### 运行风格检查

使用以下命令检查代码风格：

```bash
# 使用脚本一键检查
./scripts/validate.sh

# 或分别运行各工具
poetry run black . --check --line-length=88
poetry run isort . --check --profile black
poetry run flake8 . --max-line-length=88 --extend-ignore=E203
poetry run mypy .
```

### 自动修复风格问题

```bash
# 格式化代码
poetry run black .
poetry run isort .

# 对于其他问题，可以使用自动修复脚本
./scripts/fix_all_flake8.sh
```

## 测试指南

### 运行测试

```bash
# 运行所有单元测试
poetry run pytest

# 查看详细输出
poetry run pytest -v

# 运行特定测试文件
poetry run pytest tests/test_core_models.py

# 生成覆盖率报告
poetry run pytest --cov=agentforge_contracts tests/ --cov-report=term
```

### 编写测试

- 所有测试都应该放在`tests/`目录下
- 测试文件应以`test_`开头
- 测试函数应以`test_`开头
- 使用pytest fixtures来设置和清理测试环境

```python
import pytest
from agentforge_contracts.core.models.base_models import BaseModel

def test_base_model_validation():
    # 测试代码
    ...
```

## CI/CD流程

本项目使用GitHub Actions进行持续集成和部署。

### CI流程

每次推送到`main`或`develop`分支，或者创建指向这些分支的Pull Request时，都会触发CI流程，包括：

1. **验证**: 代码风格检查和类型检查
2. **测试**: 运行单元测试和生成覆盖率报告
3. **构建**: 构建Python包
4. **部署**: 仅在主分支上触发，部署到指定环境

### 本地验证

在提交代码前，强烈建议运行本地验证脚本，确保代码符合项目标准：

```bash
./scripts/validate.sh
```

## 常见问题排查

### 1. 依赖版本冲突

**问题**: 导入包时报错，如`ImportError: cannot import name 'Field' from 'pydantic'`。

**解决方案**:
- 检查Pydantic版本，确保是2.x版本
- 更新依赖：`poetry update`
- 如有必要，重新创建虚拟环境

### 2. 代码风格检查失败

**问题**: CI流程中代码风格检查失败。

**解决方案**:
- 运行本地自动修复：`poetry run black . && poetry run isort .`
- 使用提供的修复脚本：`./scripts/fix_all_flake8.sh`
- 手动解决长行问题：`./scripts/fix_long_lines.sh`

### 3. 类型检查错误

**问题**: mypy报告类型错误。

**解决方案**:
- 查看错误详情：`poetry run mypy --namespace-packages --explicit-package-bases .`
- 添加正确的类型注解
- 对于第三方库，可能需要添加类型存根：`poetry add --dev types-<package>`

### 4. 测试失败

**问题**: 单元测试或集成测试失败。

**解决方案**:
- 运行单个测试以定位问题：`poetry run pytest path/to/test.py::test_function -v`
- 检查测试环境和依赖
- 确保mock对象行为与预期一致
