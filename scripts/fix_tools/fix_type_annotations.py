#!/usr/bin/env python3
"""
修复类型注解的工具

此脚本检查并修复项目中Python文件的类型注解问题，
包括缺少的类型提示和不正确的类型注..."""

import ast
import importlib
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


def get_return_type_hint(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Optional[str]:  # noqa: E501
    """
    获取函数的返回类型提示。

    Args:
        func_node: 函数AST节点

    Returns:
        返回类型提示，如果存在；否则为None
 ..."""
    if func_node.returns:
        return ast.unparse(func_node.returns)
    return None


def get_arg_type_hints(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Dict[str, str]:  # noqa: E501
    """
    获取函数参数的类型提示。

    Args:
        func_node: 函数AST节点

    Returns:
        参数名到类型提示的映射
 ..."""
    arg_types = {}
    
    # 处理普通参数
    for arg in func_node.args.args:
        if arg.annotation:
            arg_types[arg.arg] = ast.unparse(arg.annotation)
        else:
            arg_types[arg.arg] = None
    
    # 处理 *args 参数
    if func_node.args.vararg and func_node.args.vararg.annotation:
        arg_types[f"*{func_node.args.vararg.arg}"] = ast.unparse(func_node.args.vararg.annotation)  # noqa: E501
    elif func_node.args.vararg:
        arg_types[f"*{func_node.args.vararg.arg}"] = None
    
    # 处理 **kwargs 参数
    if func_node.args.kwarg and func_node.args.kwarg.annotation:
        arg_types[f"**{func_node.args.kwarg.arg}"] = ast.unparse(func_node.args.kwarg.annotation)  # noqa: E501
    elif func_node.args.kwarg:
        arg_types[f"**{func_node.args.kwarg.arg}"] = None
    
    return arg_types


def analyze_function_body(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Tuple[Set[str], Optional[str]]:  # noqa: E501
    """
    分析函数体以推断参数和返回类型。

    Args:
        func_node: 函数AST节点

    Returns:
        参数名集合和推断的返回类型
 ..."""
    used_vars = set()
    return_type = None
    
    class VarVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                used_vars.add(node.id)
            self.generic_visit(node)
        
        def visit_Return(self, node):
            nonlocal return_type
            # 这里简单推断，实际需要更复杂的类型推断逻辑
            if node.value:
                if isinstance(node.value, ast.Dict):
                    return_type = "Dict"
                elif isinstance(node.value, ast.List):
                    return_type = "List"
                elif isinstance(node.value, ast.Tuple):
                    return_type = "Tuple"
                elif isinstance(node.value, ast.Set):
                    return_type = "Set"
                elif isinstance(node.value, ast.Str):
                    return_type = "str"
                elif isinstance(node.value, ast.Num):
                    if isinstance(node.value.n, int):
                        return_type = "int"
                    else:
                        return_type = "float"
                elif isinstance(node.value, ast.NameConstant):
                    if node.value.value is None:
                        return_type = "None"
                    elif isinstance(node.value.value, bool):
                        return_type = "bool"
            self.generic_visit(node)
    
    visitor = VarVisitor()
    visitor.visit(func_node)
    
    # 过滤掉不是参数的变量
    arg_names = {arg.arg for arg in func_node.args.args}
    if func_node.args.vararg:
        arg_names.add(func_node.args.vararg.arg)
    if func_node.args.kwarg:
        arg_names.add(func_node.args.kwarg.arg)
    
    used_args = used_vars.intersection(arg_names)
    
    return used_args, return_type


def suggest_type_annotations(file_path: str) -> List[str]:
    """
    分析文件并提出类型注解建议。

    Args:
        file_path: 文件路径

    Returns:
        建议列表
 ..."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return [f"解析错误: {e}"]
    
    suggestions = []
    
    # 分析所有函数定义
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            
            # 检查返回类型
            return_hint = get_return_type_hint(node)
            if not return_hint and node.name != "__init__":
                # 分析函数体尝试推断类型
                _, inferred_return = analyze_function_body(node)
                if inferred_return:
                    suggestions.append(f"函数 {func_name}: 考虑添加返回类型提示 -> {inferred_return}")  # noqa: E501
                else:
                    suggestions.append(f"函数 {func_name}: 缺少返回类型提示")
            
            # 检查参数类型
            arg_types = get_arg_type_hints(node)
            missing_args = [arg for arg, type_hint in arg_types.items() if type_hint is None]  # noqa: E501
            if missing_args:
                # 分析函数体尝试确定哪些参数实际使用了
                used_args, _ = analyze_function_body(node)
                for arg in missing_args:
                    if arg in used_args or not arg.startswith(("*", "**")):
                        suggestions.append(f"函数 {func_name}: 参数 '{arg}' 缺少类型提示")
    
    return suggestions


def main():
    """运行类型注解修复工具。...."""
    # 获取项目根目录
    root_dir = Path(__file__).parents[2].absolute()
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:]]
    else:
        # 默认处理所有Python文件
        files = list(root_dir.glob('**/*.py'))
        # 排除某些目录
        files = [f for f in files if not any(x in str(f) for x in [
            '.git', '__pycache__', '.mypy_cache', '.pytest_cache', '.venv', 'build', 'dist'  # noqa: E501
        ])]
    
    total_suggestions = 0
    total_files = 0
    
    for file_path in files:
        print(f"分析: {file_path}")
        suggestions = suggest_type_annotations(str(file_path))
        
        if suggestions:
            print(f"  发现 {len(suggestions)} 个建议:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
            total_suggestions += len(suggestions)
        else:
            print("  没有发现问题!")
        
        total_files += 1
        print()
    
    print(f"分析完成! 检查了 {total_files} 个文件，提出了 {total_suggestions} 个类型注解建议。")
    if total_suggestions > 0:
        print(f"请手动修复这些问题，或使用mypy生成的报告作为指导。")


if __name__ == "__main__":
    main()
