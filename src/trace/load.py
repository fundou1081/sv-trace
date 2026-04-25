"""
Load Tracer - 追踪信号加载点 (使用 pyslang visit API)
"""
import pyslang
from pyslang import SyntaxKind
from typing import List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Load


class LoadTracer:
    """信号加载点追踪器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.compilation = parser.compilation
        self._loads: List[Load] = []
        self._target_signal = ""
        self._current_module = ""
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号被加载的位置"""
        self._loads = []
        self._target_signal = signal_name
        self._current_module = module_name or ""
        
        for key, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            tree.root.visit(self._visit_callback)
        
        return self._loads
    
    def _visit_callback(self, node):
        """Visit callback for finding loads"""
        kind = node.kind
        
        # Track module name
        if kind == SyntaxKind.ModuleDeclaration:
            if hasattr(node, 'header') and hasattr(node.header, 'name'):
                self._current_module = str(node.header.name)
            return pyslang.VisitAction.Advance
        
        # Process always blocks
        if kind == SyntaxKind.AlwaysBlock:
            self._process_always_load(node)
            return pyslang.VisitAction.Skip  # Handle manually
        
        # Process always_ff/comb/latch blocks
        if kind in [SyntaxKind.AlwaysFFBlock, SyntaxKind.AlwaysCombBlock, SyntaxKind.AlwaysLatchBlock]:
            self._process_always_load(node)
            return pyslang.VisitAction.Skip
        
        # Process continuous assignments
        if kind == SyntaxKind.ContinuousAssign:
            self._process_continuous_assign_load(node)
            return pyslang.VisitAction.Advance
        
        return pyslang.VisitAction.Advance
    
    def _process_always_load(self, node):
        """Process always/always_ff/always_comb/always_latch block for loads"""
        try:
            if not hasattr(node, 'statement') or not node.statement:
                return
            
            stmt = node.statement
            stmt_kind = str(stmt.kind) if hasattr(stmt, 'kind') else ''
            
            # always_comb: statement 是 SequentialBlockStatement
            if 'SequentialBlockStatement' in stmt_kind or 'BlockStatement' in stmt_kind:
                self._walk_for_load(stmt)
            
            # always_ff/always_latch: statement 是 TimingControlStatement
            elif 'TimingControl' in stmt_kind:
                if hasattr(stmt, 'statement') and stmt.statement:
                    self._walk_for_load(stmt.statement)
                    
        except Exception as e:
            pass
    
    def _process_continuous_assign_load(self, node):
        """Process continuous assignment for loads"""
        try:
            if hasattr(node, 'assignments') and node.assignments:
                for i in range(len(node.assignments)):
                    assign = node.assignments[i]
                    self._check_rhs_for_load(assign)
        except Exception as e:
            pass
    
    def _walk_for_load(self, stmt):
        """Walk statement tree to find loads"""
        if stmt is None:
            return
        
        if not hasattr(stmt, 'kind'):
            return
        
        stmt_kind = str(stmt.kind)
        
        # Sequential block - iterate items
        if stmt_kind == 'SyntaxKind.SequentialBlockStatement':
            if hasattr(stmt, 'items'):
                for i in range(len(stmt.items)):
                    self._walk_for_load(stmt.items[i])
            return
        
        # Expression statement - check expr (not expression!)
        if stmt_kind == 'SyntaxKind.ExpressionStatement':
            if hasattr(stmt, 'expr') and stmt.expr:
                self._check_assignment_for_load(stmt.expr)
            return
        
        # If statement
        if 'If' in stmt_kind:
            # Check condition
            if hasattr(stmt, 'expr') and stmt.expr:
                self._check_expr_for_load(stmt.expr)
            # Recurse into branches
            if hasattr(stmt, 'statement') and stmt.statement:
                self._walk_for_load(stmt.statement)
            if hasattr(stmt, 'elseClause') and stmt.elseClause:
                self._walk_for_load(stmt.elseClause.clause)
            return
        
        # Case statement
        if 'Case' in stmt_kind:
            if hasattr(stmt, 'expr') and stmt.expr:
                self._check_expr_for_load(stmt.expr)
            if hasattr(stmt, 'items'):
                for i in range(len(stmt.items)):
                    case = stmt.items[i]
                    if hasattr(case, 'clause') and case.clause:
                        self._walk_for_load(case.clause)
            return
        
        # For loop
        if 'ForLoop' in stmt_kind:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._walk_for_load(stmt.statement)
            return
        
        # While loop
        if 'WhileLoop' in stmt_kind:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._walk_for_load(stmt.statement)
            return
    
    def _check_assignment_for_load(self, expr):
        """Check if assignment expression uses target signal"""
        if expr is None:
            return
        
        if not hasattr(expr, 'kind'):
            return
        
        kind_str = str(expr.kind)
        
        # Assignment expression - check RHS
        if 'Assignment' in kind_str or 'Nonblocking' in kind_str:
            if hasattr(expr, 'right') and expr.right:
                self._check_expr_for_load(expr.right)
            return
        
        # Other expressions - recurse
        self._check_expr_for_load(expr)
    
    def _check_expr_for_load(self, expr):
        """Check if expression contains target signal"""
        if expr is None:
            return
        
        if not hasattr(expr, 'kind'):
            return
        
        kind_str = str(expr.kind)
        
        # Identifier - check if it matches target signal
        if 'Identifier' in kind_str:
            name = str(expr).strip()
            if name == self._target_signal:
                self._add_load(str(expr), expr)
            return
        
        # Binary/Arithmetic/Logic expression - check both sides
        if kind_str.endswith('Expression') or 'Binary' in kind_str:
            if hasattr(expr, 'left') and expr.left:
                self._check_expr_for_load(expr.left)
            if hasattr(expr, 'right') and expr.right:
                self._check_expr_for_load(expr.right)
            return
        
        # Conditional expression (?:)
        if 'Conditional' in kind_str:
            if hasattr(expr, 'predicate') and expr.predicate:
                self._check_expr_for_load(expr.predicate)
            if hasattr(expr, 'left') and expr.left:
                self._check_expr_for_load(expr.left)
            if hasattr(expr, 'right') and expr.right:
                self._check_expr_for_load(expr.right)
            return
        
        # Function call - check arguments
        if 'Call' in kind_str:
            if hasattr(expr, 'arguments') and expr.arguments:
                for i in range(len(expr.arguments)):
                    arg = expr.arguments[i]
                    if hasattr(arg, 'expr'):
                        self._check_expr_for_load(arg.expr)
            return
    
    def _check_rhs_for_load(self, assign):
        """Check if assignment RHS contains target signal"""
        if not hasattr(assign, 'right') or not assign.right:
            return
        
        rhs = assign.right
        self._check_expr_for_load(rhs)
    
    def _add_load(self, context: str, node):
        """Add a load record"""
        line = 0
        if hasattr(node, 'sourceRange') and node.sourceRange:
            try:
                line = node.sourceRange.start.offset if hasattr(node.sourceRange.start, 'offset') else 0
            except:
                line = 0
        
        load = Load(
            signal_name=self._target_signal,
            context=context,
            line=line,
            module=self._current_module.strip(),
            statement_type="",
            condition=""
        )
        
        self._loads.append(load)
