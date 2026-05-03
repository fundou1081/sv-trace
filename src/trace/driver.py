"""Driver collector using pyslang visit API.

该模块提供从 SystemVerilog AST 中提取信号驱动关系的功能。

Example:
    >>> from parse import SVParser
    >>> from trace.driver import DriverCollector
    >>> p = SVParser()
    >>> tree = p.parse_text(sv_code)
    >>> p.trees["test.sv"] = tree
    >>> dc = DriverCollector(p, verbose=True)
    >>> drivers = dc.get_drivers('*')
"""

import sys
import os
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field

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


# 二元运算符表达式类型名称列表
BINARY_EXPR_KINDS = {
    'AddExpression', 'SubtractExpression', 'MultiplyExpression', 'DivideExpression',
    'ModExpression', 'PowerExpression',
    'EqualityExpression', 'InequalityExpression', 'CaseEqualityExpression', 'CaseInequalityExpression',
    'GreaterThanExpression', 'LessThanExpression', 'GreaterThanEqualExpression', 'LessThanEqualExpression',
    'WildcardEqualityExpression', 'WildcardInequalityExpression',
    'LogicalAndExpression', 'LogicalOrExpression', 'LogicalImplicationExpression',
    'BinaryAndExpression', 'BinaryOrExpression', 'BinaryXorExpression', 'BinaryXnorExpression',
    'LogicalShiftLeftExpression', 'LogicalShiftRightExpression', 
    'ArithmeticShiftLeftExpression', 'ArithmeticShiftRightExpression',
    'MinTypMaxExpression',
}

# 一元运算符表达式类型名称列表
UNARY_EXPR_KINDS = {
    'UnaryPlusExpression', 'UnaryMinusExpression', 'UnaryBitwiseNotExpression', 'UnaryLogicalNotExpression',
    'PostincrementExpression', 'PostdecrementExpression', 
    'UnaryPreincrementExpression', 'UnaryPredecrementExpression',
}

# 条件表达式类型
CONDITIONAL_EXPR_KINDS = {'ConditionalExpression', 'TernaryExpression'}


def _iter_children(node) -> List:
    """安全地遍历节点的子节点
    
    Args:
        node: pyslang AST 节点
        
    Returns:
        List: 子节点列表
    """
    if node is None:
        return []
    if isinstance(node, list):
        return node
    if hasattr(node, '__iter__') and not isinstance(node, str):
        try:
            return list(node)
        except:
            pass
    if hasattr(node, 'kind'):
        return [node]
    return []


class DriverCollector:
    """收集设计中所有信号的驱动源信息
    
    该类遍历 pyslang AST 提取：
    - always_ff/always_comb/always_latch 过程块中的赋值
    - 连续赋值 (assign)
    - 每个驱动的源信号列表
    
    Attributes:
        drivers: 信号名到驱动列表的映射
        warn_handler: 警告处理器
        
    Example:
        >>> dc = DriverCollector(parser, verbose=True)
        >>> drivers = dc.get_drivers('*')  # 获取所有驱动
        >>> clk_drivers = dc.find_driver('clk')
    """
    
    # 不支持的语法类型映射
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
        """初始化 DriverCollector
        
        Args:
            parser: SVParser 实例
            verbose: 是否打印警告信息
        """
        self.parser = parser
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="DriverCollector"
        )
        self.drivers: Dict[str, List[Driver]] = {}
        self._unsupported_encountered: Set[str] = set()
        self._collect()
    
    def _collect(self) -> None:
        """从所有解析树收集驱动信息"""
        for fname, tree in self.parser.trees.items():
            if not tree or not tree.root:
                self.warn_handler.warn_info(
                    f"文件 {fname} 解析树为空",
                    context="DriverCollection"
                )
                continue
            try:
                self._visit_tree(tree.root, fname)
            except Exception as e:
                self.warn_handler.warn_error(
                    "TreeVisit", e,
                    context=f"file={fname}",
                    component="DriverCollector"
                )
    
    def _check_unsupported_node(self, node, source: str = "") -> None:
        """检查不支持的节点类型
        
        Args:
            node: AST 节点
            source: 来源标识
        """
        kind_name = str(node.kind) if hasattr(node, 'kind') else type(node).__name__
        
        if kind_name in self.UNSUPPORTED_TYPES:
            if kind_name not in self._unsupported_encountered:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=source,
                    suggestion=self.UNSUPPORTED_TYPES[kind_name],
                    component="DriverCollector"
                )
                self._unsupported_encountered.add(kind_name)
    
    def _visit_tree(self, root, source: str = "") -> None:
        """遍历语法树查找赋值语句
        
        Args:
            root: 语法树根节点
            source: 来源标识
        """
        module_name = ""
        
        def callback(node):
            nonlocal module_name
            
            try:
                kind = node.kind
                
                # 跟踪模块名
                if kind == SyntaxKind.ModuleDeclaration:
                    if hasattr(node, 'header') and hasattr(node.header, 'name'):
                        module_name = str(node.header.name)
                    return pyslang.VisitAction.Advance
                
                # 查找过程块
                if kind in (SyntaxKind.AlwaysFFBlock, SyntaxKind.AlwaysCombBlock, 
                           SyntaxKind.AlwaysLatchBlock, SyntaxKind.AlwaysBlock):
                    self._process_procedural_block(node, module_name, kind, source)
                    return pyslang.VisitAction.Skip
                
                # 查找连续赋值
                if kind == SyntaxKind.ContinuousAssign:
                    self._process_continuous_assign(node, module_name, source)
                    return pyslang.VisitAction.Advance
                
                # 检查不支持的节点类型
                kind_name = str(kind)
                if kind_name not in self._unsupported_encountered:
                    if kind_name in self.UNSUPPORTED_TYPES or \
                       ('Declaration' in kind_name and kind_name != 'ModuleDeclaration'):
                        self._check_unsupported_node(node, source)
                
                return pyslang.VisitAction.Advance
                
            except Exception as e:
                self.warn_handler.warn_error(
                    "TreeVisit", e,
                    context=f"source={source}",
                    component="DriverCollector"
                )
                return pyslang.VisitAction.Advance
        
        root.visit(callback)
    
    def _process_procedural_block(self, node, module_name: str, 
                                  kind: SyntaxKind, source: str = "") -> None:
        """处理过程块 (always_ff, always_comb etc.)
        
        Args:
            node: AST 节点
            module_name: 模块名
            kind: 块类型
            source: 来源标识
        """
        try:
            # 确定驱动类型
            kind_name = str(kind)
            if 'AlwaysFF' in kind_name:
                driver_kind = DriverKind.AlwaysFF
            elif 'AlwaysComb' in kind_name:
                driver_kind = DriverKind.AlwaysComb
            elif 'AlwaysLatch' in kind_name:
                driver_kind = DriverKind.AlwaysLatch
            else:
                driver_kind = DriverKind.AlwaysFF
            
            # TimingControlStatement
            stmt = getattr(node, 'statement', None)
            if not stmt:
                return
            
            # 提取时钟
            timing_ctrl = getattr(stmt, 'timingControl', None)
            clock = ""
            if timing_ctrl:
                clock = self._extract_clock_from_timing_control(timing_ctrl)
            
            # 获取实际语句
            body = getattr(stmt, 'statement', None)
            if not body:
                body = stmt
            
            self._walk_statement(body, driver_kind, module_name, clock, source)
                    
        except Exception as e:
            self.warn_handler.warn_error(
                "ProceduralBlockProcessing", e,
                context=f"module={module_name}",
                component="DriverCollector"
            )
    
    def _extract_clock_from_timing_control(self, tc) -> str:
        """从 timingControl 提取时钟信号名
        
        Args:
            tc: timingControl 节点
            
        Returns:
            str: 时钟信号名
        """
        try:
            for child in tc:
                if child.kind == SyntaxKind.SignalEventExpression:
                    for subchild in child:
                        if subchild.kind == SyntaxKind.IdentifierName:
                            return str(subchild).strip()
        except Exception:
            pass
        return ""
    
    def _walk_statement(self, stmt, driver_kind: DriverKind, 
                       module_name: str, clock: str, source: str = "") -> None:
        """遍历语句查找赋值
        
        Args:
            stmt: 语句节点
            driver_kind: 驱动类型
            module_name: 模块名
            clock: 时钟信号
            source: 来源标识
        """
        if stmt is None:
            return
        
        try:
            stmt_kind = getattr(stmt, 'kind', None)
            if stmt_kind is None:
                return
            
            stmt_kind_name = str(stmt_kind)
            
            # SequentialBlockStatement (begin...end)
            if stmt_kind == SyntaxKind.SequentialBlockStatement:
                items = getattr(stmt, 'items', None)
                if items:
                    for item in _iter_children(items):
                        self._walk_statement(item, driver_kind, module_name, clock, source)
                return
            
            # ExpressionStatement
            if stmt_kind == SyntaxKind.ExpressionStatement:
                expr = getattr(stmt, 'expr', None)
                if expr:
                    self._process_expression(expr, driver_kind, module_name, clock, source)
                return
            
            # ConditionalStatement (if-else)
            if 'Conditional' in stmt_kind_name or 'If' in stmt_kind_name:
                then_stmt = getattr(stmt, 'statement', None)
                if then_stmt:
                    self._walk_statement(then_stmt, driver_kind, module_name, clock, source)
                
                else_clause = getattr(stmt, 'elseClause', None)
                if else_clause:
                    else_stmt = getattr(else_clause, 'clause', None)
                    if else_stmt:
                        self._walk_statement(else_stmt, driver_kind, module_name, clock, source)
                    else:
                        self._walk_statement(else_clause, driver_kind, module_name, clock, source)
                return
            
            # CaseStatement
            if 'Case' in stmt_kind_name:
                items = getattr(stmt, 'items', None)
                if items:
                    for item in _iter_children(items):
                        clause = getattr(item, 'clause', None)
                        if clause:
                            self._walk_statement(clause, driver_kind, module_name, clock, source)
                return
            
            # ForLoopStatement
            if 'ForLoop' in stmt_kind_name:
                body = getattr(stmt, 'statement', None)
                if body:
                    self._walk_statement(body, driver_kind, module_name, clock, source)
                return
            
            # WhileLoopStatement
            if 'WhileLoop' in stmt_kind_name:
                body = getattr(stmt, 'statement', None)
                if body:
                    self._walk_statement(body, driver_kind, module_name, clock, source)
                return
            
        except Exception as e:
            self.warn_handler.warn_error(
                "StatementWalk", e,
                context=f"module={module_name}",
                component="DriverCollector"
            )
    
    def _process_expression(self, expr, driver_kind: DriverKind,
                          module_name: str, clock: str, source: str = "") -> None:
        """处理表达式中的赋值
        
        Args:
            expr: 表达式节点
            driver_kind: 驱动类型
            module_name: 模块名
            clock: 时钟信号
            source: 来源标识
        """
        if expr is None:
            return
        
        try:
            expr_kind = getattr(expr, 'kind', None)
            if expr_kind is None:
                return
            
            # AssignmentExpression (=)
            if expr_kind == SyntaxKind.AssignmentExpression:
                self._handle_assignment(expr.left, expr.right, driver_kind, 
                                      module_name, clock, AssignKind.Blocking, source)
                return
            
            # NonblockingAssignmentExpression (<=)
            if expr_kind == SyntaxKind.NonblockingAssignmentExpression:
                self._handle_assignment(expr.left, expr.right, driver_kind,
                                      module_name, clock, AssignKind.Nonblocking, source)
                return
            
        except Exception as e:
            self.warn_handler.warn_error(
                "ExpressionProcessing", e,
                context=f"module={module_name}",
                component="DriverCollector"
            )
    
    def _handle_assignment(self, lhs, rhs, driver_kind: DriverKind,
                          module_name: str, clock: str, 
                          assign_kind: AssignKind, source: str = "") -> None:
        """处理赋值语句
        
        Args:
            lhs: 左操作数
            rhs: 右操作数
            driver_kind: 驱动类型
            module_name: 模块名
            clock: 时钟信号
            assign_kind: 赋值类型
            source: 来源标识
        """
        if lhs is None or rhs is None:
            return
        
        try:
            target = self._get_signal_name(lhs)
            if not target:
                return
            
            sources = self._extract_sources(rhs)
            
            line = 0
            if hasattr(lhs, 'sourceRange') and lhs.sourceRange:
                try:
                    line = lhs.sourceRange.start.offset if hasattr(lhs.sourceRange.start, 'offset') else 0
                except:
                    line = 0
            
            driver = Driver(
                signal=target,
                kind=driver_kind,
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
            self.warn_handler.warn_error(
                "AssignmentHandling", e,
                context=f"module={module_name}",
                component="DriverCollector"
            )
    
    def _process_continuous_assign(self, node, module_name: str, 
                                  source: str = "") -> None:
        """处理连续赋值
        
        Args:
            node: AST 节点
            module_name: 模块名
            source: 来源标识
        """
        try:
            if not hasattr(node, 'assignments'):
                return
            
            assignments = getattr(node, 'assignments', None)
            if not assignments:
                return
            
            for a in _iter_children(assignments):
                lhs = getattr(a, 'left', None)
                rhs = getattr(a, 'right', None)
                
                if lhs is None or rhs is None:
                    continue
                
                target = self._get_signal_name(lhs)
                if not target:
                    continue
                
                sources = self._extract_sources(rhs)
                
                driver = Driver(
                    signal=target,
                    kind=DriverKind.Continuous,
                    module=module_name,
                    sources=sources,
                    clock="",
                    lines=[],
                    condition=""
                )
                
                if target not in self.drivers:
                    self.drivers[target] = []
                self.drivers[target].append(driver)
                    
        except Exception as e:
            self.warn_handler.warn_error(
                "ContinuousAssignProcessing", e,
                context=f"module={module_name}",
                component="DriverCollector"
            )
    
    def _get_signal_name(self, node) -> str:
        """从节点获取信号名
        
        Args:
            node: AST 节点
            
        Returns:
            str: 信号名
        """
        if node is None:
            return ""
        
        kind_name = str(getattr(node, 'kind', ''))
        
        if 'IdentifierSelectName' in kind_name or 'Identifier' in kind_name:
            name = str(node).strip()
            if '[' in name:
                name = name.split('[')[0]
            return name
        
        return ""
    
    def _extract_sources(self, node) -> List[str]:
        """从表达式提取源信号列表
        
        Args:
            node: AST 节点
            
        Returns:
            List[str]: 源信号列表
        """
        sources = []
        
        if node is None:
            return sources
        
        kind_name = str(getattr(node, 'kind', ''))
        
        # Identifier
        if 'IdentifierSelectName' in kind_name or kind_name == 'IdentifierName':
            name = str(node).strip()
            if '[' in name:
                name = name.split('[')[0]
            if name and not self._is_literal(name):
                sources.append(name)
            return sources
        
        # Literal
        if 'Literal' in kind_name or 'Number' in kind_name:
            return sources
        
        # Binary expression
        if kind_name in BINARY_EXPR_KINDS:
            left = getattr(node, 'left', None)
            right = getattr(node, 'right', None)
            if left:
                sources.extend(self._extract_sources(left))
            if right:
                sources.extend(self._extract_sources(right))
            return sources
        
        # Unary expression
        if kind_name in UNARY_EXPR_KINDS:
            operand = getattr(node, 'operand', None)
            if operand:
                sources.extend(self._extract_sources(operand))
            return sources
        
        # Conditional expression (ternary)
        if kind_name in CONDITIONAL_EXPR_KINDS:
            condition = getattr(node, 'condition', None)
            when_true = getattr(node, 'whenTrue', None)
            when_false = getattr(node, 'whenFalse', None)
            if condition:
                sources.extend(self._extract_sources(condition))
            if when_true:
                sources.extend(self._extract_sources(when_true))
            if when_false:
                sources.extend(self._extract_sources(when_false))
            return sources
        
        return sources
    
    def _is_literal(self, name: str) -> bool:
        """检查名称是否为字面量
        
        Args:
            name: 字符串
            
        Returns:
            bool: 是否为字面量
        """
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
        """获取信号的驱动列表
        
        Args:
            signal: 信号名，'*' 表示获取所有驱动
            
        Returns:
            List[Driver]: 驱动列表
        """
        if signal == '*':
            all_drivers = []
            for sig, drvs in self.drivers.items():
                all_drivers.extend(drvs)
            return all_drivers
        return self.drivers.get(signal, [])
    
    def find_driver(self, signal_name: str, 
                   include_bit_select: bool = False) -> List[Driver]:
        """查找信号的驱动
        
        Args:
            signal_name: 信号名
            include_bit_select: 是否包含位选
            
        Returns:
            List[Driver]: 驱动列表
        """
        drivers = self.drivers.get(signal_name, [])
        
        if include_bit_select:
            for sig, drvs in self.drivers.items():
                if sig.startswith(signal_name + '['):
                    drivers.extend(drvs)
        
        return drivers
    
    def get_all_signals(self) -> List[str]:
        """获取所有有驱动的信号列表
        
        Returns:
            List[str]: 信号名列表
        """
        return list(self.drivers.keys())
    
    def get_warning_report(self) -> str:
        """获取警告报告
        
        Returns:
            str: 警告报告字符串
        """
        return self.warn_handler.get_report()
    
    def print_warning_report(self) -> None:
        """打印警告报告到标准输出"""
        self.warn_handler.print_report()


# 别名
DriverTracer = DriverCollector


def collect_drivers(parser, verbose: bool = True) -> DriverCollector:
    """便捷函数：收集驱动信息
    
    Args:
        parser: SVParser 实例
        verbose: 是否打印警告
        
    Returns:
        DriverCollector: 驱动收集器实例
    """
    return DriverCollector(parser, verbose=verbose)


    def _get_bit_range(self, node) -> Optional[Tuple[int, int]]:
        """从节点获取位范围
        
        Args:
            node: AST 节点 (bit select)
            
        Returns:
            Optional[Tuple[int, int]]: (msb, lsb) or None
        """
        if node is None:
            return None
        
        # Check for BitSelect or PartSelect
        if hasattr(node, 'select') and node.select:
            select = node.select
            # PartSelect has left and right expressions
            if hasattr(select, 'left') and hasattr(select, 'right'):
                try:
                    msb_str = str(select.left).strip()
                    lsb_str = str(select.right).strip()
                    msb = int(msb_str, 0) if msb_str else 0
                    lsb = int(lsb_str, 0) if lsb_str else 0
                    return (msb, lsb)
                except (ValueError, AttributeError):
                    pass
        
        return None
