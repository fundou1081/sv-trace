"""Scope 体系公共工具函数

从 semantic/utils.py 迁移。
"""

import pyslang


def extract_identifier(node) -> str:
    """从 AST 节点提取标识符名称
    
    处理各种标识符节点类型：
    - Identifier (Token)
    - IdentifierName (SyntaxNode → Token)
    - IdentifierSelectName (嵌套结构)
    """
    if not node:
        return ""
    
    # 直接有 text 属性
    if hasattr(node, 'text') and node.text:
        return node.text
    
    # Token 有 value 属性
    if hasattr(node, 'value') and node.value:
        return str(node.value)
    
    # 遍历子节点找 Token
    try:
        for child in node:
            if isinstance(child, pyslang.Token):
                if child.value:
                    return child.value
            result = extract_identifier(child)
            if result:
                return result
    except (TypeError, AttributeError):
        pass
    
    return ""


def get_node_text(node) -> str:
    """获取节点的文本表示"""
    if not node:
        return ""
    
    if hasattr(node, 'text') and node.text:
        return node.text
    
    try:
        parts = []
        for child in node:
            parts.append(get_node_text(child))
        return "".join(parts)
    except (TypeError, AttributeError):
        pass
    
    return str(node) if node else ""


def get_span_info(node) -> dict:
    """获取节点的位置信息"""
    if not hasattr(node, 'span') or not node.span:
        return {}
    
    return {
        'start_line': node.span.start_line,
        'start_column': node.span.start_column,
        'end_line': node.span.end_line,
        'end_column': node.span.end_column,
    }
