"""Simple driver collector using pyslang

增强版: 添加解析警告，显式打印不支持的语法结构
"""
import sys
import os
from typing import List, Dict as TyDict, Set

import pyslang
from pyslang import SyntaxKind

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.models import Driver, DriverKind, AssignKind

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


class DriverCollector:
    """Driver Collector
    
    增强: 解析过程中显式打印不支持的语法结构
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响driver分析',
        'PropertyDeclaration': 'property声明无driver',
        'SequenceDeclaration': 'sequence声明无driver',
        'ClassDeclaration': 'class内部driver可能不完整',
        'InterfaceDeclaration': 'interface内部driver可能不完整',
        'PackageDeclaration': 'package无driver',
        'ProgramDeclaration': 'program块driver可能不完整',
        'ClockingBlock': 'clocking block driver可能不完整',
        'ModportItem': 'modport信号driver可能不完整',
        'ConstraintBlock': 'constraint块无driver',
    }
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="DriverCollector"
        )
        self.drivers: Dict[str, List[Driver]] = {}
        self._unsupported_encountered: Set[str] = set()
        self._collect()
    
    def _collect(self):
        """收集所有driver"""
        for fname, tree in self.parser.trees.items():
            if not tree or not tree.root:
                self.warn_handler.warn_info(
                    f"文件 {fname} 解析树为空",
                    context="DriverCollection"
                )
                continue
            
            try:
                self._visit_module(tree.root, fname)
            except Exception as e:
                self.warn_handler.warn_error(
                    "ModuleVisit",
                    e,
                    context=f"file={fname}",
                    component="DriverCollector"
                )
    
    def _visit_module(self, node, source: str = ""):
        """访问模块节点"""
        if node.kind == SyntaxKind.ModuleDeclaration:
            self._process_module(node, self._get_module_name(node))
        elif node.kind == SyntaxKind.CompilationUnit:
            if hasattr(node, 'members') and node.members:
                for member in node.members:
                    if member.kind == SyntaxKind.ModuleDeclaration:
                        self._process_module(member, self._get_module_name(member))
                    else:
                        # 遇到非模块声明的成员
                        self._check_unsupported_node(member, source)
        else:
            # 其他顶层节点
            self._check_unsupported_node(node, source)
    
    def _check_unsupported_node(self, node, source: str = ""):
        """检查不支持的节点类型"""
        kind_name = str(node.kind) if hasattr(node, 'kind') else type(node).__name__
        
        # 检查是否是已知的不支持类型
        if kind_name in self.UNSUPPORTED_TYPES:
            if kind_name not in self._unsupported_encountered:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=source,
                    suggestion=self.UNSUPPORTED_TYPES[kind_name],
                    component="DriverCollector"
                )
                self._unsupported_encountered.add(kind_name)
        elif 'Declaration' in kind_name or 'Block' in kind_name:
            # 未知类型的声明/块
            if kind_name not in self._unsupported_encountered:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=source,
                    suggestion="可能影响driver分析完整性",
                    component="DriverCollector"
                )
                self._unsupported_encountered.add(kind_name)
    
    def _get_module_name(self, node):
        header = getattr(node, 'header', None)
        if header:
            name = getattr(header, 'name', None)
            if name:
                return getattr(name, 'value', 'unknown')
        return 'unknown'
    
    def _process_module(self, module, module_name: str):
        """处理模块"""
        if not hasattr(module, 'members') or not module.members:
            return
        
        for member in module.members:
            try:
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
                        self.warn_handler.warn_unsupported(
                            "UnknownAlwaysBlock",
                            context=f"module={module_name}",
                            suggestion="未识别always块类型，默认为always_ff",
                            component="DriverCollector"
                        )
                        self._process_always(member, DriverKind.AlwaysFF, module_name)
                elif kn == SyntaxKind.ContinuousAssign:
                    self._process_continuous_assign(member, module_name)
                else:
                    # 检查是否是不支持的类型
                    kind_name = str(kn)
                    if kind_name not in self._unsupported_encountered:
                        # 递归检查子节点
                        if hasattr(member, 'members'):
                            for child in getattr(member, 'members', []):
                                self._check_unsupported_node(child, module_name)
                            
            except Exception as e:
                self.warn_handler.warn_error(
                    "ModuleProcessing",
                    e,
                    context=f"module={module_name}, member={member.kind if hasattr(member, 'kind') else 'unknown'}",
                    component="DriverCollector"
                )
    
    def _process_always(self, block, kind, module_name):
        """处理always块"""
        try:
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
        except Exception as e:
            self.warn_handler.warn_error(
                "AlwaysBlockProcessing",
                e,
                context=f"module={module_name}",
                component="DriverCollector"
            )
    
    def _get_clock(self, block):
        """获取时钟信号"""
        try:
            stmt = getattr(block, 'statement', None)
            if not stmt:
                return ""
            if stmt.kind == SyntaxKind.TimingControlStatement:
                tc = getattr(stmt, 'timingControl', None)
                if tc:
                    expr = getattr(tc, 'expr', None)
                    if expr:
                        return self._get_signal_name(expr)
        except Exception:
            pass
        return ""
    
    def _walk_stmt(self, stmt, kind, module_name, clock):
        """遍历语句"""
        if not stmt:
            return
        
        try:
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
                    else:
                        # 未知类型的表达式
                        kind_name = str(expr.kind)
                        if kind_name not in self._unsupported_encountered:
                            self.warn_handler.warn_unsupported(
                                kind_name,
                                context=f"module={module_name}",
                                suggestion="表达式类型不支持",
                                component="DriverCollector"
                            )
                            self._unsupported_encountered.add(kind_name)
                return
            
            # 其他语句类型，递归检查子节点
            for attr in ['body', 'statements', 'statement']:
                if hasattr(stmt, attr):
                    child = getattr(stmt, attr)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                self._walk_stmt(c, kind, module_name, clock)
                        else:
                            self._walk_stmt(child, kind, module_name, clock)
                            
        except Exception as e:
            self.warn_handler.warn_error(
                "StatementWalk",
                e,
                context=f"module={module_name}",
                component="DriverCollector"
            )
    
    def _handle_assign(self, expr, kind, module_name, clock, assign_kind):
        """处理赋值"""
        try:
            lhs = getattr(expr, 'left', None)
            rhs = getattr(expr, 'right', None)
            if not lhs or not rhs:
                return
            
            dest = self._get_signal_name(lhs)
            sources = self._extract_sources(rhs)
            if dest:
                self._add_driver(dest, kind, sources, clock, assign_kind)
        except Exception as e:
            self.warn_handler.warn_error(
                "AssignmentHandling",
                e,
                context=f"module={module_name}",
                component="DriverCollector"
            )
    
    def _process_continuous_assign(self, assign, module_name):
        """处理连续赋值"""
        try:
            if not hasattr(assign, 'assignments'):
                return
            
            for i in range(len(assign.assignments)):
                a = assign.assignments[i]
                lhs = getattr(a, 'left', None)
                rhs = getattr(a, 'right', None)
                if lhs and rhs:
                    dest = self._get_signal_name(lhs)
                    sources = self._extract_sources(rhs)
                    if dest:
                        self._add_driver(dest, DriverKind.Continuous, sources, None, AssignKind.Blocking)
        except Exception as e:
            self.warn_handler.warn_error(
                "ContinuousAssignProcessing",
                e,
                context=f"module={module_name}",
                component="DriverCollector"
            )
    
    def _add_driver(self, dest, kind, sources, clock, assign_kind):
        """添加driver"""
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
        """获取信号名"""
        if not node:
            return ""
        kn = node.kind
        
        if kn == SyntaxKind.IdentifierName:
            ident = getattr(node, 'identifier', None)
            if ident:
                return str(getattr(ident, 'value', '') or getattr(ident, 'valueText', '')).strip()
        
        # IdentifierSelectName like pipe_valid[0]
        if kn == SyntaxKind.IdentifierSelectName:
            ident = getattr(node, 'identifier', None)
            if ident:
                return str(getattr(ident, 'value', '') or getattr(ident, 'valueText', '')).strip()
        
        return ""
    
    def _extract_sources(self, expr):
        """提取信号源"""
        if not expr:
            return []
        sources = []
        
        try:
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
            
        except Exception as e:
            self.warn_handler.warn_error(
                "SourceExtraction",
                e,
                context="extract_sources",
                component="DriverCollector"
            )
        
        return sources
    
    def _is_literal(self, name: str) -> bool:
        """判断是否是字面量"""
        name = name.lower()
        return name.isdigit() or name.startswith("'h") or name.startswith("'b") or name.startswith("'d")
    
    def get_drivers(self, signal):
        """Get drivers for a signal. Use '*' for all."""
        if signal == '*':
            all_drivers = []
            for sig, drvs in self.drivers.items():
                all_drivers.extend(drvs)
            return all_drivers
        return self.drivers.get(signal, [])
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()


def collect_drivers(parser, verbose: bool = True):
    """收集driver的便捷函数"""
    collector = DriverCollector(parser, verbose=verbose)
    all_drivers = []
    for drivers in collector.drivers.values():
        all_drivers.extend(drivers)
    return all_drivers


# Alias
DriverTracer = DriverCollector
