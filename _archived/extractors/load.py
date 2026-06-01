"""LoadExtractor - 负载关系提取器

迁移自 trace/load.py,使用 ScopeTree。
"""

import pyslang
from typing import List, Set

from extractors.base import Extractor, SemanticGraph, LoadPoint
from scope.models import ScopeTree, RefContext
from scope.symbol_table import SymbolTable

# 公共工具函数
try:
    from scope.utils import extract_identifier as _extract_identifier
except ImportError:
    def _extract_identifier(node):
        if hasattr(node, 'text') and node.text:
            return node.text
        return ""


class LoadExtractor(Extractor):
    """负载提取器

    符合铁律 18: 使用 pyslang.visit() 遍历
    符合铁律 19: 通过 ScopeTree 解析引用
    铁律3: 不可信则不输出 - 遇到不支持的语法时记录并警告
    """

    # 显式支持的语法类型 (铁律3: 明确声明)
    SUPPORTED_KINDS: Set[str] = {
        'ContinuousAssign',
        'SequentialBlockStatement',
        'ConditionalStatement',
        'ExpressionStatement',
        'AlwaysCombBlock', 'AlwaysFFBlock',
        'CaseStatement',
        'NonblockingAssignmentExpression',
        'AssignmentExpression',
        'ConditionalExpression',
        'ConditionalPredicate',
        'Identifier', 'IdentifierName',
    }

    # 已知但不相关的语法类型 (铁律3: 明确忽略)
    KNOWN_BUT_IGNORED: Set[str] = {
        'TokenList', 'SyntaxList', 'SeparatedList',
        'Plus', 'Minus', 'Multiply', 'Divide', 'Modulo',
        'OpenParenthesis', 'CloseParenthesis',
        'OpenBracket', 'CloseBracket',
        'IntegerLiteral', 'IntegerBase', 'VariableDimension',
        'RangeDimensionSpecifier', 'SimpleRangeSelect',
        'TimeUnit', 'DoublePeriod',
        'AssignKeyword', 'Question', 'Colon', 'At',
        'And', 'Or', 'Xor', 'Not', 'Tilde',
        'Ampersand', 'Bar', 'Caret',
        'Declarator', 'DataDeclaration', 'LogicType', 'LogicKeyword',
        'ModuleDeclaration', 'ModuleHeader', 'ModuleKeyword',
        'EndModuleKeyword', 'Semicolon', 'Comma',
        'IfKeyword', 'ElseKeyword', 'ElseClause',
        'BeginKeyword', 'EndKeyword',
        'ConditionalPattern', 'ConditionalPredicate',
        'IntegerLiteralExpression', 'IntegerVectorExpression',
        'LessThanEquals', 'Equals', 'AlwaysFFKeyword',
        'TimingControlStatement', 'EventControlWithExpression',
        'ParenthesizedEventExpression', 'SignalEventExpression',
        'PosEdgeKeyword', 'NegEdgeKeyword',
        'LessThanExpression', 'LessThan', 'GreaterThan', 'GreaterThanEquals',
        'EqualityExpression', 'NotEquals', 'CaseEqualityExpression', 'CaseInequalityExpression',
        'LogicalAndExpression', 'LogicalOrExpression', 'LogicalNotExpression',
        'BinaryAndExpression', 'BinaryOrExpression', 'BinaryXorExpression',
        'ShiftLeftExpression', 'ShiftRightExpression',
        'AddExpression', 'SubtractExpression',
        'MultiplyExpression', 'DivideExpression', 'ModuloExpression',
        'UnaryPlusExpression', 'UnaryMinusExpression', 'UnaryNotExpression', 'UnaryTildeExpression',
        'ConcatenationExpression',
        'GenvarDeclaration', 'GenVarKeyword',
        'GenerateRegion', 'GenerateKeyword',
        'LoopGenerate', 'ForKeyword',
        'GenerateBlock', 'NamedBlockClause',
        'PortDeclaration', 'ParameterDeclaration',
        'FunctionDeclaration', 'TaskDeclaration',
        'ClassDeclaration', 'InterfaceDeclaration',
        'PackageDeclaration', 'ProgramDeclaration',
        'CompilationUnit',
    }

    # 赋值操作符
    _ASSIGN_OPS: Set[str] = {
        'Equals', 'LessThanEquals',
        'PlusEquals', 'MinusEquals', 'MultiplyEquals', 'DivideEquals', 'ModuloEquals',
        'AndEquals', 'OrEquals', 'XorEquals',
        'LeftShiftEquals', 'RightShiftEquals',
    }

    # 跳过节点 (保持向后兼容)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unsupported_encountered: Set[str] = set()

    def extract(self, tree: pyslang.SyntaxTree) -> None:
        """从 AST 提取负载关系"""
        def visitor(node):
            self._on_node(node)
            return pyslang.VisitAction.Advance

        tree.root.visit(visitor)

    def _on_node(self, node) -> pyslang.VisitAction:
        """处理每个节点"""
        kind = self._get_kind(node)
        if not kind:
            return None

        kind_name = kind.name if hasattr(kind, 'name') else str(kind)

        # 铁律3: 未知语法类型 - 记录警告(只警告一次)
        if kind_name not in self.SUPPORTED_KINDS and kind_name not in self.KNOWN_BUT_IGNORED:
            if kind_name not in self._unsupported_encountered:
                if hasattr(self, 'warn_handler') and self.warn_handler:
                    self.warn_handler.warn_unsupported(
                        kind_name,
                        context='LoadExtractor',
                        suggestion='负载提取可能不完整',
                        component='LoadExtractor'
                    )
                self._unsupported_encountered.add(kind_name)

        if kind == 'ContinuousAssign':
            return self._process_continuous_assign(node)
        elif kind == 'SequentialBlockStatement':
            return self._process_sequential_block(node)
        elif kind == 'ConditionalStatement':
            return self._process_conditional_statement(node)
        elif kind == 'ExpressionStatement':
            return self._process_expression_statement(node)
        elif kind == 'AlwaysCombBlock':
            return self._process_always_comb_block(node)
        elif kind == 'CaseStatement':
            return self._process_case_statement(node)
        elif kind == 'AlwaysFFBlock':
            return self._process_sequential_block(node)

        return None

    def _process_always_comb_block(self, node) -> pyslang.VisitAction:
        """处理 always_comb 块"""
        # 直接遍历子节点查找语句
        for child in self._iter_children(node):
            sk = self._get_kind(child)
            if sk == 'CaseStatement':
                self._process_case_statement(child)
            elif sk == 'ExpressionStatement':
                self._process_expression_statement(child)
            elif sk == 'ConditionalStatement':
                self._process_conditional_statement(child)
            elif sk == 'SequentialBlockStatement':
                self._process_sequential_block(child)
        return pyslang.VisitAction.Skip

    def _process_case_statement(self, node) -> pyslang.VisitAction:
        """处理 case 语句 - 提取 case 条件中的信号"""
        # case (sel) - 条件是 OpenParenthesis 后的 IdentifierName
        for child in self._iter_children(node):
            if self._get_kind(child) == 'IdentifierName':
                # 找到 case 条件
                from scope.utils import extract_identifier as _extract_identifier
                sig = _extract_identifier(child)
                if sig:
                    self.graph.add_load(sig, sig, 'case_condition', 0)
                break
        # 处理 case 内部的语句
        for child in self._iter_children(node):
            sk = self._get_kind(child)
            if sk == 'ExpressionStatement':
                self._process_expression_statement(child)
            elif sk == 'SequentialBlockStatement':
                self._process_sequential_block(child)
            elif sk == 'StandardCaseItem':
                # 处理 case item
                for sub in self._iter_children(child):
                    ssk = self._get_kind(sub)
                    if ssk == 'ExpressionStatement':
                        self._process_expression_statement(sub)
        return pyslang.VisitAction.Skip

    def _process_continuous_assign(self, node) -> pyslang.VisitAction:
        """处理连续赋值 assign x = y"""
        for child in self._iter_children(node):
            if self._get_kind(child) == 'SeparatedList':
                for sub in self._iter_children(child):
                    if self._get_kind(sub) == 'AssignmentExpression':
                        self._process_assign(sub, 'assign')
        return pyslang.VisitAction.Skip

    def _process_sequential_block(self, node) -> pyslang.VisitAction:
        """处理 begin...end 块"""
        for child in self._iter_children(node):
            if self._get_kind(child) == 'SyntaxList':
                for sub in self._iter_children(child):
                    sk = self._get_kind(sub)
                    if sk == 'ExpressionStatement':
                        self._process_expression_statement(sub)
                    elif sk == 'ConditionalStatement':
                        self._process_conditional_statement(sub)
                    elif sk == 'SequentialBlockStatement':
                        self._process_sequential_block(sub)
        return pyslang.VisitAction.Skip

    def _process_conditional_statement(self, node) -> pyslang.VisitAction:
        """处理 if/else"""
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
                    elif ssk == 'ConditionalStatement':
                        self._process_conditional_statement(sub)
            elif sk == 'ConditionalPredicate':
                # 扫描 if 条件中的信号 (被读取的负载)
                # 条件表达式中的信号都是被读取的
                condition_signals = []
                self._scan_expression(child, [], condition_signals, found_eq=True)
                # 条件中的信号作为负载添加到图中
                for sig in condition_signals:
                    self.graph.add_load(sig, sig, 'condition', 0)
        return pyslang.VisitAction.Skip

    def _process_expression_statement(self, node) -> pyslang.VisitAction:
        """处理表达式语句"""
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind in ('NonblockingAssignmentExpression', 'AssignmentExpression'):
                ctx = 'always_ff' if kind == 'NonblockingAssignmentExpression' else 'always_comb'
                self._process_assign(child, ctx)
        return pyslang.VisitAction.Skip

    def _process_assign(self, node, context: str):
        """处理赋值语句"""
        line = getattr(node, 'span', None) and node.span.start_line or 0

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

        # NOTE: Load 表示 LHS ← RHS (LHS 被 RHS 加载)
        # 不存在反向添加，否则会污染负载关系
        for lhs in lhs_list:
            for rhs in rhs_list:
                if rhs and rhs not in lhs_list:
                    self.graph.add_load(lhs, rhs, context, line)

        # Handle case where RHS is empty (e.g., arr[idx] = literal)
        # All LHS signals are still being loaded
        if not rhs_list and lhs_list:
            for lhs in lhs_list:
                self.graph.add_load(lhs, '', context, line)

    def _scan_expression(self, node, lhs_list: list, rhs_list: list, found_eq: bool):
        """递归扫描表达式"""
        if not hasattr(node, 'kind'):
            return

        kind = self._get_kind(node)
        if not kind or kind in self._SKIP_KINDS:
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

        if kind in ('ElementSelect', 'BitSelect', 'IdentifierSelectName', 'SyntaxList', 'SeparatedList'):
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq)
            return

        if kind == 'ConditionalExpression':
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq=True)
            return

        if kind == 'ConditionalPredicate':
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq=True)
            return

        if kind == 'ConditionalPattern':
            for child in self._iter_children(node):
                self._scan_expression(child, lhs_list, rhs_list, found_eq=True)
            return

        for child in self._iter_children(node):
            self._scan_expression(child, lhs_list, rhs_list, found_eq)
