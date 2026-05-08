"""DriverExtractor - 驱动关系提取器

符合铁律 18-20
已添加: 时钟域提取 (CLOCK 边)
"""

import pyslang
from typing import Set, List, Tuple, Optional

from extractors.base import Extractor, SemanticGraph, DriverPoint
from scope.models import ScopeTree
from scope.symbol_table import SymbolTable

try:
    from scope.utils import extract_identifier as _extract_identifier
except ImportError:
    def _extract_identifier(node):
        if hasattr(node, 'text') and node.text:
            return node.text
        return ""


class DriverExtractor(Extractor):
    """驱动提取器
    
    符合铁律 18: 使用 pyslang.visit() 遍历
    符合铁律 19: 通过 ScopeTree 解析引用
    
    功能:
    - 时钟域提取 (CLOCK 边)
    - 复位提取
    - 多驱动检测
    """
    
    _ASSIGN_OPS: Set[str] = {
        'Equals', 'LessThanEquals',
        'PlusEquals', 'MinusEquals', 'MultiplyEquals',
    }
    
    _SKIP_KINDS: Set[str] = {
        'TokenList', 'SyntaxList', 'SeparatedList',
        'Plus', 'Minus', 'Multiply', 'Divide', 'Modulo',
        'OpenParenthesis', 'CloseParenthesis',
        'IntegerLiteral', 'IntegerBase',
        'AssignKeyword', 'Question', 'Colon', 'At',
        'And', 'Or', 'Xor', 'Not', 'Tilde',
        'Ampersand', 'Bar', 'Caret',
    }
    
    def extract(self, tree: pyslang.SyntaxTree) -> None:
        """从 AST 提取驱动关系"""
        def visitor(node):
            self._on_node(node)
            return pyslang.VisitAction.Advance
        
        tree.root.visit(visitor)
    
    def _on_node(self, node) -> pyslang.VisitAction:
        kind = self._get_kind(node)
        if not kind:
            return None
        
        # always 块处理 - 添加 CLOCK 边
        if kind in ('AlwaysFFBlock', 'AlwaysBlock', 'AlwaysCombBlock'):
            return self._process_always_block(node)
        
        if kind == 'ContinuousAssign':
            return self._process_continuous_assign(node)
        elif kind == 'SequentialBlockStatement':
            return self._process_sequential_block(node)
        elif kind == 'ConditionalStatement':
            return self._process_conditional_statement(node)
        elif kind == 'ExpressionStatement':
            return self._process_expression_statement(node)
        
        return None
    
    def _process_always_block(self, node) -> pyslang.VisitAction:
        """处理 always 块并提取时钟"""
        # 提取时钟信号
        clocks = self._extract_clock_from_always(node)
        
        # 处理内部的语句
        if hasattr(node, 'statement'):
            timing_stmt = node.statement
            
            # TimingControlStatement 的 statement 属性是内部的语句
            if timing_stmt and hasattr(timing_stmt, 'statement'):
                stmt = timing_stmt.statement
                self._process_stmt(stmt)
        
        return pyslang.VisitAction.Skip
    
    def _extract_clock_from_always(self, node) -> List[Tuple[str, Optional[str]]]:
        """从 always 块提取时钟信号
        
        返回: [(signal_name, edge), ...]
        edge: 'PosEdge' 或 'NegEdge'
        """
        if not hasattr(node, 'statement'):
            return []
        
        timing_stmt = node.statement
        if not hasattr(timing_stmt, 'timingControl'):
            return []
        
        timing_ctrl = timing_stmt.timingControl
        if not timing_ctrl:
            return []
        
        return self._extract_clocks_from_ctrl(timing_ctrl)
    
    def _extract_clocks_from_ctrl(self, ctrl) -> List[Tuple[str, Optional[str]]]:
        """从 TimingControl 提取时钟"""
        clocks = []
        
        # 处理 EventControlWithExpression
        if not hasattr(ctrl, 'kind') or str(ctrl.kind) != 'EventControlWithExpression':
            return clocks
        
        # 获取 expr
        if hasattr(ctrl, 'expr') and ctrl.expr:
            clocks.extend(self._extract_clocks_from_event_expr(ctrl.expr))
        
        # 处理多个时钟 (or)
        if hasattr(ctrl, 'expressions'):
            for item in ctrl.expressions:
                if hasattr(item, 'kind'):
                    clocks.extend(self._extract_clocks_from_event_expr(item))
        
        return clocks
    
    def _extract_clocks_from_event_expr(self, expr) -> List[Tuple[str, Optional[str]]]:
        """从事件表达式提取时钟"""
        clocks = []
        
        if not hasattr(expr, 'kind'):
            return clocks
        
        kind_str = str(expr.kind)
        
        if kind_str == 'SignalEventExpression':
            # 获取边沿
            edge = None
            if hasattr(expr, 'edge'):
                edge_token = expr.edge
                edge = str(edge_token.value) if hasattr(edge_token, 'value') else str(edge_token)
            
            # 获取信号名
            signal = None
            if hasattr(expr, 'expr'):
                ident_expr = expr.expr
                if ident_expr:
                    if hasattr(ident_expr, 'identifier'):
                        ident = ident_expr.identifier
                        signal = ident.value if hasattr(ident, 'value') else str(ident)
                    elif hasattr(ident_expr, 'name'):
                        signal = ident_expr.name
            
            if signal:
                clocks.append((signal, edge))
        
        elif kind_str == 'ParenthesizedEventExpression':
            if hasattr(expr, 'expr') and expr.expr:
                clocks.extend(self._extract_clocks_from_event_expr(expr.expr))
        
        elif kind_str == 'BinaryEventExpression':
            # 多个时钟用 or 连接
            if hasattr(expr, 'expr') and expr.expr:
                clocks.extend(self._extract_clocks_from_event_expr(expr.expr))
            if hasattr(expr, 'expr2') and expr.expr2:
                clocks.extend(self._extract_clocks_from_event_expr(expr.expr2))
        
        return clocks
    
    def _process_stmt(self, stmt):
        """处理语句"""
        if not hasattr(stmt, 'kind'):
            return
        
        kind = self._get_kind(stmt)
        
        if kind == 'ExpressionStatement':
            self._process_expression_statement(stmt)
        elif kind == 'SequentialBlockStatement':
            self._process_sequential_block(stmt)
        elif kind == 'ConditionalStatement':
            self._process_conditional_statement(stmt)
    
    def _process_continuous_assign(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            if self._get_kind(child) == 'SeparatedList':
                for sub in self._iter_children(child):
                    if self._get_kind(sub) == 'AssignmentExpression':
                        self._process_assign(sub, 'continuous')
        return pyslang.VisitAction.Skip
    
    def _process_sequential_block(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            if self._get_kind(child) == 'SyntaxList':
                for sub in self._iter_children(child):
                    sk = self._get_kind(sub)
                    if sk == 'ExpressionStatement':
                        self._process_expression_statement(sub)
                    elif sk == 'ConditionalStatement':
                        self._process_conditional_statement(sub)
        return pyslang.VisitAction.Skip
    
    def _process_conditional_statement(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            sk = self._get_kind(child)
            if sk == 'ExpressionStatement':
                self._process_expression_statement(child)
            elif sk == 'ConditionalStatement':
                self._process_conditional_statement(child)
            elif sk == 'SequentialBlockStatement':
                self._process_sequential_block(child)
            elif sk == 'ElseClause':
                for sub in self._iter_children(child):
                    ssk = self._get_kind(sub)
                    if ssk == 'ExpressionStatement':
                        self._process_expression_statement(sub)
        return pyslang.VisitAction.Skip
    
    def _process_expression_statement(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind in ('NonblockingAssignmentExpression', 'AssignmentExpression'):
                ctx = 'always_ff' if kind == 'NonblockingAssignmentExpression' else 'always_comb'
                self._process_assign(child, ctx)
        return pyslang.VisitAction.Skip
    
    def _process_assign(self, node, kind: str):
        """处理赋值语句"""
        line = getattr(node, 'span', None) and node.span.start_line or 0
        
        lhs_list = []
        children = self._iter_children(node)
        found_eq = False
        
        for child in children:
            ck = self._get_kind(child)
            
            if ck in self._SKIP_KINDS:
                continue
            
            if ck in self._ASSIGN_OPS:
                found_eq = True
                continue
            
            if ck in ('Identifier', 'IdentifierName'):
                sig = _extract_identifier(child)
                if sig and not found_eq:
                    lhs_list.append(sig)
                continue
            
            self._scan_lhs(child, lhs_list, found_eq)
        
        for lhs in lhs_list:
            self.graph.add_driver(lhs, lhs, kind, line)
    
    def _scan_lhs(self, node, lhs_list: list, found_eq: bool):
        """扫描左值"""
        if not hasattr(node, 'kind'):
            return
        
        kind = self._get_kind(node)
        if not kind or kind in self._SKIP_KINDS:
            return
        
        if kind in ('Identifier', 'IdentifierName'):
            sig = _extract_identifier(node)
            if sig and not found_eq:
                lhs_list.append(sig)
            return
        
        for child in self._iter_children(node):
            self._scan_lhs(child, lhs_list, found_eq)
