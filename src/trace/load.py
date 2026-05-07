"""Load Tracer - 负载追踪器"""

from typing import List, Dict, Set
from dataclasses import dataclass

import pyslang

from trace.parse_warn import ParseWarningHandler

# 导入语义层
try:
    from semantic.utils import extract_identifier as _extract_identifier
except ImportError:
    def _extract_identifier(node):
        if hasattr(node, 'text'):
            return node.text
        return ""


@dataclass
class LoadPoint:
    """信号加载点"""
    signal: str = ""      # 被加载的信号 (lhs)
    load_by: str = ""     # 加载来源信号 (rhs)
    context: str = ""      # 上下文 (always_ff, assign, etc.)
    line: int = 0


class LoadTracer:
    """加载点追踪器
    
    跟踪信号的加载关系：
    - 对于 assign c = a + b，c 被 a 和 b 加载
    """
    
    def __init__(self, trees: dict = None, verbose: bool = True):
        self.trees = trees or {}
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="LoadTracer")
        
        # 加载关系: signal -> list of LoadPoint
        self.loads: Dict[str, List[LoadPoint]] = {}
        
        # 所有负载信号 (被读取的信号)
        self._load_signals: Set[str] = set()
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'LoadTracer':
        """收集加载点"""
        # 直接遍历 AST 找所有赋值语句
        self._collect_from_tree(tree.root)
        
        return self
    
    def _iter_children(self, node):
        """安全地遍历子节点"""
        try:
            return list(node)
        except:
            return []
    
    def _collect_from_tree(self, node, depth=0):
        """从树中收集加载关系"""
        if depth > 25 or not hasattr(node, 'kind'):
            return
        
        kind = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        # 只处理顶层节点，不递归处理已处理的节点类型
        if kind == 'ContinuousAssign':
            self._process_continuous_assign(node)
        elif kind == 'NonblockingAssignmentExpression':
            self._process_nb_assign(node, 'always_ff')
        elif kind == 'AssignmentExpression':
            self._process_assign_expr(node, 'always_comb')
        elif kind in ('IfStatement', 'CaseStatement'):
            self._process_conditional_loads(node)
        else:
            # 只有非目标节点才递归遍历
            try:
                for child in list(node):
                    self._collect_from_tree(child, depth + 1)
            except:
                pass
    
    def _process_continuous_assign(self, node):
        """处理连续赋值 assign x = y"""
        for child in self._iter_children(node):
            if hasattr(child, 'kind') and child.kind.name == 'SeparatedList':
                for sub in self._iter_children(child):
                    if hasattr(sub, 'kind') and sub.kind.name == 'AssignmentExpression':
                        self._extract_assignment_loads(sub, 'assign')
    
    def _process_nb_assign(self, node, context):
        """处理非阻塞赋值"""
        self._extract_assignment_loads(node, context)
    
    def _process_assign_expr(self, node, context):
        """处理赋值表达式"""
        self._extract_assignment_loads(node, context)
    
    def _extract_assignment_loads(self, node, context):
        """提取赋值语句的负载关系"""
        # 获取行号
        line = 0
        if hasattr(node, 'span'):
            line = node.span.start_line
        
        # 遍历 AST 找 lhs 和 rhs
        lhs_signals = []
        rhs_signals = []
        found_eq = False
        
        # 递归扫描
        def scan(n):
            nonlocal found_eq
            
            if not hasattr(n, 'kind'):
                return
            
            kind = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
            
            # 调试
            if kind in ('Identifier', 'IdentifierName', 'ConditionalExpression', 'ConditionalPredicate', 'ConditionalPattern'):
                print(f"scan: kind={kind}, found_eq={found_eq}")
            
            # Equals 操作符分隔 lhs 和 rhs
            if kind == 'Equals':
                found_eq = True
                # 继续遍历子节点 (rhs 部分)
                for sub in self._iter_children(n):
                    scan(sub)
                return
            
            # 跳过元节点
            if kind in ('SyntaxList', 'TokenList', 'SeparatedList', 'Plus', 'Minus', 'Multiply',
                       'OpenParenthesis', 'CloseParenthesis', 'OpenBracket', 'CloseBracket',
                       'IntegerLiteral', 'IntegerBase', 'VariableDimension', 'RangeDimensionSpecifier',
                       'SimpleRangeSelect', 'TimeUnit', 'DoublePeriod', 'AssignKeyword',
                       'Question', 'Colon', 'At', 'DoublePeriod', 'Semicolon'):
                pass
            # ElementSelect 和 BitSelect 自然遍历
            elif kind in ('ElementSelect', 'BitSelect'):
                for child in self._iter_children(n):
                    scan(child)
            # 标识符
            elif kind in ('Identifier', 'IdentifierName'):
                sig = _extract_identifier(n)
                if sig:
                    if not found_eq:
                        lhs_signals.append(sig)
                    else:
                        rhs_signals.append(sig)
            # IdentifierSelectName 包含数组索引，SyntaxList 可能包含索引表达式
            elif kind == 'IdentifierSelectName':
                for child in self._iter_children(n):
                    child_kind = child.kind.name if hasattr(child, 'kind') else ''
                    if child_kind == 'SyntaxList':
                        for sub in self._iter_children(child):
                            scan(sub)
                    else:
                        scan(child)
            # 三元表达式 ConditionalExpression -> ConditionalPredicate ? then : else
            elif kind == 'ConditionalExpression':
                # 三元表达式的条件部分（第一个子节点）应该被处理为 rhs 的一部分
                children = self._iter_children(n)
                for i, sub in enumerate(children):
                    # 第一个是 ConditionalPredicate（条件），条件中的信号应该被提取
                    if i == 0 and hasattr(sub, 'kind') and sub.kind.name == 'ConditionalPredicate':
                        for p in self._iter_children(sub):
                            if hasattr(p, 'kind') and p.kind.name == 'SeparatedList':
                                # SeparatedList 包含实际的信号
                                for sp in self._iter_children(p):
                                    if hasattr(sp, 'kind') and sp.kind.name == 'ConditionalPattern':
                                        for cp in self._iter_children(sp):
                                            scan(cp)
                    else:
                        scan(sub)
            # 其他表达式 - 继续遍历
            else:
                for sub in self._iter_children(n):
                    scan(sub)
        
        scan(node)
        
        # 记录加载关系
        for lhs in lhs_signals:
            self._load_signals.add(lhs)
            for rhs in rhs_signals:
                if rhs and rhs not in lhs_signals:
                    self._add_load(lhs, rhs, context, line)
                    self._load_signals.add(rhs)
    
    def _process_conditional_loads(self, node):
        """处理条件语句中的负载 (if/case)"""
        def scan(n):
            if not hasattr(n, 'kind'):
                return
            
            kind = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
            
            # 条件中的信号
            if kind in ('ConditionalPredicate', 'CaseStatementItem'):
                for sub in self._iter_children(n):
                    sigs = self._extract_signals(sub)
                    for sig in sigs:
                        self._load_signals.add(sig)
            
            for sub in self._iter_children(n):
                scan(sub)
        
        scan(node)
    
    def _extract_signals(self, node, depth=0) -> List[str]:
        """从表达式中递归提取所有信号"""
        if depth > 15 or not hasattr(node, 'kind'):
            return []
        
        signals = []
        kind = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        # 跳过元节点
        if kind in ('SyntaxList', 'TokenList', 'SeparatedList', 'Equals', 'Plus', 'Minus', 
                   'Multiply', 'OpenParenthesis', 'CloseParenthesis', 'IntegerLiteral',
                   'IntegerBase', 'VariableDimension', 'RangeDimensionSpecifier',
                   'SimpleRangeSelect', 'TimeUnit', 'DoublePeriod',
                   'OpenBracket', 'CloseBracket', 'ElementSelect', 'BitSelect'):
            pass
        # 标识符
        elif kind in ('Identifier', 'IdentifierName'):
            sig = _extract_identifier(node)
            if sig:
                signals.append(sig)
        # 跳过操作符关键字
        elif kind in ('Equals', 'Plus', 'Minus', 'Multiply', 'Divide', 'Modulo',
                     'And', 'Or', 'Xor', 'Not', 'Tilde', 'Ampersand', 'Bar',
                     'Caret', 'QuestionMark', 'Colon'):
            pass
        # 继续遍历
        else:
            for child in self._iter_children(node):
                signals.extend(self._extract_signals(child, depth + 1))
        
        return signals
    
    def _add_load(self, target: str, source: str, context: str, line: int):
        """添加加载关系"""
        if not target or not source:
            return
        
        if target not in self.loads:
            self.loads[target] = []
        
        # 检查是否已存在
        for lp in self.loads[target]:
            if lp.load_by == source and lp.context == context:
                return
        
        load_point = LoadPoint(
            signal=target,
            load_by=source,
            context=context,
            line=line
        )
        self.loads[target].append(load_point)
    
    def find_load(self, signal: str) -> List[LoadPoint]:
        """查找信号的加载点"""
        return self.loads.get(signal, [])
    
    @property
    def all_signals(self) -> List[str]:
        """所有负载信号"""
        return sorted(list(self._load_signals))
