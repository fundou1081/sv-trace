"""Simple driver collector using pyslang"""
import sys
import os
from typing import List, Dict as TyDict

import pyslang
from pyslang import SyntaxKind

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.models import Driver, DriverKind, AssignKind


class DriverCollector:
    def __init__(self, parser):
        self.parser = parser
        self.drivers: Dict[str, List[Driver]] = {}
        self._collect()

    def _collect(self):
        for fname, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            self._visit_module(tree.root)

    def _visit_module(self, node):
        if node.kind == SyntaxKind.ModuleDeclaration:
            self._process_module(node, self._get_module_name(node))
        elif node.kind == SyntaxKind.CompilationUnit:
            for member in node.members:
                if member.kind == SyntaxKind.ModuleDeclaration:
                    self._process_module(member, self._get_module_name(member))

    def _get_module_name(self, node):
        header = getattr(node, 'header', None)
        if header:
            name = getattr(header, 'name', None)
            if name:
                return getattr(name, 'value', 'unknown')
        return 'unknown'

    def _process_module(self, module, module_name):
        for member in module.members:
            kn = member.kind
            if kn == SyntaxKind.AlwaysBlock:
                # 检查 always 块类型
                code = str(member) if member else ''
                if '@(posedge' in code or '@(negedge' in code:
                    self._process_always(member, DriverKind.AlwaysFF, module_name)
                elif '@(*)' in code or '@(*) ' in code:
                    self._process_always(member, DriverKind.AlwaysComb, module_name)
                else:
                    # 默认当作 always_ff
                    self._process_always(member, DriverKind.AlwaysFF, module_name)
            elif kn == SyntaxKind.ContinuousAssign:
                self._process_continuous_assign(member, module_name)

    def _process_always(self, block, kind, module_name):
        clock = self._get_clock(block)
        stmt = getattr(block, 'statement', None)
        if not stmt:
            return
        if stmt.kind == SyntaxKind.TimingControlStatement:
            inner = getattr(stmt, 'statement', None)
            if inner:
                self._walk_stmt(inner, kind, module_name, clock)
        else:
            self._walk_stmt(stmt, kind, module_name, clock)

    def _get_clock(self, block):
        stmt = getattr(block, 'statement', None)
        if not stmt:
            return ""
        if stmt.kind == SyntaxKind.TimingControlStatement:
            tc = getattr(stmt, 'timingControl', None)
            if tc:
                expr = getattr(tc, 'expr', None)
                if expr:
                    return self._get_signal_name(expr)
        return ""

    def _walk_stmt(self, stmt, kind, module_name, clock):
        if not stmt:
            return
        kn = stmt.kind
        
        if kn == SyntaxKind.SequentialBlockStatement:
            for i in range(len(stmt.items)):
                self._walk_stmt(stmt.items[i], kind, module_name, clock)
            return
        
        if kn == SyntaxKind.ConditionalStatement:
            then = getattr(stmt, 'statement', None)
            if then:
                self._walk_stmt(then, kind, module_name, clock)
            # 处理 else 分支
            else_clause = getattr(stmt, 'elseClause', None)
            if else_clause:
                clause = getattr(else_clause, 'clause', None)
                if clause:
                    self._walk_stmt(clause, kind, module_name, clock)
            return
        
        if kn == SyntaxKind.ExpressionStatement:
            expr = getattr(stmt, 'expr', None)
            if expr:
                if expr.kind == SyntaxKind.AssignmentExpression:
                    self._handle_assign(expr, kind, module_name, clock, AssignKind.Blocking)
                elif expr.kind == SyntaxKind.NonblockingAssignmentExpression:
                    self._handle_assign(expr, kind, module_name, clock, AssignKind.Nonblocking)
            return

    def _handle_assign(self, expr, kind, module_name, clock, assign_kind):
        lhs = getattr(expr, 'left', None)
        rhs = getattr(expr, 'right', None)
        if not lhs or not rhs:
            return
        
        dest = self._get_signal_name(lhs)
        sources = self._extract_sources(rhs)
        if dest:
            self._add_driver(dest, kind, sources, clock, assign_kind)

    def _process_continuous_assign(self, assign, module_name):
        for i in range(len(assign.assignments)):
            a = assign.assignments[i]
            lhs = getattr(a, 'left', None)
            rhs = getattr(a, 'right', None)
            if lhs and rhs:
                dest = self._get_signal_name(lhs)
                sources = self._extract_sources(rhs)
                if dest:
                    self._add_driver(dest, DriverKind.Continuous, sources, None, AssignKind.Blocking)

    def _add_driver(self, dest, kind, sources, clock, assign_kind):
        if not dest:
            return
        driver = Driver(
            signal=dest,
            kind=kind,
            module='unknown',
            sources=sources,
            clock=clock or '',
            assign_kind=assign_kind,
        )
        if dest not in self.drivers:
            self.drivers[dest] = []
        self.drivers[dest].append(driver)

    def _get_signal_name(self, node):
        if not node:
            return ""
        kn = node.kind
        
        if kn == SyntaxKind.IdentifierName:
            ident = getattr(node, 'identifier', None)
            if ident:
                return str(getattr(ident, 'value', '') or getattr(ident, 'valueText', '')).strip()
        
        # IdentifierSelectName like pipe_valid[0]
        if kn == SyntaxKind.IdentifierSelectName:
            # identifier is a Token
            ident = getattr(node, 'identifier', None)
            if ident:
                # Token has value attribute
                return str(getattr(ident, 'value', '') or getattr(ident, 'valueText', '')).strip()
        
        return ""

    def _extract_sources(self, expr):
        if not expr:
            return []
        sources = []
        kn = expr.kind
        
        # IdentifierName or IdentifierSelectName
        if kn in (SyntaxKind.IdentifierName, SyntaxKind.IdentifierSelectName):
            name = self._get_signal_name(expr)
            if name and not self._is_literal(name):
                sources.append(name)
            return sources
        
        # Binary expression - has left/right
        if hasattr(expr, 'left') and hasattr(expr, 'right'):
            left = getattr(expr, 'left', None)
            right = getattr(expr, 'right', None)
            if left:
                sources.extend(self._extract_sources(left))
            if right:
                sources.extend(self._extract_sources(right))
            return sources
        
        # Unary expression - has operand
        if hasattr(expr, 'operand'):
            operand = getattr(expr, 'operand', None)
            if operand:
                sources.extend(self._extract_sources(operand))
            return sources
        
        # Literal expression - not a source
        if 'Literal' in str(kn):
            return sources
        
        return sources

    
    def get_drivers(self, signal):
        """Get drivers for a signal. Use '*' for all."""
        if signal == '*':
            all_drivers = []
            for sig, drvs in self.drivers.items():
                all_drivers.extend(drvs)
            return all_drivers
        return self.drivers.get(signal, [])

def _is_literal(self, name):
        name = name.lower()
        return name.isdigit() or name.startswith("'h") or name.startswith("'b")


def collect_drivers(parser):
    collector = DriverCollector(parser)
    all_drivers = []
    for drivers in collector.drivers.values():
        all_drivers.extend(drivers)
    return all_drivers

# Alias
DriverTracer = DriverCollector
