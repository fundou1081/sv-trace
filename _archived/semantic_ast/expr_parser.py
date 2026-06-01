"""
semantic_ast.expr_parser - 表达式解析辅助函数

基于 pyslang 实验发现的 API，用于从 AST 节点提取标识符和表达式信息。

关键发现:
- AssignmentExpression / NonblockingAssignmentExpression 有 .left / .right 属性
- IdentifierNameSyntax 有 .identifier.valueText
- IntegerVectorExpression 有 .value.valueText (Token 类型)
- 二元表达式有 .left / .right 属性，括号表达式有 .expression 属性
"""

import pyslang
from typing import List, Set, Optional, Any
from dataclasses import dataclass, field


def get_identifier_text(node) -> str:
    """从 IdentifierNameSyntax 节点提取标识符文本
    
    Args:
        node: IdentifierNameSyntax 节点或其子节点
    
    Returns:
        标识符的文本值
    
    Example:
        ident = node.identifier  # IdentifierSyntax
        name = ident.valueText     # 'signal_name'
    """
    if node is None:
        return ''
    
    # 直接是 identifier 属性
    ident = getattr(node, 'identifier', None)
    if ident is not None:
        return getattr(ident, 'valueText', '') or ''
    
    # 直接是 Token 类型
    if hasattr(node, 'valueText'):
        return getattr(node, 'valueText', '') or ''
    
    return getattr(node, 'text', '') or ''


def get_integer_text(node) -> str:
    """从整数表达式节点提取文本
    
    支持:
    - IntegerVectorExpression: 8'hFF → value.valueText = 'FF'
    - IntegerLiteralExpression: literal.valueText
    - IntegerLiteral: text
    """
    if node is None:
        return ''
    
    kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
    
    if kn == 'IntegerVectorExpression':
        # 8'hFF 类型的表达式
        val = getattr(node, 'value', None)
        if val and hasattr(val, 'valueText'):
            return getattr(val, 'valueText', '') or ''
    
    elif kn == 'IntegerLiteralExpression':
        lit = getattr(node, 'literal', None)
        if lit:
            return getattr(lit, 'valueText', '') or getattr(lit, 'text', '') or ''
    
    elif kn == 'IntegerLiteral':
        return getattr(node, 'text', '') or ''
    
    return getattr(node, 'text', '') or ''


@dataclass
class DriverInfo:
    """驱动信息"""
    lhs: str                           # 左值信号名
    rhs_identifiers: List[str] = field(default_factory=list)  # 右值中的标识符
    rhs_literals: List[str] = field(default_factory=list)    # 右值中的字面量
    kind: str = ""                     # always_ff, always_comb, continuous
    clock: str = ""
    reset: str = ""
    line: int = 0


def collect_expression_identifiers(node, result: List[str], _visited: Set[int] = None) -> None:
    """递归收集表达式中的所有标识符和字面量
    
    这个函数是 expr_parser 的核心，用于从任意表达式节点提取
    所有的标识符和字面量。
    
    算法:
    1. 如果是 IdentifierNameSyntax，提取 identifier.valueText
    2. 如果是整数表达式，提取相应的文本
    3. 如果是二元/括号表达式，递归遍历 left/right/expression
    4. 否则继续遍历子节点
    
    Args:
        node: pyslang AST 节点
        result: 结果列表，收集到的标识符会追加到此列表
        _visited: 已访问节点集合（防止循环）
    """
    if node is None:
        return
    
    if _visited is None:
        _visited = set()
    
    node_id = id(node)
    if node_id in _visited:
        return
    _visited.add(node_id)
    
    kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
    
    # IdentifierNameSyntax (普通信号引用)
    if kn == 'IdentifierName':
        txt = get_identifier_text(node)
        if txt:
            result.append(txt)
        return  # 不继续遍历子节点
    
    # 整数/向量字面量
    if kn in ('IntegerLiteral', 'IntegerVectorExpression', 'IntegerLiteralExpression',
             'RealLiteral', 'StringLiteral'):
        txt = get_integer_text(node)
        if txt:
            result.append(txt)
        return
    
    # ScopedName (pkg::data) - 遍历子节点提取完整路径
    if kn == 'ScopedName':
        # 收集 ScopedName 下所有 IdentifierName 的文本，拼接成完整路径
        scoped_parts = []
        for child in node:
            ckn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            if ckn == 'IdentifierName':
                txt = get_identifier_text(child)
                if txt:
                    scoped_parts.append(txt)
            elif ckn == 'DoubleColon':
                scoped_parts.append('::')
        if scoped_parts:
            result.append('::'.join(scoped_parts))
            return
        # Fallback: 用 to_json
        import json
        try:
            node_json = json.loads(node.to_json())
            text = node_json.get('text', '')
            if text:
                result.append(text)
        except:
            pass
        return
    
    # 二元表达式: AddExpression, MultiplyExpression, LessThanExpression 等
    # 括号表达式: ParenthesizedExpression
    # 一元表达式: PrefixUnaryExpression, PostfixUnaryExpression
    # 这些都有 left/right/expression/operand 属性之一
    binary_props = ['left', 'right', 'expression', 'operand']
    if any(hasattr(node, p) for p in binary_props):
        for prop in binary_props:
            sub = getattr(node, prop, None)
            if sub is not None:
                collect_expression_identifiers(sub, result, _visited)
        return
    
    # 继续遍历子节点
    try:
        for child in node:
            collect_expression_identifiers(child, result, _visited)
    except:
        pass


def extract_driver_info(assign_node) -> DriverInfo:
    """从赋值表达式节点提取驱动信息
    
    这是 expr_parser 的主要入口函数，用于从
    NonblockingAssignmentExpression 或 AssignmentExpression 提取
    完整的驱动信息。
    
    Args:
        assign_node: AssignmentExpression 或 NonblockingAssignmentExpression 节点
    
    Returns:
        DriverInfo: 包含左值、右值标识符、右值字面量等信息
    """
    kn = assign_node.kind.name if hasattr(assign_node.kind, 'name') else str(assign_node.kind)
    
    info = DriverInfo()
    
    # 提取左值
    left = getattr(assign_node, 'left', None)
    if left:
        info.lhs = get_identifier_text(left)
    
    # 提取右值
    right = getattr(assign_node, 'right', None)
    if right:
        collect_expression_identifiers(right, info.rhs_identifiers)
    
    # 从上下文提取 kind, clock, reset (需要调用者填充)
    info.kind = _get_assign_kind(kn)
    
    # 提取行号
    if hasattr(assign_node, 'sourceRange') and assign_node.sourceRange:
        info.line = assign_node.sourceRange.start.line
    
    return info


def _get_assign_kind(kind_name: str) -> str:
    """根据 SyntaxKind 判断赋值类型"""
    kind_map = {
        'NonblockingAssignmentExpression': 'always_ff',
        'BlockingAssignmentExpression': 'always',
        'AssignmentExpression': 'continuous',
        'ProceduralAssignStatement': 'procedural',
        'ProceduralForceStatement': 'procedural',
    }
    return kind_map.get(kind_name, 'unknown')


def extract_clock_from_always(node) -> List[str]:
    """从 always_ff/always_comb 块提取时钟信号
    
    Args:
        node: AlwaysFFBlock 或 AlwaysCombBlock 节点
    
    Returns:
        时钟信号列表
    """
    clocks = []
    
    # 找到 TimingControlStatement
    timing = getattr(node, 'statement', None)
    if timing and hasattr(timing, 'timing'):
        timing = timing.timing
    
    if not timing:
        return clocks
    
    # 遍历找 SignalEventExpression
    def find_clocks(n):
        kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
        
        if kn == 'SignalEventExpression':
            # 检查 edge
            edge = getattr(n, 'edge', None)
            if edge and hasattr(edge, 'kind'):
                from pyslang import TokenKind
                edge_kind = edge.kind
                if edge_kind == TokenKind.PosEdgeKeyword:
                    pass  # 时钟信号在 expr 中
                elif edge_kind == TokenKind.NegEdgeKeyword:
                    pass
        
        # 检查 expr 属性 (信号)
        expr = getattr(n, 'expr', None)
        if expr:
            ident = get_identifier_text(expr)
            if ident:
                clocks.append(ident)
        
        try:
            for child in n:
                find_clocks(child)
        except:
            pass
    
    find_clocks(timing)
    return list(set(clocks))  # 去重


def get_signal_port_direction(node) -> Optional[str]:
    """从端口节点获取端口方向
    
    Args:
        node: AnsiPortListSyntax 的子节点
    
    Returns:
        'input', 'output', 'inout' 或 None
    """
    # 检查端口方向
    direction = getattr(node, 'direction', None)
    if direction and hasattr(direction, 'name'):
        dir_name = direction.name
        if 'Input' in dir_name:
            return 'input'
        elif 'Output' in dir_name:
            return 'output'
        elif 'InOut' in dir_name or 'Inout' in dir_name:
            return 'inout'
    
    return None


def extract_signal_info_from_declaration(node) -> dict:
    """从信号声明节点提取信号信息
    
    Args:
        node: DataDeclarationSyntax 节点
    
    Returns:
        dict: 包含 name, width, data_type 等信息的字典
    """
    info = {
        'name': '',
        'width': 1,
        'data_type': 'logic',
        'dimensions': [],
        'is_signed': False,
    }
    
    # 获取数据类型
    from pyslang import SyntaxKind
    if node.kind == SyntaxKind.DataDeclaration:
        # 查找 LogicType
        for child in node:
            if hasattr(child, 'kind') and child.kind == SyntaxKind.LogicType:
                info['data_type'] = 'logic'
                # 检查 signed
                if hasattr(child, 'signedness'):
                    info['is_signed'] = True
                # 检查 dimensions
                if hasattr(child, 'dimensions'):
                    for dim in child.dimensions:
                        dim_text = getattr(dim, 'text', '') or ''
                        if dim_text:
                            info['dimensions'].append(dim_text)
    
    # 获取信号名 (Declarator)
    declarators = []
    for child in node:
        if hasattr(child.kind, 'name') and child.kind.name == 'Declarator':
            ident = getattr(child, 'identifier', None)
            if ident:
                info['name'] = getattr(ident, 'valueText', '') or ''
            
            # 检查位宽
            if hasattr(child, 'dimensions'):
                for dim in child.dimensions:
                    dim_text = getattr(dim, 'text', '') or ''
                    if '[' in dim_text:
                        # 解析位宽，如 [7:0] → width = 8
                        import re
                        m = re.search(r'\[(\d+):0\]', dim_text)
                        if m:
                            info['width'] = int(m.group(1)) + 1
    
    return info