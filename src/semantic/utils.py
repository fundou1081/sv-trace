"""Semantic 工具函数

公共 AST 提取工具，消除重复代码
符合铁律 1: 纯 AST 遍历
"""

import pyslang


def extract_identifier(node) -> str:
    """从 AST 节点提取标识符 - 纯 AST
    
    支持:
    - Identifier: 直接包含名称
    - IdentifierName: 包含 Identifier 子节点
    - 其他节点: 递归查找子节点
    
    Args:
        node: pyslang AST 节点
        
    Returns:
        标识符名称，未找到返回空字符串
    """
    if node is None:
        return ""
    if not hasattr(node, 'kind'):
        return ""
    
    kind = node.kind.name
    
    # Identifier 直接包含名称
    if kind == 'Identifier':
        return str(getattr(node, 'value', '')) or str(node).strip()
    
    # IdentifierName 包含 Identifier 子节点
    if kind == 'IdentifierName':
        try:
            for child in list(node):
                if hasattr(child, 'kind') and child.kind.name == 'Identifier':
                    return str(getattr(child, 'value', '')) or str(child).strip()
        except:
            pass
        # fallback
        return str(node).strip()
    
    # 从子节点递归提取
    try:
        for child in list(node):
            if hasattr(child, 'kind'):
                result = extract_identifier(child)
                if result:
                    return result
    except:
        pass
    
    return ""


def extract_lhs_from_assignment(node) -> str:
    """从赋值表达式提取左侧标识符
    
    支持:
    - NonblockingAssignmentExpression: children[0] 是 LHS
    - AssignmentExpression: children[0] 是 LHS
    - ContinuousAssign: 需要特殊处理
    
    Args:
        node: 赋值表达式节点
        
    Returns:
        左侧标识符名称
    """
    if node is None:
        return ""
    if not hasattr(node, 'kind'):
        return ""
    
    kind = node.kind.name
    
    # NonblockingAssignmentExpression / AssignmentExpression
    # 结构: [IdentifierName, Operator, ...]
    if kind in ('NonblockingAssignmentExpression', 'AssignmentExpression'):
        try:
            children = list(node)
            if children and hasattr(children[0], 'kind'):
                return extract_identifier(children[0])
        except:
            pass
    
    return ""
