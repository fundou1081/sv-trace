"""DriverExtractor - 驱动关系提取器

已添加: 时钟域提取 (CLOCK 边)
"""

import pyslang
from pyslang import SyntaxKind, TokenKind
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
    """驱动提取器 - 时钟域 + 驱动关系"""
    
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
        def visitor(node):
            self._on_node(node)
            return pyslang.VisitAction.Advance
        tree.root.visit(visitor)
    
    def _get_kind(self, node):
        if not hasattr(node, 'kind'):
            return None
        return node.kind
    
    def _on_node(self, node) -> pyslang.VisitAction:
        kind = self._get_kind(node)
        if not kind:
            return None
        
        # always 块
        if kind in (SyntaxKind.AlwaysFFBlock, SyntaxKind.AlwaysBlock, SyntaxKind.AlwaysCombBlock):
            return self._process_always_block(node)
        
        if kind == SyntaxKind.ContinuousAssign:
            return self._process_continuous_assign(node)
        elif kind == SyntaxKind.SequentialBlockStatement:
            return self._process_sequential_block(node)
        elif kind == SyntaxKind.ConditionalStatement:
            return self._process_conditional_statement(node)
        elif kind == SyntaxKind.ExpressionStatement:
            return self._process_expression_statement(node)
        
        return None
    
    def _process_always_block(self, node) -> pyslang.VisitAction:
        # 提取时钟
        clocks = self._extract_clock_from_always(node)
        
        # 处理内部语句
        if hasattr(node, 'statement'):
            timing_stmt = node.statement
            if timing_stmt and hasattr(timing_stmt, 'statement'):
                self._process_stmt(timing_stmt.statement)
        
        return pyslang.VisitAction.Skip
    
    def _extract_clock_from_always(self, node) -> List[Tuple[str, Optional[str]]]:
        """提取时钟信号"""
        if not hasattr(node, 'statement'):
            return []
        
        timing_stmt = node.statement
        if not timing_stmt or not hasattr(timing_stmt, 'timingControl'):
            return []
        
        ctrl = timing_stmt.timingControl
        if not ctrl:
            return []
        
        return self._extract_clocks_from_ctrl(ctrl)
    
    def _extract_clocks_from_ctrl(self, ctrl) -> List[Tuple[str, Optional[str]]]:
        """从 TimingControl 提取"""
        clocks = []
        kind = self._get_kind(ctrl)
        
        if kind != SyntaxKind.EventControlWithExpression:
            return clocks
        
        if hasattr(ctrl, 'expr') and ctrl.expr:
            clocks.extend(self._extract_clocks_from_event_expr(ctrl.expr))
        
        return clocks
    
    def _extract_clocks_from_event_expr(self, expr) -> List[Tuple[str, Optional[str]]]:
        """从事件表达式提取 - 支持嵌套"""
        clocks = []
        kind = self._get_kind(expr)
        
        if kind == SyntaxKind.SignalEventExpression:
            # edge
            edge = None
            if hasattr(expr, 'edge'):
                ek = expr.edge.kind
                edge = 'posedge' if ek == TokenKind.PosEdgeKeyword else 'negedge'
            
            # signal
            signal = None
            if hasattr(expr, 'expr') and expr.expr:
                ie = expr.expr
                signal = getattr(ie, 'value', None) or str(ie)
            
            if signal:
                clocks.append((signal, edge))
        
        elif kind == SyntaxKind.ParenthesizedEventExpression:
            # 嵌套: ParenthesizedEventExpression → SignalEventExpression
            if hasattr(expr, 'expr') and expr.expr:
                clocks.extend(self._extract_clocks_from_event_expr(expr.expr))
        
        elif kind == SyntaxKind.BinaryEventExpression:
            # 多时钟 or
            if hasattr(expr, 'expr') and expr.expr:
                clocks.extend(self._extract_clocks_from_event_expr(expr.expr))
            if hasattr(expr, 'expr2') and expr.expr2:
                clocks.extend(self._extract_clocks_from_event_expr(expr.expr2))
        
        return clocks
    
    def _process_stmt(self, stmt):
        if not hasattr(stmt, 'kind'):
            return
        kind = self._get_kind(stmt)
        
        if kind == SyntaxKind.ExpressionStatement:
            self._process_expression_statement(stmt)
        elif kind == SyntaxKind.SequentialBlockStatement:
            self._process_sequential_block(stmt)
        elif kind == SyntaxKind.ConditionalStatement:
            self._process_conditional_statement(stmt)
    
    def _iter_children(self, node) -> list:
        try:
            return list(node)
        except:
            return []
    
    def _process_continuous_assign(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            if self._get_kind(child) == SyntaxKind.SeparatedList:
                for sub in self._iter_children(child):
                    if self._get_kind(sub) == SyntaxKind.AssignmentExpression:
                        self._process_assign(sub, 'continuous')
        return pyslang.VisitAction.Skip
    
    def _process_sequential_block(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            if self._get_kind(child) == SyntaxKind.SyntaxList:
                for sub in self._iter_children(child):
                    sk = self._get_kind(sub)
                    if sk == SyntaxKind.ExpressionStatement:
                        self._process_expression_statement(sub)
                    elif sk == SyntaxKind.ConditionalStatement:
                        self._process_conditional_statement(sub)
        return pyslang.VisitAction.Skip
    
    def _process_conditional_statement(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            sk = self._get_kind(child)
            if sk == SyntaxKind.ExpressionStatement:
                self._process_expression_statement(child)
            elif sk == SyntaxKind.ConditionalStatement:
                self._process_conditional_statement(child)
            elif sk == SyntaxKind.SequentialBlockStatement:
                self._process_sequential_block(child)
            elif sk == SyntaxKind.ElseClause:
                for sub in self._iter_children(child):
                    ssk = self._get_kind(sub)
                    if ssk == SyntaxKind.ExpressionStatement:
                        self._process_expression_statement(sub)
        return pyslang.VisitAction.Skip
    
    def _process_expression_statement(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            ctx = 'always_ff' if kind == SyntaxKind.NonblockingAssignmentExpression else 'always_comb'
            if kind in (SyntaxKind.NonblockingAssignmentExpression, SyntaxKind.AssignmentExpression):
                self._process_assign(child, ctx)
        return pyslang.VisitAction.Skip
    
    def _process_assign(self, node, kind: str):
        line = getattr(node, 'span', None) and node.span.start_line or 0
        
        lhs_list = []
        children = self._iter_children(node)
        found_eq = False
        
        for child in children:
            ck = self._get_kind(child)
            if not ck:
                continue
            
            if str(ck) in self._SKIP_KINDS:
                continue
            
            if ck in self._ASSIGN_OPS:
                found_eq = True
                continue
            
            if ck in (SyntaxKind.Identifier, SyntaxKind.IdentifierName):
                sig = _extract_identifier(child)
                if sig and not found_eq:
                    lhs_list.append(sig)
                continue
            
            self._scan_lhs(child, lhs_list, found_eq)
        
        for lhs in lhs_list:
            self.graph.add_driver(lhs, lhs, kind, line)
    
    def _scan_lhs(self, node, lhs_list: list, found_eq: bool):
        if not hasattr(node, 'kind'):
            return
        
        kind = self._get_kind(node)
        if not kind:
            return
        
        if str(kind) in self._SKIP_KINDS:
            return
        
        if kind in (SyntaxKind.Identifier, SyntaxKind.IdentifierName):
            sig = _extract_identifier(node)
            if sig and not found_eq:
                lhs_list.append(sig)
            return
        
        for child in self._iter_children(node):
            self._scan_lhs(child, lhs_list, found_eq)
