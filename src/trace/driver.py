"""Driver collector using pyslang visit API"""
import sys
import os
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field

import pyslang
from pyslang import SyntaxKind

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.models import Driver, DriverKind, AssignKind


@dataclass
class DriverInfo:
    """Driver information"""
    signal: str
    kind: DriverKind
    sources: List[str] = field(default_factory=list)
    clock: str = ""
    line: int = 0
    module: str = ""


class DriverCollector:
    """Collects drivers for all signals in the design"""
    
    def __init__(self, parser):
        self.parser = parser
        self.drivers: Dict[str, List[Driver]] = {}
        self._collect()
    
    def _collect(self):
        """Collect drivers from all parsed files"""
        for fname, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            self._visit_tree(tree.root)
    
    def _visit_tree(self, root):
        """Visit the entire tree to find assignments"""
        module_name = ""
        
        def callback(node):
            nonlocal module_name
            
            kind = node.kind
            
            # Track module name
            if kind == SyntaxKind.ModuleDeclaration:
                if hasattr(node, 'header') and hasattr(node.header, 'name'):
                    module_name = str(node.header.name)
                return pyslang.VisitAction.Advance
            
            # Find always/always_ff/always_comb/always_latch blocks
            if kind == SyntaxKind.AlwaysBlock:
                self._process_always_block(node, module_name, DriverKind.AlwaysFF)
                return pyslang.VisitAction.Skip
            
            if kind == SyntaxKind.AlwaysCombBlock:
                self._process_always_block(node, module_name, DriverKind.AlwaysComb)
                return pyslang.VisitAction.Skip
            
            if kind == SyntaxKind.AlwaysLatchBlock:
                self._process_always_block(node, module_name, DriverKind.AlwaysLatch)
                return pyslang.VisitAction.Skip
            
            if kind == SyntaxKind.AlwaysFFBlock:
                self._process_always_block(node, module_name, DriverKind.AlwaysFF)
                return pyslang.VisitAction.Skip
            
            # Find assignment expressions (in continuous assignments, etc.)
            if kind == SyntaxKind.AssignmentExpression:
                self._process_assignment(node, module_name, DriverKind.Continuous, "")
                return pyslang.VisitAction.Advance
            
            # Find nonblocking assignment expressions (procedural)
            if kind == SyntaxKind.NonblockingAssignmentExpression:
                self._process_assignment(node, module_name, DriverKind.AlwaysFF, "")
                return pyslang.VisitAction.Advance
            
            # Find continuous assignments
            if kind == SyntaxKind.ContinuousAssign:
                self._process_continuous_assign(node, module_name)
                return pyslang.VisitAction.Advance
            
            return pyslang.VisitAction.Advance
        
        root.visit(callback)
    
    def _process_assignment(self, node, module_name: str, kind: DriverKind, clock: str):
        """Process an assignment expression"""
        try:
            if not hasattr(node, 'left') or not node.left:
                return
            left = node.left
            
            target = self._get_signal_name(left)
            if not target:
                return
            
            sources = []
            if hasattr(node, 'right') and node.right:
                sources = self._extract_sources(node.right)
            
            line = 0
            if hasattr(node, 'sourceRange') and node.sourceRange:
                try:
                    line = node.sourceRange.start.offset if hasattr(node.sourceRange.start, 'offset') else 0
                except:
                    line = 0
            
            driver = Driver(
                signal=target,
                kind=kind,
                module=module_name,
                sources=sources,
                clock=clock,
                lines=[line] if line else [],
                condition=""
            )
            
            if target not in self.drivers:
                self.drivers[target] = []
            self.drivers[target].append(driver)
            
        except Exception as e:
            pass
    
    def _process_always_block(self, node, module_name: str, kind: DriverKind):
        """Process always/always_ff/always_comb/always_latch block"""
        try:
            if not hasattr(node, 'statement') or not node.statement:
                return
            
            stmt = node.statement
            stmt_kind = str(stmt.kind) if hasattr(stmt, 'kind') else ''
            
            # always_comb: statement 是 SequentialBlockStatement
            if 'SequentialBlockStatement' in stmt_kind or 'BlockStatement' in stmt_kind:
                self._walk_statement(stmt, kind, module_name, "")
            
            # always_ff/always_latch: statement 是 TimingControlStatement
            # 需要再取一层 .statement
            elif 'TimingControl' in stmt_kind:
                if hasattr(stmt, 'statement') and stmt.statement:
                    self._walk_statement(stmt.statement, kind, module_name, "")
                    
        except Exception as e:
            pass
    
    def _process_continuous_assign(self, node, module_name: str):
        """Process continuous assignment"""
        try:
            if hasattr(node, 'assignments') and node.assignments:
                for assign in node.assignments:
                    self._process_assignment(assign, module_name, DriverKind.Continuous, "")
        except Exception as e:
            pass
    
    def _walk_statement(self, stmt, kind: DriverKind, module_name: str, clock: str):
        """Walk a statement to find assignments"""
        try:
            if stmt is None:
                return
            
            if not hasattr(stmt, 'kind'):
                return
            
            stmt_kind = str(stmt.kind)
            
            if stmt_kind == 'SyntaxKind.SequentialBlockStatement':
                if hasattr(stmt, 'items'):
                    for i in range(len(stmt.items)):
                        child = stmt.items[i]
                        self._walk_statement(child, kind, module_name, clock)
                return
            
            if 'ExpressionStatement' in stmt_kind:
                if hasattr(stmt, 'expr') and stmt.expr:
                    expr = stmt.expr
                    if hasattr(expr, 'kind'):
                        expr_kind = str(expr.kind)
                        if 'Assignment' in expr_kind or 'Nonblocking' in expr_kind:
                            self._process_assignment(expr, module_name, kind, clock)
                return
            
            if 'If' in stmt_kind or 'Conditional' in stmt_kind:
                if hasattr(stmt, 'statement') and stmt.statement:
                    self._walk_statement(stmt.statement, kind, module_name, clock)
                if hasattr(stmt, 'elseClause') and stmt.elseClause.clause:
                    self._walk_statement(stmt.elseClause.clause, kind, module_name, clock)
                return
            
            if 'Case' in stmt_kind:
                if hasattr(stmt, 'items'):
                    for i in range(len(stmt.items)):
                        case = stmt.items[i]
                        if hasattr(case, 'clause') and case.clause:
                            self._walk_statement(case.clause, kind, module_name, clock)
                return
            
            if 'ForLoop' in stmt_kind:
                if hasattr(stmt, 'statement') and stmt.statement:
                    self._walk_statement(stmt.statement, kind, module_name, clock)
                return
            
            if 'WhileLoop' in stmt_kind:
                if hasattr(stmt, 'statement') and stmt.statement:
                    self._walk_statement(stmt.statement, kind, module_name, clock)
                return
            
        except Exception as e:
            pass
    
    def _get_signal_name(self, node) -> str:
        """Get the signal name from a node"""
        if node is None:
            return ""
        
        kind_str = str(node.kind)
        
        if 'Identifier' in kind_str:
            return str(node).strip()
        
        if 'ElementSelect' in kind_str:
            return str(node).strip()
        
        if 'RangeSelect' in kind_str:
            return str(node).strip()
        
        return ""
    
    def _extract_sources(self, node) -> List[str]:
        """Extract source signals from an expression"""
        sources = []
        
        if node is None:
            return sources
        
        if not hasattr(node, 'kind'):
            return sources
        
        kind_str = str(node.kind)
        
        if 'Identifier' in kind_str and 'Pattern' not in kind_str:
            name = str(node).strip()
            if name and not self._is_literal(name):
                sources.append(name)
            return sources
        
        if 'Binary' in kind_str:
            if hasattr(node, 'left') and node.left:
                sources.extend(self._extract_sources(node.left))
            if hasattr(node, 'right') and node.right:
                sources.extend(self._extract_sources(node.right))
            return sources
        
        if 'Conditional' in kind_str or 'Ternary' in kind_str:
            if hasattr(node, 'whenTrue') and node.whenTrue:
                sources.extend(self._extract_sources(node.whenTrue))
            if hasattr(node, 'whenFalse') and node.whenFalse:
                sources.extend(self._extract_sources(node.whenFalse))
            return sources
        
        if 'Call' in kind_str:
            return sources
        
        return sources
    
    def _is_literal(self, name: str) -> bool:
        """Check if a name is a literal value"""
        name = name.strip()
        if not name:
            return True
        name_lower = name.lower()
        if name_lower.isdigit():
            return True
        if name_lower.startswith("'h") or name_lower.startswith("'b") or name_lower.startswith("'d"):
            return True
        if name_lower.startswith("'"):
            return True
        if name_lower in ['x', 'z', '?']:
            return True
        return False
    
    def get_drivers(self, signal: str = '*') -> List[Driver]:
        """Get drivers for a signal. Use '*' for all."""
        if signal == '*':
            all_drivers = []
            for sig, drvs in self.drivers.items():
                all_drivers.extend(drvs)
            return all_drivers
        return self.drivers.get(signal, [])
    
    def find_driver(self, signal_name: str, include_bit_select: bool = False) -> List[Driver]:
        """Find drivers for a signal.
        
        Args:
            signal_name: Name of the signal to find drivers for
            include_bit_select: If True, also match signals with bit selects (e.g., sig[0])
        
        Returns:
            List of Driver objects
        """
        drivers = self.drivers.get(signal_name, [])
        
        if include_bit_select:
            # Also find drivers for signals that match the base name
            for sig, drvs in self.drivers.items():
                if sig.startswith(signal_name + '['):
                    drivers.extend(drvs)
        
        return drivers
    
    def get_all_signals(self) -> List[str]:
        """Get list of all signals with drivers"""
        return list(self.drivers.keys())


# Alias for backward compatibility
DriverTracer = DriverCollector


def collect_drivers(parser):
    """Convenience function to collect drivers"""
    return DriverCollector(parser)
