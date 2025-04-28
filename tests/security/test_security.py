"""安全测试模块，用于验证安全实践和防护措施。"""

import re
import os
from pathlib import Path
import pytest
import inspect
import importlib
import pkgutil
from typing import Dict, List, Set, Tuple

# 敏感方法列表（需要特别关注的方法）
SENSITIVE_METHODS = {
    "eval", "exec", "os.system", "subprocess.call", "subprocess.run",
    "subprocess.Popen", "pickle.loads", "yaml.load", "__reduce__",
}

# 密码和密钥相关的变量名模式
SECRET_PATTERNS = [
    r"password",
    r"passwd",
    r"secret",
    r"key",
    r"token",
    r"credential",
    r"api[_-]?key",
    r"auth",
]


def get_python_files(directory: str) -> List[str]:
    """
    获取目录中的所有Python文件。

    Args:
        directory: 要搜索的目录

    Returns:
        Python文件路径列表
    """
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files


def scan_for_sensitive_code(file_path: str) -> List[Tuple[int, str, str]]:
    """
    扫描文件中的敏感代码。

    Args:
        file_path: 文件路径

    Returns:
        包含行号、代码和敏感方法的元组列表
    """
    findings = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            # 忽略注释
            if line.startswith("#"):
                continue
            
            # 检查敏感方法
            for method in SENSITIVE_METHODS:
                pattern = r"\b" + re.escape(method) + r"\s*\("
                if re.search(pattern, line):
                    findings.append((i, line, method))
                    
    return findings


def scan_for_hardcoded_secrets(file_path: str) -> List[Tuple[int, str, str]]:
    """
    扫描文件中的硬编码密钥和凭据。

    Args:
        file_path: 文件路径

    Returns:
        包含行号、代码和模式的元组列表
    """
    findings = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            # 忽略注释和测试数据
            if line.startswith("#") or "test" in file_path.lower():
                continue
            
            # 检查变量赋值
            for pattern in SECRET_PATTERNS:
                var_pattern = r"\b" + pattern + r"\b\s*=\s*['\"]([^'\"]+)['\"]"
                matches = re.finditer(var_pattern, line, re.IGNORECASE)
                for match in matches:
                    # 忽略空值、占位符和模板值
                    value = match.group(1)
                    if (value and 
                        len(value) > 3 and  # 忽略短值
                        value != "None" and 
                        not value.startswith("${") and 
                        not value.startswith("<<") and
                        "placeholder" not in value.lower() and
                        "example" not in value.lower() and
                        "test" not in value.lower()):
                        findings.append((i, line, pattern))
                    
    return findings


def check_input_validation(module_name: str) -> List[str]:
    """
    检查模块中的输入验证。

    Args:
        module_name: 模块名称

    Returns:
        缺少输入验证的函数列表
    """
    findings = []
    try:
        module = importlib.import_module(module_name)
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                # 检查函数是否有类型注解
                sig = inspect.signature(obj)
                for param_name, param in sig.parameters.items():
                    if param.annotation == inspect.Parameter.empty and param_name != "self":
                        findings.append(f"{module_name}.{name} 缺少类型注解: {param_name}")
                
                # 检查函数体中是否有参数检查
                source = inspect.getsource(obj)
                has_validation = False
                for param_name in sig.parameters:
                    if param_name != "self":
                        if re.search(r"\b" + re.escape(param_name) + r"\b.*?assert", source):
                            has_validation = True
                            break
                        if re.search(r"\bif\b.*?\b" + re.escape(param_name) + r"\b", source):
                            has_validation = True
                            break
                
                if not has_validation and len(sig.parameters) > 0:
                    findings.append(f"{module_name}.{name} 可能缺少输入验证")
    except (ImportError, AttributeError):
        # 模块不存在或无法检查
        pass
    
    return findings


def test_no_sensitive_code():
    """测试代码中没有敏感方法。"""
    core_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core")
    monitoring_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "monitoring")
    utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "utils")
    
    all_findings = []
    
    for directory in [core_dir, monitoring_dir, utils_dir]:
        py_files = get_python_files(directory)
        for file in py_files:
            findings = scan_for_sensitive_code(file)
            if findings:
                all_findings.append((file, findings))
    
    # 特定的例外情况
    exceptions = {
        "utils/testing_utils.py": {"subprocess.run", "subprocess.call"},  # 测试工具允许使用子进程
        "monitoring/log_processor.py": {"subprocess.Popen"},  # 日志处理器允许使用子进程
    }
    
    # 过滤掉例外情况
    filtered_findings = []
    for file, file_findings in all_findings:
        file_basename = os.path.basename(file)
        allowed_methods = set()
        for exc_file, exc_methods in exceptions.items():
            if exc_file in file:
                allowed_methods.update(exc_methods)
        
        filtered_file_findings = []
        for line_no, line, method in file_findings:
            if method not in allowed_methods:
                filtered_file_findings.append((line_no, line, method))
        
        if filtered_file_findings:
            filtered_findings.append((file, filtered_file_findings))
    
    # 格式化输出
    error_message = ""
    for file, file_findings in filtered_findings:
        error_message += f"\n文件 {file} 中包含敏感代码:\n"
        for line_no, line, method in file_findings:
            error_message += f"  - 行 {line_no}: 使用了 {method}：{line}\n"
    
    assert not filtered_findings, error_message


def test_no_hardcoded_secrets():
    """测试代码中没有硬编码的密钥和凭据。"""
    core_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core")
    monitoring_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "monitoring")
    utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "utils")
    
    all_findings = []
    
    for directory in [core_dir, monitoring_dir, utils_dir]:
        py_files = get_python_files(directory)
        for file in py_files:
            # 跳过测试文件
            if "test_" in file or "/tests/" in file:
                continue
                
            findings = scan_for_hardcoded_secrets(file)
            if findings:
                all_findings.append((file, findings))
    
    # 格式化输出
    error_message = ""
    for file, file_findings in all_findings:
        error_message += f"\n文件 {file} 中包含硬编码的密钥或凭据:\n"
        for line_no, line, pattern in file_findings:
            error_message += f"  - 行 {line_no}: 匹配模式 '{pattern}'：{line}\n"
    
    assert not all_findings, error_message


def test_data_sanitization():
    """测试数据消毒机制。"""
    # 检查LogFireClient是否有数据消毒方法
    from shared_contracts.monitoring.implementations.logfire_client import LogFireClient
    
    # 创建测试客户端
    from shared_contracts.monitoring.implementations.logfire_config import LogFireConfig
    
    config = LogFireConfig(
        api_key="test-key",
        service_name="security-test",
        environment="test"
    )
    client = LogFireClient(config)
    
    # 测试_sanitize_data方法
    assert hasattr(client, "_sanitize_data"), "LogFireClient应该有_sanitize_data方法"
    
    # 测试敏感数据被消毒
    test_data = {
        "username": "user123",
        "password": "secret123",  # 应该被消毒
        "api_key": "abc123",      # 应该被消毒
        "token": "token123",      # 应该被消毒
        "description": "This is a test",
        "nested": {
            "secret": "value123",  # 应该被消毒
            "normal": "normal_value"
        }
    }
    
    sanitized = client._sanitize_data(test_data)
    
    assert sanitized["username"] == "user123", "非敏感数据不应被消毒"
    assert sanitized["password"] == "***REDACTED***", "密码应该被消毒"
    assert sanitized["api_key"] == "***REDACTED***", "API密钥应该被消毒"
    assert sanitized["token"] == "***REDACTED***", "令牌应该被消毒"
    assert sanitized["description"] == "This is a test", "描述不应被消毒"
    assert sanitized["nested"]["secret"] == "***REDACTED***", "嵌套密钥应该被消毒"
    assert sanitized["nested"]["normal"] == "normal_value", "嵌套非敏感数据不应被消毒"


if __name__ == "__main__":
    test_no_sensitive_code()
    test_no_hardcoded_secrets()
    test_data_sanitization()
    print("所有安全测试通过!")
