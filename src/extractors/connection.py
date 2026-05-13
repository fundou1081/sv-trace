"""ConnectionExtractor - 端口连接关系提取器

从 AST 提取模块实例化和端口连接关系。
融合 MIG 支持 generate block 层级。

符合铁律:
- 铁律1: AST 唯一数据源
- 铁律2: 位精确性
- 铁律3: 不可信则不输出
- 铁律18: 继承 Extractor 基类，接收 ScopeTree
- 铁律19: 通过 ScopeTree 解析引用
"""

import pyslang
from pyslang import SyntaxKind
from typing import List, Dict, Set, Tuple, Optional

from extractors.base import Extractor, SemanticGraph, Connection
from scope.models import ScopeTree
from scope.symbol_table import SymbolTable


try:
    from scope.utils import extract_identifier as _extract_identifier
except ImportError:
    def _extract_identifier(node):
        if hasattr(node, 'text') and node.text:
            return node.text
        return ""


# 跳过的节点类型
_SKIP_KINDS: Set[str] = {
    'TokenList',
    'IntegerLiteral',
    'IntegerBase',
    'VariableDimension',
    'RangeDimensionSpecifier',
    'SimpleRangeSelect',
    'TimeUnit',
    'DoublePeriod',
    'AssignKeyword',
    'Question',
    'Colon',
    'OpenParenthesis',
    'CloseParenthesis',
    'OpenBracket',
    'CloseBracket',
    'Plus',
    'Minus',
    'Multiply',
    'Divide',
    'Modulo',
    'And',
    'Or',
    'Xor',
    'Not',
    'Tilde',
    'Ampersand',
    'Bar',
    'Caret',
    'At',
    'Separator',
    'Comma',
    'Semicolon',
}


class ConnectionExtractor(Extractor):
    """端口连接关系提取器
    
    提取模块实例化和端口连接关系。
    支持:
    - 模块实例化 (HierarchyInstantiation → HierarchicalInstance)
    - generate 块内实例化
    - 命名端口连接 (NamedPortConnection)
    
    AST 结构:
    - HierarchyInstantiation → [Identifier(module_type), SeparatedList<HierarchicalInstance>]
    - HierarchicalInstance → [InstanceName, OpenParenthesis, SeparatedList<NamedPortConnection>]
    - NamedPortConnection → [SyntaxList(Dot, Identifier(port)), OpenParenthesis, SimplePropertyExpr, CloseParenthesis]
    
    输出:
    - graph.connections: List[Connection]
    """
    
    # 追踪当前实例层级
    _instance_stack: List[Tuple[str, str]] = []  # [(instance_name, module_type), ...]
    
    def extract(self, tree: pyslang.SyntaxTree) -> None:
        """从 AST 提取连接关系"""
        self._instance_stack = []
        
        def visitor(node):
            self._on_node(node)
            return pyslang.VisitAction.Advance
        
        tree.root.visit(visitor)
    
    def _get_kind(self, node):
        if not hasattr(node, 'kind'):
            return None
        kind = node.kind
        if hasattr(kind, 'name'):
            return kind.name
        return str(kind)
    
    def _get_syntax_kind(self, node):
        if not hasattr(node, 'kind'):
            return None
        return node.kind
    
    def _iter_children(self, node) -> list:
        try:
            return list(node)
        except:
            return []
    
    def _on_node(self, node) -> pyslang.VisitAction:
        """处理每个节点"""
        kind = self._get_syntax_kind(node)
        if not kind:
            return None
        
        # 模块实例化 - HierarchyInstantiation 是顶层
        if kind == SyntaxKind.HierarchyInstantiation:
            return self._process_hierarchy_instantiation(node)
        
        # 跳过 generate 块自身，它们的实例化由内部处理
        if kind in (
            SyntaxKind.LoopGenerate,
            SyntaxKind.IfGenerate,
            SyntaxKind.CaseGenerate,
        ):
            return pyslang.VisitAction.Advance
        
        return None
    
    def _process_hierarchy_instantiation(self, node) -> pyslang.VisitAction:
        """处理 HierarchyInstantiation (模块实例化语句)
        
        结构: HierarchyInstantiation → [SyntaxList, Identifier(module_type), SeparatedList(HierarchicalInstance), Semicolon]
        """
        module_type = ""
        line = 0
        
        if hasattr(node, 'span') and node.span:
            line = node.span.start_line
        
        children = self._iter_children(node)
        
        # 找 Identifier (模块类型) - 通常是第二个子节点
        for child in children:
            ck = self._get_kind(child)
            if not ck:
                continue
            
            if ck == 'Identifier':
                ident = _extract_identifier(child)
                if ident and not module_type:
                    module_type = ident
                    break
        
        # 找 SeparatedList，里面有 HierarchicalInstance
        for child in children:
            ck = self._get_kind(child)
            if not ck:
                continue
            
            if ck == 'SeparatedList':
                # 处理 HierarchicalInstance 列表
                for sub in self._iter_children(child):
                    subk = self._get_kind(sub)
                    if subk == 'HierarchicalInstance':
                        self._process_hierarchical_instance(sub, module_type, line)
        
        return pyslang.VisitAction.Skip
    
    def _process_hierarchical_instance(self, node, module_type: str, line: int):
        """处理单个 HierarchicalInstance
        
        结构: HierarchicalInstance → [InstanceName, OpenParenthesis, SeparatedList<NamedPortConnection>, ...]
        """
        instance_name = ""
        
        # 获取实例名
        if hasattr(node, 'instanceName'):
            inst = node.instanceName
            instance_name = _extract_identifier(inst) or ""
        elif hasattr(node, 'name'):
            instance_name = _extract_identifier(node.name) or ""
        
        # 从子节点获取实例名
        if not instance_name:
            for child in self._iter_children(node):
                ck = self._get_kind(child)
                if not ck:
                    continue
                if ck in ('Identifier', 'IdentifierName', 'InstanceName'):
                    ident = _extract_identifier(child)
                    if ident:
                        instance_name = ident
                        break
        
        if not instance_name:
            return
        
        # 构建层级路径
        parent_path = self._get_current_hierarchy()
        hierarchy = f"{parent_path}.{instance_name}" if parent_path else instance_name
        
        # 入栈
        self._instance_stack.append((instance_name, module_type))
        
        # 处理端口连接 - 从子节点中找 NamedPortConnection
        self._process_port_connections(node, hierarchy, line)
        
        # 出栈
        if self._instance_stack:
            self._instance_stack.pop()
    
    def _get_current_hierarchy(self) -> str:
        """获取当前实例层级路径"""
        if not self._instance_stack:
            return ""
        
        parts = []
        for inst_name, _ in self._instance_stack:
            parts.append(inst_name)
        
        return ".".join(parts)
    
    def _process_port_connections(self, node, instance_hierarchy: str, line: int):
        """处理端口连接
        
        AST 结构:
        - NamedPortConnection 直接在 SeparatedList 中 (HierarchicalInstance → SeparatedList → NamedPortConnection)
        - 结构: NamedPortConnection → [SyntaxList(empty), Dot, Identifier(port), OpenParenthesis, SimplePropertyExpr, CloseParenthesis]
        """
        for child in self._iter_children(node):
            ck = self._get_kind(child)
            if not ck:
                continue
            
            # NamedPortConnection 直接在 SeparatedList 中
            if ck == 'NamedPortConnection':
                self._process_named_connection(child, instance_hierarchy, line)
            elif ck == 'OrderedPortConnection':
                self._process_ordered_connection(child, instance_hierarchy, line)
            elif ck == 'SeparatedList':
                # SeparatedList 容器 (可能包含 NamedPortConnection 或 OrderedPortConnection)
                for sub in self._iter_children(child):
                    subk = self._get_kind(sub)
                    if subk == 'NamedPortConnection':
                        self._process_named_connection(sub, instance_hierarchy, line)
                    elif subk == 'OrderedPortConnection':
                        self._process_ordered_connection(sub, instance_hierarchy, line)
    
    def _process_named_connection(self, node, to_instance: str, line: int):
        """处理单个命名端口连接: .port(signal)
        
        AST 结构:
        NamedPortConnection → [SyntaxList(empty), Dot, Identifier(port), OpenParenthesis, SimplePropertyExpr, CloseParenthesis]
        
        注意: SyntaxList 是空的，真实数据在直接子节点中:
        - Identifier (index 2) 是端口名
        - SimplePropertyExpr (index 4) 包含信号名
        """
        port_name = ""
        connected_signal = ""
        
        # 直接遍历所有直接子节点 (不迭代 SyntaxList，因为它是空的)
        children = self._iter_children(node)
        
        # 找 Identifier (端口名) 和 SimplePropertyExpr (信号)
        for child in children:
            ck = self._get_kind(child)
            if not ck:
                continue
            
            if ck == 'Identifier':
                # 这是端口名 (在 Dot 之后)
                ident = _extract_identifier(child)
                val = getattr(child, 'value', None)
                if val and not port_name:
                    port_name = val
            
            elif ck == 'SimplePropertyExpr':
                # 从表达式提取信号名
                signal = self._extract_signal_from_expr(child)
                if signal and not connected_signal:
                    connected_signal = signal
        
        # 过滤 literal-value nodes (如 32'hA5A5A5A5)
        if connected_signal and self._is_literal_value(connected_signal):
            return
        
        if port_name and connected_signal:
            from_instance = self._get_parent_instance()
            
            conn = Connection(
                from_instance=from_instance or "",
                from_port=connected_signal or "",
                to_instance=to_instance,
                to_port=port_name,
                signal=connected_signal or "",
                line=line,
            )
            self.graph.connections.append(conn)
    
    def _extract_signal_from_expr(self, node) -> str:
        """从表达式中提取信号名
        
        结构: SimplePropertyExpr > SimpleSequenceExpr > IdentifierName > Identifier
        
        注意: IdentifierName 节点本身的 value 通常为 None，
              信号名在 Identifier 子节点中 (value=clk)
        """
        if not hasattr(node, 'kind'):
            return ""
        
        kind = self._get_kind(node)
        if kind in ('IdentifierName', 'Identifier'):
            # 先检查当前节点的值
            val = getattr(node, 'value', None)
            if val:
                return val
            text = getattr(node, 'text', None)
            if text:
                return text
            # IdentifierName 的值在子节点 Identifier 中
            # 递归到子节点
            for child in self._iter_children(node):
                result = self._extract_signal_from_expr(child)
                if result:
                    return result
            return ""
        
        # 递归遍历
        for child in self._iter_children(node):
            result = self._extract_signal_from_expr(child)
            if result:
                return result
        return ""
    
    def _process_ordered_port_connections(self, node, to_instance: str, line: int):
        """处理有序端口连接 (不常用)"""
        for child in self._iter_children(node):
            ck = self._get_kind(child)
            if not ck:
                continue
            
            if ck == 'OrderedPortConnection':
                self._process_ordered_connection(child, to_instance, line)
    
    def _process_ordered_connection(self, node, to_instance: str, line: int):
        """处理单个有序端口连接"""
        connected_signal = ""
        
        if hasattr(node, 'connection') and node.connection:
            conn = node.connection
            if hasattr(conn, 'value'):
                connected_signal = str(conn.value)
            elif hasattr(conn, 'text'):
                connected_signal = conn.text
            else:
                connected_signal = _extract_identifier(conn) or ""
        
        # 过滤 literal-value
        if connected_signal and self._is_literal_value(connected_signal):
            return
        
        # 有序连接无法确定端口名
        from_instance = self._get_parent_instance()
        
        conn = Connection(
            from_instance=from_instance or "",
            from_port=connected_signal or "",
            to_instance=to_instance,
            to_port="",  # 未知端口名
            signal=connected_signal or "",
            line=line,
        )
        self.graph.connections.append(conn)
    
    def _get_parent_instance(self) -> str:
        """获取父实例名称"""
        if len(self._instance_stack) >= 2:
            return self._instance_stack[-2][0]
        return ""
    
    def _is_literal_value(self, sig: str) -> bool:
        """检查是否是字面量值 (spurious nodes)"""
        if not sig:
            return False
        
        # 32'hA5A5A5A5, 'hA5A5, 8'b1010 等
        if "'" in sig:
            return True
        
        # 数字开头的
        if sig[0].isdigit():
            return True
        
        # 只包含数字和 'hx 的 (如 0x123)
        stripped = sig.replace("'", "").replace("x", "")
        if stripped and stripped.lstrip('0123456789') == '':
            return True
        
        return False
