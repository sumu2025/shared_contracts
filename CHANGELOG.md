# Changelog

所有对shared_contracts的重要更改都将记录在此文件中。

格式基于[Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
且本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增

- 测试框架完善：
  - 添加标准化的测试工具和夹具（tests/helpers目录）
  - 添加模拟服务实现，用于集成测试
  - 添加特定业务流程的参数化测试
  - 创建标准化测试数据目录和示例文件
  - 添加覆盖率配置和报告生成功能

- CI/CD流程优化：
  - 添加自动依赖版本检查，特别是确保pydantic版本 >= 2.0.0
  - 添加代码风格自动修复功能，减少因格式问题导致的CI失败
  - 添加`auto_format.sh`脚本用于本地和CI环境中的代码格式化
  - 添加基于LogFire的CI/CD监控模块，用于跟踪构建、测试和部署状态
  - 添加`run_integration_tests.sh`集成测试运行脚本
  - 添加`run_tests.sh`统一测试运行脚本

- 项目配置文件：
  - 添加requirements.txt文件支持非Poetry用户
  - 添加setup.cfg配置文件，统一所有工具配置
  - 确保脚本文件可执行

- 文档更新：
  - 添加开发者指南（`docs/guides/developer_guide.md`）
  - 添加CI/CD指南（`docs/ci_cd_guide.md`）
  - 添加代码风格指南（`docs/guides/code_style_guide.md`）
  - 更新故障排除文档，包含更详细的依赖问题解决方案
  - 更新README文件，介绍新的CI/CD流程

### 修改

- 更新CI工作流配置：
  - 优化依赖安装，明确使用`--with dev`标志
  - 添加依赖版本检查步骤
  - 添加自动代码格式化逻辑
  - 确保脚本具有执行权限

- 更新pre-commit配置：
  - 添加Pydantic版本检查钩子
  - 为mypy添加命名空间包支持
  - 明确注释指示自动格式化功能

### 修复

- 改进依赖管理以解决版本冲突问题，特别是确保pydantic 2.x兼容性
- 确保所有bash脚本具有执行权限
- 实现更加鲁棒的CI工作流，减少因格式问题导致的失败

## [0.1.0] - 2023-11-01

### 新增

- 初始项目结构
- 核心数据模型
- 服务接口定义
- 监控组件
- 工具函数
