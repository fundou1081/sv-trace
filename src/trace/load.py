"""
LoadTracer - 负载追踪器

按项目纪律重构 - 负载关系提取
符合铁律 1: AST 唯一数据源
符合铁律 17: 提取逻辑封装为独立 Visitor 类

使用 pyslang.visit() 遍历 AST，提取信号的加载关系。
"""

import pyslang
from typing import List, Dict, Set
from dataclasses import dataclass

from trace.parse_warn import ParseWarningHandler

# 公共工具函数
try:
    from semantic.utils import extract_identifier as _extract_identifier
except ImportError:
    def _extract_identifier(node):
        if hasattr(node, 'text') and node.text:
            return node.text
        return ""


@dataclass
class LoadPoint:
    """信号加载点
    
    表示: signal 被 load_by 加载
    例如: q <= data → LoadPoint(signal='q', load_by='data', context='always_ff')
    """
    signal: str = ""      # 被加载的信号 (lhs)
    load_by: str = ""     # 加载来源信号 (rhs)
    context: str = ""     # 上下文 (always_ff, assign, etc.)
    line: int = 0


class LoadExtractor:
    """负载提取器
    
    符合铁律 17: 提取逻辑封装为独立 Visitor 类
    符合铁律 1: 仅使用 pyslang AST 遍历
    """
    
    # 赋值操作符
    _ASSIGN_OPS: Set[str] = {
        'Equals', 'LessThanEquals',
        'PlusEquals', 'MinusEquals', 'MultiplyEquals', 'DivideEquals', 'ModuloEquals',
        'AndEquals', 'OrEquals', 'XorEquals',
        'LeftShiftEquals', 'RightShiftEquals',
    }
    
    # 应跳过的元节点
    _SKIP_KINDS: Set[str] = {
        'TokenList',
        'Plus', 'Minus', 'Multiply', 'Divide', 'Modulo',
        'OpenParenthesis', 'CloseParenthesis',
        'OpenBracket', 'CloseBracket',
        'IntegerLiteral', 'IntegerBase', 'VariableDimension',
        'RangeDimensionSpecifier', 'SimpleRangeSelect',
        'TimeUnit', 'DoublePeriod',
        'AssignKeyword', 'Question', 'Colon', 'At',
        'And', 'Or', 'Xor', 'Not', 'Tilde',
        'Ampersand', 'Bar', 'Caret',
    }
    
    def __init__(self, verbose: bool = False):
        self._loads: List[LoadPoint] = []
        self._load_signals: Set[str] = set()
        self._verbose = verbose
    
    def extract(self, root) -> 'LoadExtractor':
        def visitor(node):
            action = self._on_node(node)
            return action if action is not None else pyslang.VisitAction.Advance
        root.visit(visitor)
        return self
    
    @property
    def loads(self) -> List[LoadPoint]:
        return self._loads
    
    @property
    def load_signals(self) -> Set[str]:
        return self._load_signals
    
    def _iter_children(self, node) -> list:
        try:
            return list(node)
        except:
            return []
    
    def _get_kind(self, node) -> str:
        if not hasattr(node, 'kind'):
            return ""
        kind = node.kind
        if hasattr(kind, 'name'):
            return kind.name
        return str(kind)
    
    def _scan_expression(self, node, lhs_list: list, rhs_list: list, found_eq: bool):
        """递归扫描表达式，收集 lhs/rhs 标识符"""
        if not hasattr(node, 'kind'):
            return
        
        kind = self._get_kind(node)
        if not kind:
            return
        
        if kind in self._SKIP_KINDS:
            return
        
        if kind in self._ASSIGN_OPS:
            return
        
        if kind in ('Identifier', 'IdentifierName'):
            sig = _extract_identifier(node)
            if sig:
                if not found_eq:
                    lhs_list.append(sig)
                else:
                    rhs_list.append(sig)
            return
        
        if kind in ('ElementSelect', 'BitSelect'):
            # 递归到子节点，提取 base 和 index
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq)
            return
        
        if kind == 'IdentifierSelectName':
            # 递归到子节点，提取 base 和下标
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq)
            return
        
        # SyntaxList: 递归处理（可能包含 ConditionalPattern 等）
        if kind == 'SyntaxList':
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq)
            return
        
        # SeparatedList: 递归处理
        if kind == 'SeparatedList':
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq)
            return
        
        # ConditionalExpression (三元表达式): 所有子节点都是 RHS
        if kind == 'ConditionalExpression':
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq=True)
            return
        
        # ConditionalPredicate: 条件部分，同样是 RHS
        if kind == 'ConditionalPredicate':
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq=True)
            return
        
        # ConditionalPattern: case 模式中的条件
        if kind == 'ConditionalPattern':
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq=True)
            return
        
        # 默认: 递归到子节点
        for child in self._iter_children(node):
            self._scan_expression(child, lhs_list, rhs_list, found_eq)
    
    def _on_node(self, node) -> pyslang.VisitAction:
        kind = self._get_kind(node)
        if not kind:
            return None
        
        if kind == 'ContinuousAssign':
            return self._process_continuous_assign(node)
        elif kind == 'SequentialBlockStatement':
            return self._process_sequential_block(node)
        elif kind == 'ConditionalStatement':
            return self._process_conditional_statement(node)
        elif kind == 'ExpressionStatement':
            return self._process_expression_statement(node)
        
        return None
    
    def _process_continuous_assign(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            child_kind = self._get_kind(child)
            if child_kind == 'SeparatedList':
                for sub in self._iter_children(child):
                    if self._get_kind(sub) == 'AssignmentExpression':
                        self._process_assign(sub, 'assign')
        return pyslang.VisitAction.Skip
    
    def _process_sequential_block(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            child_kind = self._get_kind(child)
            if child_kind == 'SyntaxList':
                for sub in self._iter_children(child):
                    sub_kind = self._get_kind(sub)
                    if sub_kind == 'ExpressionStatement':
                        self._process_expression_statement(sub)
                    elif sub_kind == 'ConditionalStatement':
                        self._process_conditional_statement(sub)
                    elif sub_kind == 'SequentialBlockStatement':
                        self._process_sequential_block(sub)
        return pyslang.VisitAction.Skip
    
    def _process_conditional_statement(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            child_kind = self._get_kind(child)
            if child_kind == 'ExpressionStatement':
                self._process_expression_statement(child)
            elif child_kind == 'ConditionalStatement':
                self._process_conditional_statement(child)
            elif child_kind == 'SequentialBlockStatement':
                self._process_sequential_block(child)
            elif child_kind == 'ElseClause':
                for sub in self._iter_children(child):
                    sub_kind = self._get_kind(sub)
                    if sub_kind == 'ExpressionStatement':
                        self._process_expression_statement(sub)
                    elif sub_kind == 'ConditionalStatement':
                        self._process_conditional_statement(sub)
        return pyslang.VisitAction.Skip
    
    def _process_expression_statement(self, node) -> pyslang.VisitAction:
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind in ('NonblockingAssignmentExpression', 'AssignmentExpression'):
                ctx = 'always_ff' if kind == 'NonblockingAssignmentExpression' else 'always_comb'
                self._process_assign(child, ctx)
        return pyslang.VisitAction.Skip
    
    def _process_assign(self, node, context: str):
        line = 0
        if hasattr(node, 'span'):
            line = node.span.start_line
        
        lhs_list = []
        rhs_list = []
        children = self._iter_children(node)
        found_eq = False
        
        for child in children:
            kind = self._get_kind(child)
            
            if kind in self._SKIP_KINDS:
                continue
            
            if kind in self._ASSIGN_OPS:
                found_eq = True
                continue
            
            if kind in ('Identifier', 'IdentifierName'):
                sig = _extract_identifier(child)
                if sig:
                    if not found_eq:
                        lhs_list.append(sig)
                    else:
                        rhs_list.append(sig)
                continue
            
            self._scan_expression(child, lhs_list, rhs_list, found_eq)
        
        for lhs in lhs_list:
            self._load_signals.add(lhs)
            for rhs in rhs_list:
                if rhs and rhs not in lhs_list:
                    self._add_load(lhs, rhs, context, line)
                    self._load_signals.add(rhs)
        
        for rhs in rhs_list:
            self._load_signals.add(rhs)
            for lhs in lhs_list:
                if lhs:
                    self._add_load(rhs, lhs, context, line)
                    self._load_signals.add(lhs)
    
    def _add_load(self, target: str, source: str, context: str, line: int):
        if not target or not source:
            return
        for lp in self._loads:
            if lp.signal == target and lp.load_by == source and lp.context == context:
                return
        self._loads.append(LoadPoint(
            signal=target, load_by=source, context=context, line=line
        ))


class LoadTracer:
    def __init__(self, trees: dict = None, verbose: bool = True, use_semantic: bool = True):
        self.trees = trees or {}
        self.verbose = verbose
        self.use_semantic = use_semantic  # 预留，供 semantic 层扩展
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="LoadTracer")
        self.loads: Dict[str, List[LoadPoint]] = {}
        self._load_signals: Set[str] = set()
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'LoadTracer':
        extractor = LoadExtractor(verbose=self.verbose)
        extractor.extract(tree.root)
        for lp in extractor.loads:
            if lp.signal not in self.loads:
                self.loads[lp.signal] = []
            self.loads[lp.signal].append(lp)
        self._load_signals = extractor.load_signals
        return self
    
    def find_load(self, signal: str) -> List[LoadPoint]:
        return self.loads.get(signal, [])
    
    @property
    def all_signals(self) -> List[str]:
        return sorted(list(self._load_signals))
    
    def trace(self, signal: str) -> List[LoadPoint]:
        return self.find_load(signal)


def trace_load(parser=None, verbose: bool = True) -> LoadTracer:
    tracer = LoadTracer(verbose=verbose)
    if parser:
        for filename, tree in (parser.trees.items() if hasattr(parser, 'trees') else []):
            tracer.trees[filename] = tree
    return tracer
