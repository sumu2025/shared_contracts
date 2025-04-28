#!/usr/bin/env python3
"""
修复文档字符串格式的工具

此脚本检查并修复项目中的Python文件的文档字符串格式问题，
使其符合Google风格指..."""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def extract_docstring(node: ast.AST) -> Optional[str]:
    """
    从AST节点中提取文档字符串。

    Args:
        node: AST节点

    Returns:
        文档字符串，如果存在；否则为None
 ..."""
    if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):  # noqa: E501
        return None
    
    if not node.body:
        return None
    
    first = node.body[0]
    if not isinstance(first, ast.Expr):
        return None
    
    if not isinstance(first.value, ast.Str):
        return None
    
    return first.value.s


def fix_google_style_docstring(docstring: str) -> str:
    """
    修复Google风格的文档字符串格式。

    Args:
        docstring: 原始文档字符串

    Returns:
        修复后的文档字符串
 ..."""
    if not docstring:
        return ""
    
    # 去除前后空白
    docstring = docstring.strip()
    
    # 确保第一行后有空行（如果有多行）
    lines = docstring.split("\n")
    if len(lines) > 1:
        # 确保第一段后有空行
        if lines[1].strip():
            lines.insert(1, "")
    
    # 修复Args, Returns, Raises等部分的格式
    sections = ["Args", "Returns", "Raises", "Yields", "Examples", "Attributes", "Note"]
    in_section = None
    for i, line in enumerate(lines):
        # 检查部分标题
        section_match = re.match(r'^(\s*)(' + '|'.join(sections) + r')[\s:]*$', line)
        if section_match:
            indent, section = section_match.groups()
            lines[i] = f"{indent}{section}:"
            in_section = section
            # 确保部分标题后有内容或空行
            if i+1 < len(lines) and not lines[i+1].strip():
                continue
            if i+1 < len(lines) and not lines[i+1].startswith(indent + "    "):
                lines.insert(i+1, indent + "    ")
        
        # 修复参数描述格式
        if in_section == "Args" and ":" in line and not line.endswith(":"):
            param_match = re.match(r'^(\s*)([a-zA-Z0-9_]+)\s*:\s*(.+)$', line)
            if param_match:
                indent, param, desc = param_match.groups()
                lines[i] = f"{indent}{param}: {desc}"
    
    return "\n".join(lines)


def fix_file_docstrings(file_path: str) -> Tuple[int, List[str]]:
    """
    修复文件中的所有文档字符串。

    Args:
        file_path: 文件路径

    Returns:
        修复的文档字符串数量和问题信息列表
 ..."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return 0, [f"解析错误: {e}"]
    
    fixed_count = 0
    issues = []
    
    # 递归处理所有节点
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):  # noqa: E501
            docstring = extract_docstring(node)
            if docstring:
                fixed_docstring = fix_google_style_docstring(docstring)
                if fixed_docstring != docstring:
                    fixed_count += 1
                    node_name = getattr(node, 'name', 'module') if hasattr(node, 'name') else 'unknown'  # noqa: E501
                    issues.append(f"修复 {node_name} 的文档字符串")
    
    # 如果有修复，写回文件
    if fixed_count > 0:
        # 这里只是概念演示，实际修复需要更复杂的代码处理，
        # 因为ast不保留原始格式，直接写回可能会破坏代码格式
        # 在实际实现中，需要使用更精细的工具如tokenize或专门的文档字符串修复库
        issues.append("注意：此脚本仅检测问题，不实际修改文件。请手动修复上述问题。")
    
    return fixed_count, issues


def main():
    """运行文档字符串修复工具。...."""
    parser = argparse.ArgumentParser(description='修复Python文件的文档字符串格式')
    parser.add_argument('files', nargs='*', help='要检查的文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅检查，不修改文件')
    args = parser.parse_args()
    
    # 获取项目根目录
    root_dir = Path(__file__).parents[2].absolute()
    
    # 确定要处理的文件
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        # 默认处理所有Python文件
        files = list(root_dir.glob('**/*.py'))
        # 排除某些目录
        files = [f for f in files if not any(x in str(f) for x in [
            '.git', '__pycache__', '.mypy_cache', '.pytest_cache', '.venv', 'build', 'dist'  # noqa: E501
        ])]
    
    total_fixed = 0
    total_files = 0
    
    for file_path in files:
        print(f"处理: {file_path}")
        fixed, issues = fix_file_docstrings(str(file_path))
        if issues:
            print('\n'.join(f"  - {issue}" for issue in issues))
        total_fixed += fixed
        total_files += 1
    
    print(f"\n处理完成! 检查了 {total_files} 个文件，发现 {total_fixed} 个文档字符串问题。")
    if total_fixed > 0 and args.dry_run:
        print("使用 --fix 选项可以自动修复这些问题（功能尚未实现）")


if __name__ == "__main__":
    main()
