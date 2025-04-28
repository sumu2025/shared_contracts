# 代码风格指南和自动修复工具

本文档介绍了本项目的代码风格规范及自动修复工具的使用方法。

## 代码风格规范

本项目采用以下代码风格规范：

1. **PEP 8**：遵循Python官方风格指南，但有以下调整：
   - 行长度限制为88个字符（而非PEP 8中的79个字符）
   - 使用Black格式化工具的默认风格

2. **导入排序**：使用isort按照以下规则排序：
   - 标准库
   - 第三方库
   - 本地导入

3. **文档字符串**：
   - 所有模块、类、函数和方法都应有文档字符串
   - 文档字符串第一行应以句点结束
   - 使用Google风格的文档字符串格式

4. **类型注解**：
   - 所有函数和方法应有类型注解
   - 使用最新的类型注解语法（Python 3.10+）

## 自动修复工具

我们提供了一系列自动化工具来帮助维护代码质量：

### 一键修复

使用以下命令一键修复大部分代码风格问题：

```bash
./scripts/fix_all_auto.sh
```

这个脚本将执行以下操作：
1. 修复文档字符串问题
2. 使用Black格式化代码
3. 使用isort修复导入排序
4. 修复长行问题
5. 为剩余问题添加noqa标记
6. 再次检查剩余问题

### 个别修复工具

如果你只想解决特定问题，可以使用以下单独的工具：

#### 修复文档字符串

```bash
poetry run python scripts/fix_docstrings_auto.py
```

#### 格式化代码

```bash
poetry run black .
```

#### 修复导入排序

```bash
poetry run isort .
```

#### 修复长行

```bash
poetry run python scripts/fix_remaining_long_lines.py
```

#### 添加noqa标记

```bash
poetry run python scripts/add_noqa.py
```

## Git提交前自动检查

本项目使用pre-commit钩子在提交前自动检查代码质量。安装和使用方法：

1. 安装pre-commit：

```bash
poetry run pre-commit install
```

2. 现在每次提交代码前，pre-commit将自动检查并尝试修复代码风格问题。

## CI/CD集成

CI/CD流程中也集成了代码风格检查：

1. 代码风格检查
2. 类型检查
3. 单元测试
4. 构建和部署

如果CI检查失败，请在本地运行 `./scripts/fix_all_auto.sh` 自动修复问题，然后重新提交。

## 常见问题

### 1. 如何处理无法自动修复的问题？

对于无法自动修复的问题，你可以：
- 手动修复
- 在特定行添加 `# noqa: 错误代码` 注释来忽略特定错误

### 2. 如何暂时跳过pre-commit检查？

```bash
git commit -m "提交信息" --no-verify
```

### 3. 如何更新pre-commit钩子？

```bash
poetry run pre-commit autoupdate
```
