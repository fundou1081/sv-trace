"""signal_tracer.tracer - 信号追踪核心实现

给一个信号，返回它的所有驱动和负载，包含文件位置和 scope 源码。
"""

import pyslang
from pyslang import SyntaxKind, TokenKind
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

from signal_tracer.models import (
    TraceResult, TraceType, ScopeKind, DriverTrace, LoadTrace,
    ScopeInfo, SignalInfo, TraceSummary,
    SyntaxNodeSnapshot,  # M5.1h: 冻结 syntax node 文本, 防 pyslang buffer 复用
    _set_source_manager,  # M5.1h fix: 同步 SourceManager 给 build_evidence_via_syntax
)
from signal_tracer.port_resolver import PortResolver, PortConnection


def _strip_evidence(trace_result) -> dict:
    """从 TraceResult 提取 dict, 过滤掉内部 _evidence_override 字段

    DriverTrace(**d.__dict__) 会因 _evidence_override 而崩溃 (DriverTrace 没这个字段)。
    此函数提取安全字段给 DriverTrace/LoadTrace 构造用, 保留 _evidence_override 在
    原对象上 (供 to_context() 用)。
    """
    return {k: v for k, v in trace_result.__dict__.items() if k != '_evidence_override'}


def _get_line_from_offset(text: str, offset: int) -> int:
    """从字符偏移计算行号 (1-indexed)"""
    if offset <= 0:
        return 1
    return text[:offset].count('\n') + 1


def _extract_identifiers(node) -> List[str]:
    """从表达式节点递归提取所有标识符 (去重)"""
    result = []
    _collect_ids(node, result)
    return list(set(result))  # 去重


def _collect_ids(node, result: List[str], _visited: set = None):
    """递归收集标识符 (带去重)"""
    if node is None:
        return
    
    # 避免重复处理
    node_id = id(node)
    if _visited and node_id in _visited:
        return
    if _visited is None:
        _visited = set()
    _visited.add(node_id)
    
    kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
    
    # IdentifierName: 直接的标识符引用
    if kn == 'IdentifierName':
        ident = getattr(node, 'identifier', None)
        if ident:
            val = getattr(ident, 'valueText', '') or getattr(ident, 'text', '') or ''
            if val:
                result.append(val)
    
    # IdentifierSelectName: 带选择器的标识符如 req[7], mod.signal
    elif kn == 'IdentifierSelectName':
        ident = getattr(node, 'identifier', None)
        if ident:
            val = getattr(ident, 'valueText', '') or getattr(ident, 'text', '') or ''
            if val:
                result.append(val)
    
    # Identifier: 单独的标识符
    elif kn == 'Identifier':
        val = getattr(node, 'valueText', '') or getattr(node, 'text', '') or ''
        if val:
            result.append(val)
    
    # ConditionalPredicate 的内容在 SeparatedList 中
    elif kn == 'SeparatedList':
        for child in node:
            _collect_ids(child, result, _visited)
        return
    
    # ConditionalPattern: 包含实际的条件表达式如 req[7]
    elif kn == 'ConditionalPattern':
        for child in node:
            _collect_ids(child, result, _visited)
        return
    
    # ConditionalPredicate: 条件在 conditions 属性中
    elif kn == 'ConditionalPredicate':
        conditions = getattr(node, 'conditions', None)
        if conditions is not None:
            _collect_ids(conditions, result, _visited)
        return
    
    # IntegerVectorExpression: 数值字面量如 8'hFF, 3'd7
    elif kn == 'IntegerVectorExpression':
        value = getattr(node, 'value', None)
        if value and hasattr(value, 'valueText'):
            result.append(getattr(value, 'valueText', '') or '')
    
    # IntegerLiteralExpression: 纯数字如 42
    elif kn == 'IntegerLiteralExpression':
        literal = getattr(node, 'literal', None)
        if literal and hasattr(literal, 'valueText'):
            result.append(getattr(literal, 'valueText', '') or '')
    
    # Binary expressions (AddExpression, etc.) - 只通过 left/right 属性递归
    # 不遍历 children，因为 children 会重复包含 left/right
    elif kn.endswith('Expression') and kn not in ('IntegerLiteralExpression', 'IntegerVectorExpression'):
        pass  # 只通过下面的 left/right 处理
    
    # 递归处理子属性 (for other node types)
    for prop in ['expression', 'left', 'right']:
        sub = getattr(node, prop, None)
        if sub is not None:
            _collect_ids(sub, result, _visited)


def _get_lhs_name(node) -> str:
    """从赋值表达式获取左值名称"""
    if node is None:
        return ""
    
    kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
    
    if kn == 'IdentifierName':
        ident = getattr(node, 'identifier', None)
        if ident:
            return getattr(ident, 'valueText', '') or ''
    
    if kn == 'IdentifierSelectName':
        # Handle array/select access like data_out[i]
        ident = getattr(node, 'identifier', None)
        if ident:
            name = getattr(ident, 'valueText', '') or ''
            # Include selectors if present
            selectors = getattr(node, 'selectors', None)
            if selectors and len(list(selectors)) > 0:
                # Build selector string
                parts = [name]
                for sel in selectors:
                    sel_kn = sel.kind.name if hasattr(sel.kind, 'name') else str(sel.kind)
                    if sel_kn == 'ElementSelect':
                        # Get the index expression from BitSelect inside
                        for idx_child in sel:
                            idx_kn = idx_child.kind.name if hasattr(idx_child.kind, 'name') else str(idx_child.kind)
                            if idx_kn == 'BitSelect':
                                # Look inside BitSelect for the actual index
                                for bit_child in idx_child:
                                    bit_kn = bit_child.kind.name if hasattr(bit_child.kind, 'name') else str(bit_child.kind)
                                    if bit_kn == 'IdentifierName':
                                        idx_ident = getattr(bit_child, 'identifier', None)
                                        if idx_ident:
                                            idx_val = getattr(idx_ident, 'valueText', '') or ''
                                            parts.append(f'[{idx_val}]')
                                    elif bit_kn in ('IntegerLiteralExpression', 'IntegerVectorExpression'):
                                        literal = getattr(bit_child, 'literal', None) or getattr(bit_child, 'value', None)
                                        if literal:
                                            val = getattr(literal, 'valueText', '') or getattr(literal, 'text', '') or ''
                                            parts.append(f'[{val}]')
                return ''.join(parts)
            return name
    
    if kn == 'VariableSelect':
        base = getattr(node, 'variable', None)
        if base:
            return _get_lhs_name(base)
    
    return ""


def _get_source_range(node) -> Tuple[int, int]:
    """获取节点的 sourceRange (start_offset, end_offset)"""
    if not hasattr(node, 'sourceRange') or not node.sourceRange:
        return (0, 0)
    sr = node.sourceRange
    return (sr.start.offset, sr.end.offset)


def _get_text_from_range(sv_code: str, start: int, end: int) -> str:
    """从 sv_code 提取指定范围的文本"""
    if start <= 0:
        start = 0
    if end > len(sv_code):
        end = len(sv_code)
    if start >= end:
        return ""
    return sv_code[start:end]


def _reconstruct_node_text(node) -> str:
    """从节点属性重建文本（当 sourceRange 不正确时使用）"""
    kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
    
    # IntegerVectorExpression: 如 8'hFF, 3'd7
    if kn == 'IntegerVectorExpression':
        parts = []
        size = getattr(node, 'size', None)
        base = getattr(node, 'base', None)
        value = getattr(node, 'value', None)
        if size and hasattr(size, 'text'):
            parts.append(size.text)
        if base and hasattr(base, 'text'):
            parts.append(base.text)
        if value and hasattr(value, 'valueText'):
            parts.append(getattr(value, 'valueText', '') or '')
        return ''.join(parts)
    
    # IntegerLiteralExpression
    if kn == 'IntegerLiteralExpression':
        literal = getattr(node, 'literal', None)
        if literal:
            return getattr(literal, 'valueText', '') or getattr(literal, 'text', '') or ''
    
    return ""


def _dump_chain(
    chain: List['TraceResult'],
    signal_name: str,
    direction: str,
    include_context_window: bool = True,
    include_scope_text: bool = False,
    summary_only: bool = False,
) -> Dict:
    """M5.1f: 核心函数, 把 chain list dump 成 dict (含 summary)

    Args:
        chain: List[TraceResult] (来自 get_driver_chain / get_load_chain)
        signal_name: 查询的信号
        direction: 'upstream' / 'downstream'
        include_context_window: 是否含 context before/after
        include_scope_text: 是否含完整 scope_text
        summary_only: 只返回 summary 不要 hops

    Returns:
        Dict 含 4 个顶层字段: signal_name / direction / hops / summary

    summary 字段:
        - total_hops: 链长
        - verified_count: is_verified=True 的 hop 数
        - high_credibility_count: credibility >= 0.8 的 hop 数
        - low_credibility_count: credibility < 0.6 的 hop 数 (告警指标)
        - avg_credibility: 平均可信度
        - min_credibility: 最低可信度
        - cross_files: 跨文件列表
    """
    if not chain:
        return {
            'signal_name': signal_name,
            'direction': direction,
            'hops': [],
            'summary': {
                'total_hops': 0,
                'verified_count': 0,
                'high_credibility_count': 0,
                'low_credibility_count': 0,
                'avg_credibility': 0.0,
                'min_credibility': 0.0,
                'cross_files': [],
            },
        }

    hops = []
    credibilities = []
    cross_files = set()
    verified_count = 0
    high_cred_count = 0
    low_cred_count = 0

    for d in chain:
        ctx = d.to_context()
        ce = ctx.code_evidence
        try:
            cred = round(ce.credibility_score, 2)
        except Exception:
            cred = 0.0
        credibilities.append(cred)
        is_verified = bool(ce.is_verified) if ce else False
        if is_verified:
            verified_count += 1
        if cred >= 0.8:
            high_cred_count += 1
        if cred < 0.6:
            low_cred_count += 1
        if d.file:
            cross_files.add(d.file.split('/')[-1])

        hop = {
            'hop': len(hops) + 1,
            'signal_name': d.signal_name,
            'file': d.file.split('/')[-1] if d.file else '',
            'line': d.line,
            'hierarchical_path': d.hierarchical_path,
            'source_expr': d.source_expr,
            'source_signals': list(d.source_signals) if d.source_signals else [],
            'scope_kind': str(d.scope_kind) if d.scope_kind else '',
            'credibility': cred,
            'is_verified': is_verified,
            'matches_source_expr': ce.matches_source_expr if ce else False,
            'matches_signal_name': ce.matches_signal_name if ce else False,
            'snippet': ce.snippet if ce else '',
        }
        if include_scope_text:
            hop['scope_text'] = d.scope_text or ''
        if include_context_window and ce:
            hop['context_window'] = {
                'before': list(ce.context_before),
                'after': list(ce.context_after),
            }
        hops.append(hop)

    summary = {
        'total_hops': len(hops),
        'verified_count': verified_count,
        'high_credibility_count': high_cred_count,
        'low_credibility_count': low_cred_count,
        'avg_credibility': round(sum(credibilities) / len(credibilities), 2),
        'min_credibility': min(credibilities),
        'cross_files': sorted(cross_files),
    }

    result = {'signal_name': signal_name, 'direction': direction}
    if summary_only:
        result['summary'] = summary
    else:
        result['hops'] = hops
        result['summary'] = summary
    return result


class SignalTracer:
    """信号追踪器
    
    给一个信号，返回它的所有驱动和负载。
    """
    
    def __init__(self, sv_code: str = "", file_path: str = ""):
        # M3: 支持多文件. _files 是 [(file_path, sv_code), ...]
        # 向后兼容: 如果传了 sv_code, 仍可直接工作
        self._files: List[Tuple[str, str]] = []
        self._sv_code = sv_code  # 保留作向后兼容 (单文件时 = _files[0][1])
        self._file_path = file_path
        self._tree: pyslang.SyntaxTree = None
        self._drivers: Dict[str, List[TraceResult]] = {}
        self._loads: Dict[str, List[TraceResult]] = {}
        self._scopes: List[ScopeInfo] = []
        self._port_info: Dict[str, str] = {}  # hpath -> direction ('in', 'out', 'inout')
        self._port_resolver: PortResolver = None  # 端口连接解析器
        self._source_manager = None  # M4: pyslang SourceManager (跨文件精确行号)
        self._built = False
        if sv_code or file_path:
            self.add_file(file_path, sv_code)

    def add_file(self, file_path: str, sv_code: str) -> 'SignalTracer':
        """M3: 加一个 .sv 文件到追踪项目

        多个文件会被加到同一 pyslang Compilation, 可以跨文件追踪 (top.u_sub.signal)。

        可以连续调用多次:
            t = SignalTracer()
            t.add_file('top.sv', top_code)
            t.add_file('sub.sv', sub_code)
            t.build()
            t.trace('top.u_sub.out_data')

        Returns:
            self, 支持链式调用
        """
        if not sv_code:
            return self
        self._files.append((file_path, sv_code))
        # 保持 _sv_code 指向第一个文件 (向后兼容)
        if not self._sv_code:
            self._sv_code = sv_code
            self._file_path = file_path
        return self

    def build(self):
        """构建追踪索引"""
        if self._built:
            return self

        self._scopes = []
        self._drivers = {}
        self._loads = {}

        if not self._files:
            # 没有文件, build 出空
            self._built = True
            return self

        # M3: 多棵 SyntaxTree 加到同一 Compilation (跨文件 module 解析)
        comp = pyslang.Compilation()
        for file_path, sv_code in self._files:
            tree = pyslang.SyntaxTree.fromText(sv_code, file_path or '')
            comp.addSyntaxTree(tree)
        comp.freeze()

        # M4: 保存 SourceManager, 后续所有行号计算都走它 (跨文件精确)
        self._source_manager = comp.sourceManager
        # M5.1h fix: 同步给 models 里的 singleton, build_evidence_via_syntax 拿得到
        _set_source_manager(self._source_manager)

        # Get elaborated root and traverse all semantic symbols
        root = comp.getRoot()

        # Collect port information first
        self._collect_port_info(root)

        # Use visit() to traverse the semantic AST - visit() handles internal traversal
        # and crosses module boundaries (top.u_sub.signal 都能拿到)
        root.visit(lambda s: self._process_all_symbols(s))

        # Build port connection resolver for cross-module tracing
        # PortResolver 当前是单文件, 喂第一个文件 (主要使用场景是单文件或顶层)
        if self._sv_code:
            self._port_resolver = PortResolver(self._sv_code)
            self._port_resolver.build()

        self._built = True
        return self
    
    def _collect_port_info(self, root):
        """收集所有端口信息"""
        self._port_info = {}
        
        def visit_sym(sym):
            if 'PortSymbol' in type(sym).__name__:
                hpath = getattr(sym, 'hierarchicalPath', '')
                direction = getattr(sym, 'direction', None)
                if direction:
                    dir_name = str(direction).split('.')[-1].lower()
                    self._port_info[hpath] = dir_name
        
        root.visit(visit_sym)
    
    def _process_all_symbols(self, symbol):
        """Process all semantic symbols - procedural blocks and continuous assigns"""
        kind = type(symbol).__name__
        
        # Process procedural blocks
        if 'ProceduralBlock' in kind:
            self._process_procedural_block(symbol)
        
        # Process continuous assigns
        elif 'ContinuousAssign' in kind:
            self._process_continuous_assign(symbol)
    
    def _process_continuous_assign(self, sym):
        """Process a ContinuousAssignSymbol from semantic AST"""
        # Get the assignment expression
        assign_expr = getattr(sym, 'assignment', None)
        if assign_expr is None:
            return

        # M4 防御: pyslang 可能返回 InvalidExpression (例如 reg block 类型不在编译单元中)
        # 这种情况 fallback 到语法层解析, 不让整个 build 崩
        expr_type = type(assign_expr).__name__
        if expr_type == 'InvalidExpression':
            # Fallback: 从 syntax 恢复 lhs/rhs
            syn = getattr(sym, 'syntax', None)
            if syn:
                self._process_syntax_for_assignment(syn, None)
            return

        # Get left (target) and right (source) from semantic expressions
        lhs_name = self._get_lhs_name_semantic(assign_expr.left)
        rhs_info = self._get_rhs_info_semantic(assign_expr.right)
        
        if not lhs_name:
            return
        
        # Get location info (M4: 跨文件精确, 走 SourceManager)
        loc = getattr(sym, 'location', None)
        if loc is not None:
            line = self._offset_to_line(loc)
            if line == 0:
                line = 1
        else:
            line = 1

        # Get syntax and line info (M2: 多行保留, 精确 line_end)
        syn = getattr(sym, 'syntax', None)
        syn_text = ''
        line_end = line
        if syn and hasattr(syn, 'sourceRange') and syn.sourceRange:
            sr = syn.sourceRange
            syn_text = str(syn).strip()
            end_offset = sr.end.offset
            if end_offset > 0 and end_offset <= len(self._sv_code):
                line_end = self._sv_code[:end_offset].count('\n') + 1
        elif syn:
            syn_text = str(syn).strip()

        # Create scope info for continuous assign
        # M3: continuous assign 的 hpath 就是其所在 module 的 hpath (如 'top' 或 'top.u_sub')
        assign_hpath = getattr(sym, 'hierarchicalPath', '') or ''
        # M4: 从 SourceLocation 取实际文件名 (代替 self._file_path)
        assign_file = self._get_file_from_location(sym.location)
        scope = ScopeInfo(
            kind=ScopeKind.CONTINUOUS_ASSIGN,
            name=assign_hpath or 'assign',
            instance_path=assign_hpath,
            line_start=line,
            line_end=line_end,
            text=syn_text,
            offset_start=0,
            offset_end=0,
            clock='',
            reset='',
            file_path=assign_file,
        )
        self._scopes.append(scope)

        # M3: 用 scope.instance_path (hpath) 作为前缀
        full_name = self._qualify_signal_name(scope, lhs_name)

        # Create driver trace
        trace = TraceResult(
            trace_type=TraceType.DRIVER,
            signal_name=lhs_name,
            source_expr=rhs_info['text'],
            source_signals=rhs_info['signals'],
            file=scope.file_path,
            line=line,
            char_offset=0,
            scope_kind=ScopeKind.CONTINUOUS_ASSIGN,
            scope_line_start=line,
            scope_line_end=line_end,
            scope_text=syn_text,
            scope_offset_start=0,
            scope_offset_end=0,
            clock='',
            reset='',
            hierarchical_path=assign_hpath,
        )
        # M5.1h: 注入 syntax node (continuous assign 也需要)
        # assign_expr.syntax = AssignmentExpressionSyntax, str() 返回完整 'c = a & b'
        # M5.1h: 用 SyntaxNodeSnapshot 冻结 str(), 防 pyslang buffer 复用后被截断
        trace._syntax_node = SyntaxNodeSnapshot(
            getattr(assign_expr, 'syntax', None) or getattr(sym, 'syntax', None)
        )
        if full_name not in self._drivers:
            self._drivers[full_name] = []
        self._drivers[full_name].append(trace)
        if lhs_name not in self._drivers:
            self._drivers[lhs_name] = []
        self._drivers[lhs_name].append(trace)

        # Create load traces for signals used in RHS
        for sig in rhs_info['signals']:
            if sig != lhs_name:
                full_sig = self._qualify_signal_name(scope, sig)
                if full_sig not in self._loads:
                    self._loads[full_sig] = []
                if sig not in self._loads:
                    self._loads[sig] = []
                load_trace = TraceResult(
                    trace_type=TraceType.LOAD,
                    signal_name=sig,
                    source_expr=lhs_name,
                    source_signals=[lhs_name],
                    file=scope.file_path,
                    line=line,
                    char_offset=0,
                    scope_kind=ScopeKind.CONTINUOUS_ASSIGN,
                    scope_line_start=line,
                    scope_line_end=line,
                    scope_text=syn_text,
                    scope_offset_start=0,
                    scope_offset_end=0,
                    clock='',
                    reset='',
                    hierarchical_path=assign_hpath,
                )
                # M5.1h: load 也注入 syntax node (RHS 表达式)
                # M5.1h: 用 SyntaxNodeSnapshot 冻结 str()
                load_trace._syntax_node = SyntaxNodeSnapshot(
                    getattr(assign_expr.right, 'syntax', None) or getattr(sym, 'syntax', None)
                )
                self._loads[full_sig].append(load_trace)
                self._loads[sig].append(load_trace)
    
    def _process_procedural_block(self, block):
        """Process a single ProceduralBlockSymbol from semantic AST"""
        # Get hierarchical path
        hpath = getattr(block, 'hierarchicalPath', None)
        block_name = str(hpath) if hpath else 'unknown'

        # Get procedure kind
        proc_kind = getattr(block, 'procedureKind', None)
        kind_name = str(proc_kind).split('.')[-1] if proc_kind else 'Unknown'

        # Map to ScopeKind
        if 'AlwaysFF' in kind_name:
            scope_kind = ScopeKind.ALWAYS_FF
        elif 'AlwaysComb' in kind_name:
            scope_kind = ScopeKind.ALWAYS_COMB
        elif 'AlwaysLatch' in kind_name:
            scope_kind = ScopeKind.ALWAYS_LATCH
        else:
            scope_kind = ScopeKind.ALWAYS_FF

        # Get location info (M4: 跨文件精确, 走 SourceManager)
        loc = getattr(block, 'location', None)
        if loc is not None:
            line_start = self._offset_to_line(loc)
            if line_start == 0:
                line_start = 1
        else:
            line_start = 1

        # Get syntax and line info (M2: 多行保留, 精确 end line)
        syn = getattr(block, 'syntax', None)
        syn_text = ''
        line_end = line_start
        if syn and hasattr(syn, 'sourceRange') and syn.sourceRange:
            sr = syn.sourceRange
            # 保留多行 (不 replace('\n', ' '))
            syn_text = str(syn)
            # 去首尾空白
            syn_text = syn_text.strip()
            # 计算 end line
            end_offset = sr.end.offset
            if end_offset > 0 and end_offset <= len(self._sv_code):
                line_end = self._sv_code[:end_offset].count('\n') + 1
        elif syn:
            syn_text = str(syn).strip()

        # 提取 clock / reset (仅 always_ff 才有, always_comb/latch 没有 timing control)
        clock_name, reset_name = self._extract_clock_reset(block)

        # Create scope info
        # M4: 从 block.location 取实际文件
        block_file = self._get_file_from_location(block.location)
        scope = ScopeInfo(
            kind=scope_kind,
            name=block_name,
            instance_path=block_name,
            line_start=line_start,
            line_end=line_end,
            text=syn_text,
            offset_start=0,
            offset_end=0,
            clock=clock_name,
            reset=reset_name,
            file_path=block_file,
        )
        self._scopes.append(scope)

        # Process assignments inside the procedural block
        self._process_block_body(block, scope)

    def _extract_clock_reset(self, block) -> Tuple[str, str]:
        """从 always_ff/always_latch 的 timing 表达式提取 clock 和 reset 名称

        原理: pyslang 语义 AST 里, ProceduralBlock.body 是 TimedStatement,
        TimedStatement.timing 可能是:
        - SignalEventControl: 单事件 (always @(posedge clk))
        - EventListControl: 多事件 (always @(posedge clk or negedge rst_n))
        每个 SignalEventControl 有 .edge (PosEdge/NegEdge) 和 .expr (信号名)

        判定 clock vs reset (按优先级):
        1. 命名启发式: 含 'rst' / 'reset' / 'arst' / 'srst' / 'por' → reset
        2. edge 方向: negedge → reset 倾向; posedge → clock 倾向
        3. 多 posedge: 全是 clock (如 @(posedge clk1, posedge clk2))
        4. 启发式都失败: 归 clock

        Returns:
            (clock_name, reset_name) — 任一为空字符串表示未识别
        """
        clock = ''
        reset = ''

        body = getattr(block, 'body', None)
        if body is None or type(body).__name__ != 'TimedStatement':
            return clock, reset

        timing = getattr(body, 'timing', None)
        if timing is None:
            return clock, reset

        # 收集所有 events
        events = []
        if type(timing).__name__ == 'EventListControl':
            events = list(getattr(timing, 'events', []) or [])
        elif type(timing).__name__ == 'SignalEventControl':
            events = [timing]
        else:
            return clock, reset

        for ev in events:
            if type(ev).__name__ != 'SignalEventControl':
                continue

            # 提取信号名
            expr = getattr(ev, 'expr', None)
            sig_name = ''
            if expr is not None:
                sym = getattr(expr, 'symbol', None)
                if sym:
                    sig_name = getattr(sym, 'name', '') or ''
            if not sig_name:
                continue

            # 判定 clock vs reset
            is_reset = self._is_reset_signal(sig_name, ev)
            if is_reset:
                if not reset:
                    reset = sig_name
            else:
                if not clock:
                    clock = sig_name
                # else: 多 posedge 都被记为 clock, 但只保留第一个 (TODO M3 多 clock)

        return clock, reset

    def _is_reset_signal(self, sig_name: str, event) -> bool:
        """判断一个 event 信号是否是 reset

        优先级:
        1. 命名匹配 (强信号, 几乎必定 reset): rst/reset/arst/srst/por/clr/clear
        2. edge 是 negedge 且没匹配 reset 命名 → 倾向 reset
        3. 否则: 不算 reset
        """
        name_lower = sig_name.lower()
        # 命名启发式
        reset_keywords = ('rst', 'reset', 'arst', 'srst', 'por', 'clr', 'clear', 'rstn', 'rst_n')
        for kw in reset_keywords:
            if kw in name_lower:
                return True

        # 边缘启发式: negedge 倾向 reset
        edge = getattr(event, 'edge', None)
        if edge is not None and 'NegEdge' in str(edge):
            return True

        return False

    def _process_block_body(self, block, scope):
        """从语义化的 ProceduralBlockSymbol 提取赋值和条件

        只负责入口分发：拿到 block.body，调 _process_any 递归处理。
        所有 unwrapping / dispatch 逻辑都在 _process_any 里。
        """
        body = getattr(block, 'body', None)
        if body is None:
            return
        self._process_any(body, scope, condition_stack=[])

    def _process_any(self, node, scope, condition_stack):
        """递归处理任意语句节点

        处理的节点类型：
        - TimedStatement     → 解包 .stmt
        - BlockStatement     → 解包 .body (单语句 或 StatementList)
        - StatementList      → 迭代处理每个
        - ExpressionStatement→ 取 .expr 调用 _process_assignment_expr
        - ConditionalStatement→ 处理 condition (作为 load)，递归 ifTrue/ifFalse
        - CaseStatement      → 处理 expr (作为 load)，递归 items/defaultCase
        - CallStatement      → 任务调用，提取参数中的信号作为 load
        - EmptyStatement     → 啥也不做
        - InvalidStatement   → fallback 到语法树恢复

        condition_stack 记录当前嵌套的 if/case 条件，透传给所有生成的 trace。
        """
        if node is None:
            return

        node_type = type(node).__name__

        # ---- Wrapper nodes: 解包后递归 ----
        if node_type == 'TimedStatement':
            # always_ff / always_latch / initial 都会包一层 TimedStatement
            inner = getattr(node, 'stmt', None)
            if inner is not None:
                self._process_any(inner, scope, condition_stack)
            return

        if node_type == 'BlockStatement':
            # begin...end 块，body 可能是单语句 或 StatementList
            inner = getattr(node, 'body', None)
            if inner is None:
                return
            # 区分单语句和 StatementList
            if isinstance(inner, str) or not hasattr(inner, '__iter__'):
                # 单语句
                self._process_any(inner, scope, condition_stack)
            else:
                # 多语句列表（包括 StatementList 类型）
                for stmt in inner:
                    self._process_any(stmt, scope, condition_stack)
            return

        if node_type == 'StatementList':
            # pyslang 在 begin...end 多语句时返回这个类型
            # 它本身不可迭代，要用 .list 属性拿真正的 list
            stmt_list = getattr(node, 'list', None) or []
            for stmt in stmt_list:
                self._process_any(stmt, scope, condition_stack)
            return

        if node_type == 'EmptyStatement':
            # ;  (例如 case 里的 default 空分支)
            return

        if node_type == 'InvalidStatement':
            # 语义分析失败，fallback 到语法树恢复
            syntax = getattr(node, 'syntax', None)
            if syntax:
                self._process_syntax_for_assignment(syntax, scope)
            return

        # ---- Statement nodes: 实际处理 ----
        if node_type == 'ExpressionStatement':
            expr = getattr(node, 'expr', None)
            self._process_assignment_expr(expr, scope, condition_stack)
            return

        if node_type == 'ConditionalStatement':
            self._process_conditional_stmt(node, scope, condition_stack)
            return

        if node_type == 'CaseStatement':
            self._process_case_stmt(node, scope, condition_stack)
            return

        if node_type == 'CallStatement':
            # task 调用：参数表达式中的信号是 load
            self._process_call_stmt(node, scope, condition_stack)
            return

        if node_type == 'ForLoopStatement':
            # for 循环: pyslang 已提升 init/cond/iter，体内还可能有赋值
            loop_body = getattr(node, 'body', None)
            if loop_body:
                self._process_any(loop_body, scope, condition_stack)
            return

        if node_type in ('WhileLoopStatement', 'DoWhileStatement'):
            # while / do-while 循环同理
            loop_body = getattr(node, 'body', None)
            if loop_body:
                self._process_any(loop_body, scope, condition_stack)
            return

        # ---- 已知但不产生 trace 的节点 ----
        # 变量声明 (int i = 0;)、return/break/continue 等
        if node_type in ('VariableDeclStatement', 'VariableDecl', 'NetDeclStatement'):
            return
        if node_type in ('ReturnStatement', 'BreakStatement', 'ContinueStatement'):
            return
        # M4: 状态断言 (assert property) - SV断言, 不产生 driver/load trace
        # (assertion 内的信号在 SVA 内部使用, 不是赋值的 source)
        if node_type == 'ConcurrentAssertionStatement':
            return

        # ---- 真正未知的才打 WARNING ----
        import sys
        print(
            f"WARNING: Unknown node type in _process_any: {node_type} "
            f"(kind={getattr(node, 'kind', '?')})",
            file=sys.stderr,
        )

    
    def _process_syntax_for_assignment(self, syntax_node, scope):
        """从语法树节点恢复赋值信息 - 用于 InvalidStatement 恢复"""
        # Walk syntax to find assignment expression
        def find_assignment(node):
            if hasattr(node, 'kind'):
                kn = str(node.kind)
                if 'NonblockingAssignment' in kn or 'BlockingAssignment' in kn:
                    return node
            if hasattr(node, '__iter__'):
                try:
                    for child in node:
                        result = find_assignment(child)
                        if result:
                            return result
                except:
                    pass
            return None
        
        assign_node = find_assignment(syntax_node)
        if assign_node is None:
            return
        
        # Extract LHS and RHS from assignment
        children = list(assign_node) if hasattr(assign_node, '__iter__') else []
        if len(children) < 4:
            return
        
        lhs_node = children[0]
        rhs_node = children[3]
        
        # Get LHS name from syntax - use .identifier for IdentifierNameSyntax
        lhs_name = ''
        identifier = getattr(lhs_node, 'identifier', None)
        if identifier is not None:
            if isinstance(identifier, str):
                lhs_name = identifier
            elif hasattr(identifier, 'valueText'):
                lhs_name = getattr(identifier, 'valueText', '') or ''
        elif hasattr(lhs_node, 'name'):
            lhs_name = getattr(lhs_node, 'name', '') or ''
        
        if lhs_name:
            # Get RHS name for load tracking
            rhs_name = ''
            rhs_identifier = getattr(rhs_node, 'identifier', None)
            if rhs_identifier is not None:
                if isinstance(rhs_identifier, str):
                    rhs_name = rhs_identifier
                elif hasattr(rhs_identifier, 'valueText'):
                    rhs_name = getattr(rhs_identifier, 'valueText', '') or ''
            
            # Get the assignment expression part only (not the clock)
            assign_syntax = str(assign_node) if hasattr(assign_node, '__str__') else ''
            
            trace = TraceResult(
                trace_type=TraceType.DRIVER,
                signal_name=lhs_name,
                source_expr=assign_syntax,
                source_signals=[rhs_name] if rhs_name else [],
                file=scope.file_path,
                line=scope.line_start,
                char_offset=0,
                scope_kind=scope.kind,
                scope_line_start=scope.line_start,
                scope_line_end=scope.line_end,
                scope_text=scope.text,
                scope_offset_start=scope.offset_start,
                scope_offset_end=scope.offset_end,
                clock='',
                reset='',
                hierarchical_path=scope.instance_path,
            )
            if lhs_name not in self._drivers:
                self._drivers[lhs_name] = []
            self._drivers[lhs_name].append(trace)
            
            # Add load trace for RHS signal
            if rhs_name and rhs_name != lhs_name:
                if rhs_name not in self._loads:
                    self._loads[rhs_name] = []
                load_trace = TraceResult(
                    trace_type=TraceType.LOAD,
                    signal_name=rhs_name,
                    source_expr=lhs_name,
                    source_signals=[lhs_name],
                    file=scope.file_path,
                    line=scope.line_start,
                    char_offset=0,
                    scope_kind=scope.kind,
                    scope_line_start=scope.line_start,
                    scope_line_end=scope.line_end,
                    scope_text=scope.text,
                    scope_offset_start=scope.offset_start,
                    scope_offset_end=scope.offset_end,
                    clock='',
                    reset='',
                    hierarchical_path=scope.instance_path,
                )
                self._loads[rhs_name].append(load_trace)

    def _process_statement(self, stmt, scope):
        """向后兼容的 shim — 委托给 _process_any

        保留这个方法名以防外部代码调用。
        """
        self._process_any(stmt, scope, condition_stack=[])

    def _process_case_stmt(self, case_stmt, scope, condition_stack):
        """处理 case/casez/casex/unique case/cover case 语句

        - 把 case(expr) 里的 expr 涉及的信号记为 load
        - 递归处理每个 item.statement 和 defaultCase
        - condition_stack 传播下去
        """
        # 把 case 表达式涉及的信号记为 load
        expr = getattr(case_stmt, 'expr', None)
        if expr:
            rhs_info = self._get_rhs_info_semantic(expr)
            for sig in rhs_info['signals']:
                if sig not in self._loads:
                    self._loads[sig] = []
                load_trace = TraceResult(
                    trace_type=TraceType.LOAD,
                    signal_name=sig,
                    source_expr=f"case({rhs_info['text']})",
                    source_signals=[rhs_info['text']],
                    file=scope.file_path,
                    line=scope.line_start,
                    char_offset=0,
                    scope_kind=scope.kind,
                    scope_line_start=scope.line_start,
                    scope_line_end=scope.line_end,
                    scope_text=scope.text,
                    scope_offset_start=scope.offset_start,
                    scope_offset_end=scope.offset_end,
                    clock=scope.clock,
                    reset=scope.reset,
                    hierarchical_path=scope.instance_path,
                    condition_stack=list(condition_stack),
                )
                self._loads[sig].append(load_trace)

        # case 本身也作为一层 context (用 case 表达式文本作标识)
        case_label = f"case({getattr(expr, 'syntax', expr)!s})" if expr else "case"
        new_stack = list(condition_stack) + [case_label]

        # 递归处理每个 case item
        items = getattr(case_stmt, 'items', []) or []
        for item in items:
            item_stmt = getattr(item, 'statement', None)
            if item_stmt:
                self._process_any(item_stmt, scope, new_stack)

        # 递归处理 default 分支
        default_case = getattr(case_stmt, 'defaultCase', None)
        if default_case:
            self._process_any(default_case, scope, new_stack)

    def _process_conditional_stmt(self, cond_stmt, scope, condition_stack):
        """处理 if / else if / else 条件语句

        pyslang 的表示：每个 if-else if 都是嵌套的 ConditionalStatement。
        `if (A) X else if (B) Y else Z` →
            outer_cs.ifTrue = X
            outer_cs.ifFalse = nested_cs
            nested_cs.ifTrue = Y
            nested_cs.ifFalse = Z

        每个 cs.conditions 列表里一般只有 1 个 cond，cond.stmt 为 None。
        ifTrue/ifFalse 是实际的分支。

        把每个 cond 表达式中的信号记为 load，cond 文本推入 condition_stack 后递归 ifTrue。
        """
        # 迭代处理 if-else if 链
        cs = cond_stmt
        while cs is not None and type(cs).__name__ == 'ConditionalStatement':
            # 提取本层 cond 表达式
            conditions = getattr(cs, 'conditions', []) or []
            cond_text = ''
            for cond in conditions:
                cond_expr = getattr(cond, 'expr', None)
                if cond_expr:
                    rhs_info = self._get_rhs_info_semantic(cond_expr)
                    cond_text = rhs_info['text']
                    for sig in rhs_info['signals']:
                        if sig not in self._loads:
                            self._loads[sig] = []
                        load_trace = TraceResult(
                            trace_type=TraceType.LOAD,
                            signal_name=sig,
                            source_expr=cond_text,
                            source_signals=rhs_info['signals'],
                            file=scope.file_path,
                            line=scope.line_start,
                            char_offset=0,
                            scope_kind=scope.kind,
                            scope_line_start=scope.line_start,
                            scope_line_end=scope.line_end,
                            scope_text=scope.text,
                            scope_offset_start=scope.offset_start,
                            scope_offset_end=scope.offset_end,
                            clock=scope.clock,
                            reset=scope.reset,
                            hierarchical_path=scope.instance_path,
                            condition_stack=list(condition_stack),
                        )
                        self._loads[sig].append(load_trace)

            # 递归 ifTrue，把 cond 文本推入栈
            new_stack = list(condition_stack) + ([cond_text] if cond_text else [])
            if_true = getattr(cs, 'ifTrue', None)
            if if_true:
                self._process_any(if_true, scope, new_stack)

            # 走到 else 分支
            if_false = getattr(cs, 'ifFalse', None)
            if if_false is None:
                break  # 没有 else，到此为止
            if type(if_false).__name__ == 'ConditionalStatement':
                # else if: 继续循环，处理下一层 cs
                cs = if_false
            else:
                # 纯 else: 不推新 cond，复用当前 condition_stack
                self._process_any(if_false, scope, list(condition_stack))
                break

    def _process_call_stmt(self, call_stmt, scope, condition_stack):
        """处理 task 调用语句 (CallStatement)

        例: do_something(a, b); — 参数中的 a, b 是 load
        """
        # CallStatement 内部有 subroutine (subroutine 名) + arguments
        subroutine = getattr(call_stmt, 'subroutine', None)
        args = getattr(call_stmt, 'arguments', None) or []

        # 提取函数/任务名 (仅供记录)
        call_name = ''
        if subroutine is not None:
            call_name = getattr(subroutine, 'name', '') or str(subroutine)

        # 遍历参数
        for arg in args:
            if arg is None:
                continue
            # arg 可能是 Expression wrapper 或直接的 Expression
            expr = getattr(arg, 'expr', arg)
            rhs_info = self._get_rhs_info_semantic(expr)
            for sig in rhs_info['signals']:
                if sig not in self._loads:
                    self._loads[sig] = []
                load_trace = TraceResult(
                    trace_type=TraceType.LOAD,
                    signal_name=sig,
                    source_expr=f"{call_name}({rhs_info['text']})" if call_name else rhs_info['text'],
                    source_signals=rhs_info['signals'],
                    file=scope.file_path,
                    line=scope.line_start,
                    char_offset=0,
                    scope_kind=scope.kind,
                    scope_line_start=scope.line_start,
                    scope_line_end=scope.line_end,
                    scope_text=scope.text,
                    scope_offset_start=scope.offset_start,
                    scope_offset_end=scope.offset_end,
                    clock=scope.clock,
                    reset=scope.reset,
                    hierarchical_path=scope.instance_path,
                    condition_stack=list(condition_stack),
                )
                self._loads[sig].append(load_trace)

    def _process_assignment_expr(self, expr, scope, condition_stack):
        """处理赋值表达式 (AssignmentExpression / ContinuousAssign 内部)

        创建 driver trace (LHS) 和多个 load traces (RHS 引用的信号)。
        condition_stack 会透传到每条 trace。
        """
        if expr is None:
            return

        # Get left (target) and right (source) from semantic expressions
        lhs_name = self._get_lhs_name_semantic(expr.left) if hasattr(expr, 'left') else ''
        if not lhs_name:
            return

        rhs_info = self._get_rhs_info_semantic(expr.right) if hasattr(expr, 'right') else {'text': '', 'signals': []}

        # M2: 获取实际赋值表达式的行号 (不是 scope 起始行)
        actual_line, actual_offset = self._get_expr_location(expr, scope)

        # M3: 用 scope.instance_path (hpath) 作为前缀, 让 trace('top.u_sub.signal') 能工作
        full_name = self._qualify_signal_name(scope, lhs_name)

        # Create trace for driver
        trace = TraceResult(
            trace_type=TraceType.DRIVER,
            signal_name=lhs_name,
            source_expr=rhs_info['text'],
            source_signals=rhs_info['signals'],
            file=scope.file_path,
            line=actual_line,
            char_offset=actual_offset,
            scope_kind=scope.kind,
            scope_line_start=scope.line_start,
            scope_line_end=scope.line_end,
            scope_text=scope.text,
            scope_offset_start=scope.offset_start,
            scope_offset_end=scope.offset_end,
            clock=scope.clock,
            reset=scope.reset,
            hierarchical_path=scope.instance_path,
            condition_stack=list(condition_stack),
        )
        # M5.1h: 注入 syntax node, 让 syntax-based evidence 能工作
        # 注入 expr.syntax (语法节点) 而非 expr (语义 Expression),
        # 因为 build_evidence_via_syntax 走 str(syntax_node) 拿 snippet,
        # 对语义 Expression str() 返回的是 'Expression(ExpressionKind.X)' 类名, 不是源码
        # M5.1h: 用 SyntaxNodeSnapshot 冻结 str()
        trace._syntax_node = SyntaxNodeSnapshot(
            getattr(expr, 'syntax', expr) or expr
        )
        if full_name not in self._drivers:
            self._drivers[full_name] = []
        self._drivers[full_name].append(trace)

        # 同时存到 leaf name 和基名下, 让 trace('signal') / trace('arr') 也能查到
        if lhs_name not in self._drivers:
            self._drivers[lhs_name] = []
        self._drivers[lhs_name].append(trace)
        if '[' in lhs_name:
            base = lhs_name.split('[')[0]
            if base and base != lhs_name:
                if base not in self._drivers:
                    self._drivers[base] = []
                self._drivers[base].append(trace)

        # Create traces for loads
        for sig in rhs_info['signals']:
            if sig != lhs_name:
                full_sig = self._qualify_signal_name(scope, sig)
                if full_sig not in self._loads:
                    self._loads[full_sig] = []
                if sig not in self._loads:
                    self._loads[sig] = []
                load_trace = TraceResult(
                    trace_type=TraceType.LOAD,
                    signal_name=sig,
                    source_expr=lhs_name,
                    source_signals=[lhs_name],
                    file=scope.file_path,
                    line=actual_line,
                    char_offset=actual_offset,
                    scope_kind=scope.kind,
                    scope_line_start=scope.line_start,
                    scope_line_end=scope.line_end,
                    scope_text=scope.text,
                    scope_offset_start=scope.offset_start,
                    scope_offset_end=scope.offset_end,
                    clock=scope.clock,
                    reset=scope.reset,
                    hierarchical_path=scope.instance_path,
                    condition_stack=list(condition_stack),
                )
                # M5.1h: 注入 syntax node (同 driver, 走 syntax 节点)
                # M5.1h fix: load trace 用 expr.right.syntax (RHS 表达式节点),
                # 不然 function call 场景下 expr.syntax 会把 load 'a' 指向 'foo(a)' 而非 'a'
                # M5.1h: 用 SyntaxNodeSnapshot 冻结 str()
                rhs_syntax = getattr(expr, 'right', None)
                if rhs_syntax is not None:
                    rhs_syntax = getattr(rhs_syntax, 'syntax', rhs_syntax)
                load_trace._syntax_node = SyntaxNodeSnapshot(
                    rhs_syntax or getattr(expr, 'syntax', expr) or expr
                )
                self._loads[full_sig].append(load_trace)
                self._loads[sig].append(load_trace)

    def _qualify_signal_name(self, scope, signal_name: str) -> str:
        """M3: 用 scope 的 hpath 前缀限定信号名

        例: scope.instance_path='top.u_sub', signal_name='out_data'
            -> 'top.u_sub.out_data'

        退化: scope.instance_path 为空 / 'unknown' 时, 返回原 signal_name
        """
        prefix = scope.instance_path if scope else ''
        if not prefix or prefix == 'unknown':
            return signal_name
        if not signal_name:
            return prefix
        return f"{prefix}.{signal_name}"

    def _offset_to_line(self, source_loc) -> int:
        """M4: 用 pyslang SourceManager 跨文件精确算行号

        之前问题: self._sv_code 只存第一个文件, 用 count('\n') 算的
        行号在多文件下完全错 (pyslang 的 offset 是 per-file 的)。

        Solution: pyslang SourceManager.getLineNumber(SourceLocation) 能
        跨文件 (看 SourceLocation.buffer) 正确算行号。

        Returns:
            1-indexed 行号, 如果无法计算返回 0
        """
        if source_loc is None or self._source_manager is None:
            return 0
        try:
            return self._source_manager.getLineNumber(source_loc)
        except Exception:
            return 0

    def _get_file_from_location(self, source_loc) -> str:
        """M4: 用 pyslang SourceManager 跨文件获得文件名

        之前 bug: TraceResult.file 总是指向第一个添加的文件 (spid_csb_sync.sv 等)
        原因: self._file_path 只在第一个文件 add_file 时被设
        修复: 从 SourceLocation 拿到 buffer 交给 SourceManager 查文件名

        Returns:
            文件路径, 如果无法计算返回 self._file_path (fallback)
        """
        if source_loc is None or self._source_manager is None:
            return self._file_path
        try:
            return self._source_manager.getFileName(source_loc)
        except Exception:
            return self._file_path

    def _get_expr_location(self, expr, scope) -> Tuple[int, int]:
        """获取表达式的精确位置 (行号, 字符偏移)

        M2: 返回 AssignmentExpression 的真实位置, 不是 scope 起始位置。
        M4: 跨文件精确 — 走 pyslang SourceManager (不看 self._sv_code)。

        多个 fallback:
        1. expr.sourceRange + SourceManager → 跨文件精确行号
        2. expr.syntax.sourceRange + SourceManager
        3. scope.line_start (最后 fallback)

        Returns:
            (line, char_offset) — 都是 1-indexed (line) / 0-indexed (char_offset)
        """
        # Try semantic layer first
        sr = getattr(expr, 'sourceRange', None)
        if sr is None:
            # Try syntax layer
            syn = getattr(expr, 'syntax', None)
            if syn:
                sr = getattr(syn, 'sourceRange', None)

        if sr:
            offset = sr.start.offset
            if offset > 0:
                line = self._offset_to_line(sr.start)
                if line > 0:
                    return line, offset
        # Fallback to scope
        return scope.line_start, 0

    def _get_lhs_name_semantic(self, expr) -> str:
        """从语义表达式获取左值名称"""
        if expr is None:
            return ""
        
        kind = str(expr.kind).split('.')[-1]
        
        if kind == 'ElementSelect':
            # Array element access like data[i]
            value = getattr(expr, 'value', None)
            if value:
                symbol = getattr(value, 'symbol', None)
                if symbol:
                    name = getattr(symbol, 'name', '') or ''
                    # Get selector (index)
                    selector = getattr(expr, 'selector', None)
                    if selector:
                        sel_name = getattr(selector, 'name', None) or self._get_selector_name(selector)
                        if sel_name:
                            return f'{name}[{sel_name}]'
                    return name
        elif kind == 'RangeSelect':
            # Part select like data[7:4]
            value = getattr(expr, 'value', None)
            if value:
                symbol = getattr(value, 'symbol', None)
                if symbol:
                    name = getattr(symbol, 'name', '') or ''
                    # Get range [left:right]
                    left = getattr(expr, 'left', None)
                    right = getattr(expr, 'right', None)
                    if left and right:
                        left_val = getattr(left, 'name', None) or self._get_selector_name(left)
                        right_val = getattr(right, 'name', None) or self._get_selector_name(right)
                        if left_val and right_val:
                            return f'{name}[{left_val}:{right_val}]'
                    return name
                # M5.2: 嵌套 ElementSelect, e.g. arr[0][255:0] 的 [0] 部分
                # value 有 .selector 字段 (如 [0])
                value_kind = str(value.kind).split('.')[-1]
                if value_kind == 'ElementSelect':
                    # 递归拿 value 的字符串名
                    base_name = self._get_lhs_name_semantic(value) or ''
                elif value_kind == 'MemberAccess':
                    member = getattr(value, 'member', None)
                    if member:
                        member_name = getattr(member, 'name', '') or ''
                        # 拿 base (.value 的 .symbol.name)
                        base_value = getattr(value, 'value', None)
                        if base_value:
                            base_sym = getattr(base_value, 'symbol', None)
                            if base_sym:
                                base_name = getattr(base_sym, 'name', '') or ''
                                # 拿范围
                                left = getattr(expr, 'left', None)
                                right = getattr(expr, 'right', None)
                                if left and right:
                                    left_val = getattr(left, 'name', None) or self._get_selector_name(left)
                                    right_val = getattr(right, 'name', None) or self._get_selector_name(right)
                                    if left_val and right_val:
                                        return f'{base_name}.{member_name}[{left_val}:{right_val}]'
                                return f'{base_name}.{member_name}'
                # M4.1: 嵌套 HierarchicalValue (modport 访问), e.g. m.data[3:0]
                if value_kind == 'HierarchicalValue':
                    val_sym = getattr(value, 'symbol', None)
                    if val_sym:
                        internal = getattr(val_sym, 'internalSymbol', None)
                        if internal:
                            base_name = getattr(internal, 'name', '') or ''
                        else:
                            base_name = getattr(val_sym, 'name', '') or ''
                        left = getattr(expr, 'left', None)
                        right = getattr(expr, 'right', None)
                        if left and right:
                            left_val = getattr(left, 'name', None) or self._get_selector_name(left)
                            right_val = getattr(right, 'name', None) or self._get_selector_name(right)
                            if left_val and right_val:
                                return f'{base_name}[{left_val}:{right_val}]'
                        return base_name
        elif kind == 'NamedValue':
            # Simple variable like data
            symbol = getattr(expr, 'symbol', None)
            if symbol:
                return getattr(symbol, 'name', '') or ''

        elif kind == 'HierarchicalValue':
            # M4.1: Interface modport access, e.g. m.valid (modport master)
            # pyslang 语义层把 m.valid 折成为 ModportPortSymbol
            # .symbol.internalSymbol 是 interface 内的原始 VariableSymbol
            # .symbol.internalSymbol.name 是底层信号名 (例如 'valid')
            # .symbol.hierarchicalPath 是带 modport 的完整路径 (e.g. 'top.bus.master.valid')
            # 我们返回底层信号名, 让 trace('valid') 能定位
            sym = getattr(expr, 'symbol', None)
            if sym:
                internal = getattr(sym, 'internalSymbol', None)
                if internal:
                    return getattr(internal, 'name', '') or ''
                return getattr(sym, 'name', '') or ''

        return ""
    
    def _get_selector_name(self, expr) -> str:
        """获取选择器/索引表达式的名称"""
        if expr is None:
            return ""
        
        kind = str(expr.kind).split('.')[-1]
        
        if kind == 'NamedValue':
            symbol = getattr(expr, 'symbol', None)
            if symbol:
                return getattr(symbol, 'name', '') or ''
        elif kind == 'IntegerLiteral':
            # 之前用 .literal.valueText, 但 pyslang IntegerLiteral 是直接有 .value
            # 例: a[3:0] 的 left=3, right=0
            # 优先级: 1. syntax 文本  2. .value 数字  3. .constant
            syn = getattr(expr, 'syntax', None)
            if syn:
                syn_text = str(syn).strip()
                if syn_text:
                    return syn_text
            value = getattr(expr, 'value', None)
            if value is not None:
                # SVInt 有 toString 或 .value
                return str(value) if not hasattr(value, 'value') else str(value.value)
            constant = getattr(expr, 'constant', None)
            if constant is not None:
                return str(constant)
        elif kind == 'UnbasedUnsizedIntegerLiteral':
            # Unsized literal like '0, '1, 'x, 'z (常用于 cast 如 8'(expr))
            value = getattr(expr, 'value', None)
            if value is not None:
                # 拼回 '0 / '1 / 'x / 'z 形式
                return "'" + str(value).lower()
            # fallback
            literal = getattr(expr, 'literal', None)
            if literal:
                return getattr(literal, 'valueText', '') or "'0"

        return ""

    def _expr_to_source_text(self, expr, fallback: str = '') -> str:
        """M5.1h step 5: 从 syntax node 拿表达式在源码中的真实文本

        背景: 语义 Expression 的 str() 返回 'BinaryExpression(Add, a, b)' 这种
        C++ 风格文本, 而 syntax node 的 str() 返回 'a + b' 真实源码。后者才能
        与文件行 / 上下文做包含验证 (matches_source_expr)。

        fallback: 语义节点没有 .syntax 时返回 (如 import-only 表达式)。
        """
        if expr is None:
            return fallback
        syn = getattr(expr, 'syntax', None)
        if syn is None:
            return fallback
        try:
            text = str(syn).strip()
        except Exception:
            return fallback
        return text if text else fallback

    def _get_rhs_info_semantic(self, expr) -> Dict:
        """从语义表达式获取 RHS 信息 (文本 and 加载的信号) - M5.1h step 5 wrapper

        实际 kind-specific 逻辑在 _get_rhs_info_semantic_kind。本函数:
        1. 调 kind 拿 signals + kind-级别 text (例如 'a Add b')
        2. 覆盖 text 为 str(expr.syntax).strip() (真实源码 'a + b')

        这样 _process_assignment_expr 拿到的 source_expr 总是真实源码,
        matches_source_expr 能成立, credibility 提升到 1.0。
        """
        result = self._get_rhs_info_semantic_kind(expr)
        # 覆盖 text 为 syntax 真实文本
        syn_text = self._expr_to_source_text(expr, result.get('text', ''))
        if syn_text:
            result['text'] = syn_text
        return result

    def _get_rhs_info_semantic_kind(self, expr) -> Dict:
        """从语义表达式获取 RHS 信息 (文本 and 加载的信号)
        
        防御性检查: 遇到未知的表达式类型会记录并返回空，避免静默失败。
        """
        if expr is None:
            return {'text': '', 'signals': []}
        
        kind = str(expr.kind).split('.')[-1]
        
        if kind == 'Conversion':
            # Unary conversion like '1 or signed
            operand = getattr(expr, 'operand', None)
            if operand:
                return self._get_rhs_info_semantic(operand)

        elif kind in ('UnaryOp', 'UnaryExpression'):
            # Unary op: ~a, -a, !a, &a, |a, ^a, ~^a, +a
            # 递归到 operand 提取信号
            operand = getattr(expr, 'operand', None)
            op = getattr(expr, 'op', None)
            op_text = str(op).split('.')[-1] if op else '~'
            # 映射为可读文本
            op_map = {
                'BitwiseNot': '~', 'LogicalNot': '!', 'Minus': '-', 'Plus': '+',
                'BitwiseAnd': '&', 'BitwiseOr': '|', 'BitwiseXor': '^',
                'BitwiseNand': '~&', 'BitwiseNor': '~|', 'BitwiseXnor': '~^',
                'Preincrement': '++', 'Predecrement': '--',
            }
            op_symbol = op_map.get(op_text, op_text)
            if operand:
                inner = self._get_rhs_info_semantic(operand)
                return {
                    'text': f"{op_symbol}{inner['text']}",
                    'signals': inner['signals'],
                }
        
        elif kind in ('Binary', 'BinaryOp'):
            # Binary expression like a + b
            left = getattr(expr, 'left', None)
            right = getattr(expr, 'right', None)
            
            left_info = self._get_rhs_info_semantic(left) if left else {'text': '', 'signals': []}
            right_info = self._get_rhs_info_semantic(right) if right else {'text': '', 'signals': []}
            
            # Get operation text
            op = getattr(expr, 'op', None)
            op_text = str(op).split('.')[-1] if op else '+'
            
            return {
                'text': f"{left_info['text']} {op_text} {right_info['text']}",
                'signals': left_info['signals'] + right_info['signals']
            }
        
        elif kind == 'NamedValue':
            symbol = getattr(expr, 'symbol', None)
            if symbol:
                name = getattr(symbol, 'name', '') or ''
                return {'text': name, 'signals': [name]}
        
        elif kind == 'IntegerLiteral':
            # Use syntax for text, or value attribute
            syntax = getattr(expr, 'syntax', None)
            if syntax:
                return {'text': str(syntax).strip(), 'signals': []}
            # Fallback to value
            val = getattr(expr, 'value', None)
            if val:
                return {'text': str(val), 'signals': []}
        
        elif kind == 'ElementSelect':
            # Array element access: mem[addr] or mem[i][j] (nested)
            # Extract base name and selector recursively
            value = getattr(expr, 'value', None)
            selector = getattr(expr, 'selector', None)
            
            # Get base name and signals from value
            base_name = ''
            signals = []
            if value:
                value_kind = str(value.kind).split('.')[-1]
                if value_kind == 'NamedValue':
                    value_symbol = getattr(value, 'symbol', None)
                    if value_symbol:
                        base_name = getattr(value_symbol, 'name', '') or ''
                        # NamedValue is a signal being read
                        signals.append(base_name)
                elif value_kind == 'ElementSelect':
                    # Nested access: get the full base recursively
                    base_info = self._get_rhs_info_semantic(value)
                    base_name = base_info['text']
                    signals.extend(base_info['signals'])
            
            # Get selector info (this is also a load)
            sel_info = self._get_rhs_info_semantic(selector) if selector else {'text': '', 'signals': []}
            sel_name = sel_info['text']
            signals.extend(sel_info['signals'])
            
            full_name = f"{base_name}[{sel_name}]" if sel_name else base_name
            
            return {'text': full_name, 'signals': signals}
        
        elif kind == 'RangeSelect':
            # Part select: data[7:4] - extract the base signal
            value = getattr(expr, 'value', None)
            selector = getattr(expr, 'selector', None)
            
            base_name = ''
            signals = []
            if value:
                value_kind = str(value.kind).split('.')[-1]
                if value_kind == 'NamedValue':
                    value_symbol = getattr(value, 'symbol', None)
                    if value_symbol:
                        base_name = getattr(value_symbol, 'name', '') or ''
                        signals.append(base_name)
                elif value_kind == 'MemberAccess':
                    # 嵌套: e.g. reg2hw.val[BufferAw:0]
                    # 递归拿整个 member chain 的 text 和 signals
                    value_info = self._get_rhs_info_semantic(value)
                    base_name = value_info['text']
                    signals.extend(value_info['signals'])
                elif value_kind == 'HierarchicalValue':
                    # M4.1: modport 访问 + bit select, e.g. m.data[3:0]
                    val_sym = getattr(value, 'symbol', None)
                    if val_sym:
                        hpath = getattr(val_sym, 'hierarchicalPath', '') or ''
                        if not hpath:
                            internal = getattr(val_sym, 'internalSymbol', None)
                            if internal:
                                hpath = getattr(internal, 'hierarchicalPath', '') or ''
                        if hpath:
                            base_name = hpath
                            signals.append(hpath)
                elif value_kind == 'ElementSelect':
                    # M5.2: 嵌套 ElementSelect, e.g. sideload[0][255:0]
                    value_info = self._get_rhs_info_semantic(value)
                    base_name = value_info['text']
                    signals.extend(value_info['signals'])

            # Get range info [left:right]
            left_val = getattr(expr, 'left', None)
            right_val = getattr(expr, 'right', None)
            range_text = ''
            if left_val and right_val:
                left_info = self._get_rhs_info_semantic(left_val)
                right_info = self._get_rhs_info_semantic(right_val)
                range_text = f"[{left_info['text']}:{right_info['text']}]"
            
            full_name = f"{base_name}{range_text}" if base_name else ''
            
            return {'text': full_name, 'signals': signals}
        
        elif kind == 'Concatenation':
            # Concatenation: {a, b, c} or Replication: {N{a}}
            operands = getattr(expr, 'operands', []) or []
            
            all_signals = []
            all_texts = []
            for operand in operands:
                op_info = self._get_rhs_info_semantic(operand)
                all_signals.extend(op_info['signals'])
                if op_info['text']:
                    all_texts.append(op_info['text'])
            
            replication_count = getattr(expr, 'count', None)
            if replication_count:
                inner_text = ', '.join(all_texts)
                return {
                    'text': f"{{{{{replication_count}{{{inner_text}}}}}}}",
                    'signals': all_signals
                }
            else:
                return {
                    'text': '{' + ', '.join(all_texts) + '}',
                    'signals': all_signals
                }
        
        elif kind in ('ConditionalOp', 'ConditionalExpression'):
            # Ternary: a ? b : c
            # Check for conditions list (ConditionalOp) or direct attributes
            conditions = getattr(expr, 'conditions', None)
            if conditions:
                # ConditionalOp style
                all_signals = []
                all_texts = []
                for cond in conditions:
                    cond_expr = getattr(cond, 'expr', None)
                    cond_info = self._get_rhs_info_semantic(cond_expr) if cond_expr else {'text': '', 'signals': []}
                    all_signals.extend(cond_info['signals'])
                    if cond_info['text']:
                        all_texts.append(cond_info['text'])
                
                true_info = self._get_rhs_info_semantic(getattr(expr, 'left', None))
                false_info = self._get_rhs_info_semantic(getattr(expr, 'right', None))
                
                return {
                    'text': f"{' ? '.join(all_texts)} ? {true_info['text']} : {false_info['text']}",
                    'signals': all_signals + true_info['signals'] + false_info['signals']
                }
            else:
                # Direct ConditionalExpression style
                cond_info = self._get_rhs_info_semantic(getattr(expr, 'condition', None))
                true_info = self._get_rhs_info_semantic(getattr(expr, 'if_true', None))
                false_info = self._get_rhs_info_semantic(getattr(expr, 'if_false', None))
                
                return {
                    'text': f"{cond_info['text']} ? {true_info['text']} : {false_info['text']}",
                    'signals': cond_info['signals'] + true_info['signals'] + false_info['signals']
                }
        
        elif kind in ('Call', 'FunctionCallExpression'):
            # Function call: func(a, b, c)
            # Extract all arguments as loaded signals
            args = getattr(expr, 'arguments', []) or []
            all_signals = []
            all_texts = []
            
            for arg in args:
                arg_info = self._get_rhs_info_semantic(arg)
                all_signals.extend(arg_info['signals'])
                if arg_info['text']:
                    all_texts.append(arg_info['text'])
            
            # Get function name
            func_name = getattr(expr, 'subroutineName', None) or 'func'
            
            return {
                'text': f"{func_name}({', '.join(all_texts)})",
                'signals': all_signals
            }
        
        elif kind == 'MemoryAccess':
            # Multi-dimensional array: mem[i][j]
            mem = getattr(expr, 'memory', None)
            indices = getattr(expr, 'indices', []) or []
            
            mem_name = ''
            if mem:
                sym = getattr(mem, 'symbol', None)
                mem_name = getattr(sym, 'name', '') if sym else ''
            
            idx_signals = []
            idx_texts = []
            for idx in indices:
                idx_info = self._get_rhs_info_semantic(idx)
                idx_signals.extend(idx_info['signals'])
                if idx_info['text']:
                    idx_texts.append(idx_info['text'])
            
            # Build access string
            access_str = mem_name
            for idx_text in idx_texts:
                access_str += f"[{idx_text}]"
            
            return {
                'text': access_str,
                'signals': idx_signals
            }
        
        elif kind == 'CastExpression':
            # Type cast: '(type)expr
            operand = getattr(expr, 'operand', None)
            cast_type = getattr(expr, 'castType', None)
            
            type_name = str(cast_type).split('.')[-1] if cast_type else 'type'
            operand_info = self._get_rhs_info_semantic(operand) if operand else {'text': '', 'signals': []}
            
            return {
                'text': f"'{type_name}({operand_info['text']})",
                'signals': operand_info['signals']
            }
        
        elif kind == 'UnaryExpression':
            # Unary operators: -a, !a, ~a
            operand = getattr(expr, 'operand', None)
            op = getattr(expr, 'op', None)
            op_text = str(op).split('.')[-1] if op else ''

            operand_info = self._get_rhs_info_semantic(operand) if operand else {'text': '', 'signals': []}

            return {
                'text': f"{op_text}{operand_info['text']}",
                'signals': operand_info['signals']
            }

        elif kind == 'MemberAccess':
            # M4: struct/类 成员访问, e.g. r.q, blk.ctrl.tx.q, reg2hw.ctrl.tx.q
            # .value 是父表达式 (NamedValue 或嵌套 MemberAccess)
            # .member 是 FieldSymbol, 取 .name 拿字段名
            value = getattr(expr, 'value', None)
            member = getattr(expr, 'member', None)
            member_name = ''
            if member is not None:
                member_name = getattr(member, 'name', '') or str(member)
            value_info = self._get_rhs_info_semantic(value) if value else {'text': '', 'signals': []}
            base_text = value_info['text'] or (getattr(value, 'symbol', None) and getattr(value.symbol, 'name', '') or '')
            full_text = f"{base_text}.{member_name}" if base_text else member_name
            return {
                'text': full_text,
                'signals': value_info['signals'],  # 基础信号是 load, field 本身不是变量
            }

        elif kind == 'HierarchicalValue':
            # M4.1: Interface modport 访问, e.g. m.valid, s.data[7:0]
            # pyslang 把 m.valid 折成 ModportPortSymbol:
            #   .symbol.name = 'valid' (接口内的原始信号名)
            #   .symbol.hierarchicalPath = 'top.bus.master.valid' (带 modport)
            #   .symbol.internalSymbol = VariableSymbol (接口内变量)
            # 我们返回: text=完整路径, signals=[完整路径]
            # 这样 trace('top.bus.valid') 能查, trace('valid') 也能查 (trace 做后缀匹配)
            sym = getattr(expr, 'symbol', None)
            if sym:
                hpath = getattr(sym, 'hierarchicalPath', '') or ''
                if not hpath:
                    # 退化到 internalSymbol
                    internal = getattr(sym, 'internalSymbol', None)
                    if internal:
                        hpath = getattr(internal, 'hierarchicalPath', '') or ''
                name = getattr(sym, 'name', '') or ''
                if hpath:
                    return {'text': hpath, 'signals': [hpath]}
                if name:
                    return {'text': name, 'signals': [name]}
            return {'text': '', 'signals': []}

        elif kind == 'Replication':
            # M4: {count{expr}} — 拼接复制
            # 例: {8{1'b1}} -> "8'11111111" 文本
            # .count 是次数 (IntegerLiteral)
            # .concat 内部是 ConcatenationExpression (M4 也顺手处理)
            count = getattr(expr, 'count', None)
            concat = getattr(expr, 'concat', None)
            # 复用 _get_rhs_info_semantic 拿 concat 内部的信号
            concat_info = self._get_rhs_info_semantic(concat) if concat else {'text': '', 'signals': []}
            # count 文本 (IntegerLiteral 直接取 value)
            count_val = ''
            if count is not None:
                count_lit = getattr(count, 'literal', None) or getattr(count, 'value', None)
                if count_lit is not None:
                    count_val = str(getattr(count_lit, 'valueText', count_lit))
                else:
                    count_val = str(count)
            full_text = f"{{{count_val}{{{concat_info['text']}}}}}"
            return {
                'text': full_text,
                'signals': concat_info['signals'],
            }

        elif kind == 'UnbasedUnsizedIntegerLiteral':
            # M4: unsized literal like '0, '1, 'x, 'z (常用于 cast)
            value = getattr(expr, 'value', None)
            text = ''
            if value is not None:
                text = "'" + str(value).lower()
            elif getattr(expr, 'literal', None) is not None:
                text = "'" + str(getattr(expr.literal, 'valueText', '0'))
            else:
                text = "'0"
            return {'text': text, 'signals': []}

        elif kind == 'StructuredAssignmentPattern':
            # M4: SV struct initialization/assignment pattern
            # e.g. my_struct_t'{a: val_a, b: val_b}
            # memberSetters: [MemberSetter{expr, member}, ...]
            # elements: [expr, ...] — 按顺序对应字段
            member_setters = getattr(expr, 'memberSetters', [])
            elements = getattr(expr, 'elements', [])
            parts = []
            signals = []
            if member_setters:
                for ms in member_setters:
                    ms_expr = getattr(ms, 'expr', None)
                    ms_member = getattr(ms, 'member', None)
                    member_name = getattr(ms_member, 'name', '') or ''
                    if ms_expr:
                        info = self._get_rhs_info_semantic(ms_expr)
                        parts.append(f"{member_name}: {info['text']}")
                        signals.extend(info['signals'])
                    else:
                        parts.append(f"{member_name}: ?")
            elif elements:
                for el in elements:
                    info = self._get_rhs_info_semantic(el) if el else {'text': '?', 'signals': []}
                    parts.append(info['text'])
                    signals.extend(info['signals'])
            else:
                parts = ['?']
            return {
                'text': "'{" + ', '.join(parts) + '}' if parts else "'?",
                'signals': list(set(signals))
            }

        elif kind == 'SimpleAssignmentPattern':
            # M4: 单字段 struct literal, e.g. my_t'{a: val}
            # 与 StructuredAssignmentPattern 相同结构 (memberSetters/elements)
            member_setters = getattr(expr, 'memberSetters', [])
            elements = getattr(expr, 'elements', [])
            parts = []
            signals = []
            if member_setters:
                for ms in member_setters:
                    ms_expr = getattr(ms, 'expr', None)
                    ms_member = getattr(ms, 'member', None)
                    member_name = getattr(ms_member, 'name', '') or ''
                    if ms_expr:
                        info = self._get_rhs_info_semantic(ms_expr)
                        parts.append(f"{member_name}: {info['text']}")
                        signals.extend(info['signals'])
                    else:
                        parts.append(f"{member_name}: ?")
            elif elements:
                for el in elements:
                    info = self._get_rhs_info_semantic(el) if el else {'text': '?', 'signals': []}
                    parts.append(info['text'])
                    signals.extend(info['signals'])
            return {
                'text': "'{" + ', '.join(parts) + '}' if parts else "'?",
                'signals': list(set(signals))
            }


        elif kind == 'LValueReference':
            # M4: LValue 在 RHS 中的引用 (少见)
            # 直接递归 .value
            value = getattr(expr, 'value', None)
            if value:
                return self._get_rhs_info_semantic(value)
            return {'text': '', 'signals': []}

        elif kind == 'Streaming':
            # M4: SV streaming concatenation, e.g. {<<8{val}}
            # .sliceSize: int (8 in <<8)
            # .streams: [StreamExpression, ...] — each has .operand
            # .bitstreamWidth: int
            slice_size = getattr(expr, 'sliceSize', 0)
            streams = getattr(expr, 'streams', [])
            parts = []
            signals = []
            for stream in streams:
                stream_operand = getattr(stream, 'operand', None)
                if stream_operand:
                    info = self._get_rhs_info_semantic(stream_operand)
                    parts.append(info['text'])
                    signals.extend(info['signals'])
            if not parts:
                return {'text': '', 'signals': []}
            # text: {<<8{operand}}
            inner = '{' + ', '.join(parts) + '}' if len(parts) > 1 else parts[0]
            return {
                'text': f"{{{'<<' if slice_size else '>>'}{slice_size}{{{inner}}}}}",
                'signals': list(set(signals))
            }

        elif kind == 'Inside':
            # M4: SV inside operator, e.g. (a inside {b, c, [1:5]})
            # .left: 主表达式
            # .rangeList: [expr, ...] — 集合成员
            left_expr = getattr(expr, 'left', None)
            range_list = getattr(expr, 'rangeList', [])
            signals = []
            parts = []
            if left_expr:
                left_info = self._get_rhs_info_semantic(left_expr)
                signals.extend(left_info['signals'])
                parts.append(left_info['text'])
            for r in range_list:
                info = self._get_rhs_info_semantic(r) if r else {'text': '?', 'signals': []}
                parts.append(info['text'])
                signals.extend(info['signals'])
            if len(parts) >= 2:
                return {
                    'text': f"({parts[0]} inside {{{', '.join(parts[1:])}}})",
                    'signals': list(set(signals))
                }
            return {'text': f"inside {{{', '.join(parts[1:])}}}", 'signals': list(set(signals))}

        elif kind == 'DataType':
            # M4: DataTypeExpression - 类型作为表达式 (罕见, 通常在 cast 上下文)
            # e.g. type'(val) 或 某些 SVA 上下文
            # 没有子表达式可追踪, 退到 syntax text
            syn = getattr(expr, 'syntax', None)
            if syn:
                return {'text': str(syn).strip(), 'signals': []}
            return {'text': '<type>', 'signals': []}

        else:
            # 防御性检查: 未知类型，记录并返回空
            import sys
            print(f"WARNING: Unknown expression kind in _get_rhs_info_semantic: {kind} ({type(expr).__name__})", file=sys.stderr)
            return {'text': '', 'signals': []}

    def _enrich_port_info(self, trace_result: TraceResult):
        """根据 hierarchical_path 设置端口信息"""
        # Construct full path: instance_path.signal_name
        full_path = f"{trace_result.hierarchical_path}.{trace_result.signal_name}" if trace_result.hierarchical_path else trace_result.signal_name
        if full_path in self._port_info:
            trace_result.is_port = True
            trace_result.port_direction = self._port_info[full_path]
        return trace_result
    
    def trace(self, signal_name: str, verify: bool = True) -> TraceSummary:
        """追踪信号的所有驱动和负载 (支持跨模块 + 层次路径)

        M3 智能匹配:
        1. 完全匹配 (signal_name 含 '.': 当 hpath 用; 否则当 leaf name)
        2. 前缀匹配 (数组 a[i] → a[...])
        3. 后缀匹配 (查 'out_data' 会找所有 '*.out_data')
        4. Cross-module fallback (找不到时走端口连接)
        """
        if not self._built:
            self.build()

        drivers: List[TraceResult] = []
        loads: List[TraceResult] = []

        # Pass 1: 完全匹配
        if signal_name in self._drivers:
            drivers.extend(self._drivers[signal_name])
        if signal_name in self._loads:
            loads.extend(self._loads[signal_name])

        # Pass 2: 数组前缀匹配 (a[0] 找 a[...])
        if not drivers and not loads and '[' in signal_name:
            base = signal_name.split('[')[0]
            for k, lst in self._drivers.items():
                if k.startswith(base + '['):
                    drivers.extend(lst)
            for k, lst in self._loads.items():
                if k.startswith(base + '['):
                    loads.extend(lst)

        # Pass 3: 后缀匹配 (查 'out_data' 找所有 '*.out_data')
        # 但只对不含 '.' 的查询做 (避免 'top.u_sub.out_data' 也匹配 'sub.out_data')
        if not drivers and not loads and '.' not in signal_name:
            suffix = '.' + signal_name
            seen_keys = set()  # 防重复
            for k, lst in self._drivers.items():
                if k.endswith(suffix) and k not in seen_keys:
                    drivers.extend(lst)
                    seen_keys.add(k)
            seen_keys.clear()
            for k, lst in self._loads.items():
                if k.endswith(suffix) and k not in seen_keys:
                    loads.extend(lst)
                    seen_keys.add(k)

        # Pass 4: Cross-module fallback (port connection)
        if not drivers or not loads:
            cross = self._cross_module_drivers(signal_name)
            if cross:
                drivers.extend(cross)

        # Enrich with port info
        drivers = [self._enrich_port_info(d) for d in drivers]
        loads = [self._enrich_port_info(l) for l in loads]

        # M5.1d: 自动填充 evidence (用 in-memory 文件内容)
        if verify and (drivers or loads):
            from signal_tracer.models import build_evidence
            for d in drivers:
                fc = self._get_file_content(d.file)
                if fc:
                    d._evidence_override = build_evidence(
                        file=d.file, line=d.line,
                        source_expr=d.source_expr, signal_name=d.signal_name,
                        scope_text=d.scope_text, file_content=fc, context_window=2,
                    )
            for l in loads:
                fc = self._get_file_content(l.file)
                if fc:
                    l._evidence_override = build_evidence(
                        file=l.file, line=l.line,
                        source_expr=l.source_expr, signal_name=l.signal_name,
                        scope_text=l.scope_text, file_content=fc, context_window=2,
                    )

        new_drivers = [DriverTrace(**_strip_evidence(d)) for d in drivers]
        new_loads = [LoadTrace(**_strip_evidence(l)) for l in loads]
        # 复制 _evidence_override 到新对象 (M5.1d)
        for orig, new in zip(drivers, new_drivers):
            ev = getattr(orig, '_evidence_override', None)
            if ev:
                new._evidence_override = ev
        for orig, new in zip(loads, new_loads):
            ev = getattr(orig, '_evidence_override', None)
            if ev:
                new._evidence_override = ev
        return TraceSummary(
            signal_name=signal_name,
            drivers=new_drivers,
            loads=new_loads,
        )
    
    def _cross_module_drivers(self, signal_name: str) -> List[TraceResult]:
        """通过端口连接查找信号的驱动 (跨模块追踪)
        
        例如: sig_in (top) -> u_dut.data_in (端口) -> u_dut.data_out (驱动)
        所以 sig_in 的驱动是 top.u_dut.data_out
        """
        if not self._port_resolver:
            return []
        
        result = []
        
        # Find all port connections where this signal is connected
        port_conns = self._port_resolver.get_signal_connections(signal_name)
        
        for conn in port_conns:
            # conn = PortConnection(instance_path='top.u_dut', port_name='data_in', connected_signal='sig_in', ...)
            # The port 'data_in' is an OUTPUT port of the parent module
            # Find what drives data_in inside the child module
            
            # Build full path to the port inside child module
            port_full_path = f"{conn.instance_path}.{conn.port_name}"
            
            # Check if this port has any drivers inside the child module
            # by tracing the port signal name inside the child instance
            port_drivers = self._find_drivers_through_port(conn)
            result.extend(port_drivers)
        
        return result
    
    def _find_drivers_through_port(self, conn: PortConnection) -> List[TraceResult]:
        """查找通过端口连接的内部信号驱动
        
        conn: 外部信号连接到 child_instance.child_port
        返回: child_instance 内部信号的驱动列表
        
        逻辑:
        - sig_in (top) 连接到 u_dut.data_in (输入端口)
        - data_in 在 dut 内部被使用 (如 data_out <= data_in)
        - data_out 是 data_in 的"下游"信号
        - 因此 sig_in 的驱动是 data_out (通过 data_in 传递)
        """
        result = []
        
        # The port name inside the child module (e.g., 'data_in')
        internal_port = conn.port_name
        
        # Find signals that depend on this port (signals where internal_port is on RHS)
        # In _loads, we store signals that use the queried signal
        # So _loads[data_in] = [data_out] means data_out uses data_in
        internal_loads = self._loads.get(internal_port, [])
        
        for load in internal_loads:
            # This signal depends on the port - it's what the port drives
            new_result = TraceResult(
                signal_name=load.signal_name,
                trace_type=TraceType.DRIVER,  # It's a driver from external perspective
                hierarchical_path=load.hierarchical_path,
                line=load.line,
                source_expr=load.source_expr,
                scope_text=getattr(load, 'scope_text', ''),
                scope_kind=getattr(load, 'scope_kind', None),
                is_port=load.is_port,
                port_direction=load.port_direction,
            )
            result.append(new_result)
        
        return result
    
    def trace_drivers(self, signal_name: str, verify: bool = True) -> List[DriverTrace]:
        """只追踪驱动 (M5.1d: 默认 verify=True, 自动带 evidence)"""
        if not self._built:
            self.build()
        drivers = list(self._drivers.get(signal_name, []))
        if verify and drivers:
            from signal_tracer.models import build_evidence
            for d in drivers:
                fc = self._get_file_content(d.file)
                if fc:
                    d._evidence_override = build_evidence(
                        file=d.file, line=d.line,
                        source_expr=d.source_expr, signal_name=d.signal_name,
                        scope_text=d.scope_text, file_content=fc, context_window=2,
                    )
        new_drivers = [DriverTrace(**_strip_evidence(d)) for d in drivers]
        # 复制 _evidence_override 到新对象 (M5.1d)
        for orig, new in zip(drivers, new_drivers):
            ev = getattr(orig, '_evidence_override', None)
            if ev:
                new._evidence_override = ev
        return new_drivers

    def trace_loads(self, signal_name: str, verify: bool = True) -> List[LoadTrace]:
        """只追踪负载 (M5.1d: 默认 verify=True, 自动带 evidence)"""
        if not self._built:
            self.build()
        loads = list(self._loads.get(signal_name, []))
        if verify and loads:
            from signal_tracer.models import build_evidence
            for l in loads:
                fc = self._get_file_content(l.file)
                if fc:
                    l._evidence_override = build_evidence(
                        file=l.file, line=l.line,
                        source_expr=l.source_expr, signal_name=l.signal_name,
                        scope_text=l.scope_text, file_content=fc, context_window=2,
                    )
        new_loads = [LoadTrace(**_strip_evidence(l)) for l in loads]
        # 复制 _evidence_override 到新对象 (M5.1d)
        for orig, new in zip(loads, new_loads):
            ev = getattr(orig, '_evidence_override', None)
            if ev:
                new._evidence_override = ev
        return new_loads

    def _get_file_content(self, file_path: str) -> Optional[str]:
        """M5.1: 从已加载文件查找内容 (用于证据链交叉验证)

        路径匹配规则 (按优先级):
        1. 完全匹配
        2. basename 匹配 (兼容相对路径 vs 绝对路径)
        3. endswith 匹配 (宽松)
        """
        if not file_path:
            return None
        # Basename 提取
        import os
        target_base = os.path.basename(file_path)
        for fp, fc in self._files:
            if fp == file_path:
                return fc
            if target_base and os.path.basename(fp) == target_base:
                return fc
            if file_path and fp and fp.endswith(file_path):
                return fc
        return None

    def trace_verified(self, signal_name: str) -> 'TraceSummary':
        """M5.1: trace + 自动交叉验证 (读已加载的文件内容)

        Args:
            signal_name: 信号名

        Returns:
            TraceSummary, 每个 driver/load 的 ContextBundle.code_evidence 已被填充
        """
        result = self.trace(signal_name)
        from signal_tracer.models import build_evidence
        for d in result.drivers:
            fc = self._get_file_content(d.file)
            if fc:
                d._evidence_override = build_evidence(
                    file=d.file, line=d.line,
                    source_expr=d.source_expr, signal_name=d.signal_name,
                    scope_text=d.scope_text, file_content=fc, context_window=2,
                )
        for d in result.loads:
            fc = self._get_file_content(d.file)
            if fc:
                d._evidence_override = build_evidence(
                    file=d.file, line=d.line,
                    source_expr=d.source_expr, signal_name=d.signal_name,
                    scope_text=d.scope_text, file_content=fc, context_window=2,
                )
        return result

    def find_multi_drivers(self, verify: bool = True) -> Dict[str, List[TraceResult]]:
        """找出所有被多个 scope 驱动的信号 (>= 2 个不同 scope)

        在 always 风格的 RTL 里，同一信号被 >= 2 个不同 scope 驱动通常是 bug
        (例如两个 always_ff 都写 count，或 always_ff + assign 同时写)。

        去重规则：按 scope_text 去重。同一 always 块内的 if/else 多分支
        算 1 个 driver（它们实际是同一块代码在不同条件下的输出）。

        M5.1: 默认 verify=True, 为每个 driver 自动填充 code_evidence (用 in-memory
        文件内容), 让 caller 立刻看到每个 driver 的 credibility_score 0-1 和
        is_verified 标记。多驱动检测 + 证据链 = "看到冲突 + 看到冲突的真凭实据"。

        Args:
            verify: 是否自动填充 evidence (默认 True)

        Returns:
            Dict[信号名, List[TraceResult]], 只含 >= 2 个 scope 的信号。
            若 verify=True, 每个 driver 的 _evidence_override 已填充,
            可直接 d.to_context() 拿到带 credibility 的 ContextBundle。
        """
        if not self._built:
            self.build()

        result: Dict[str, List[TraceResult]] = {}
        for sig_name, drivers in self._drivers.items():
            # 收集所有不同的 scope_text
            unique_scopes = set()
            for d in drivers:
                if d.scope_text:
                    unique_scopes.add(d.scope_text)
            if len(unique_scopes) >= 2:
                result[sig_name] = drivers

        # M5.1: 自动填充 evidence (用 in-memory 文件内容, 避免磁盘 I/O)
        if verify and result:
            from signal_tracer.models import build_evidence
            for sig_name, drivers in result.items():
                for d in drivers:
                    fc = self._get_file_content(d.file)
                    if fc:
                        d._evidence_override = build_evidence(
                            file=d.file, line=d.line,
                            source_expr=d.source_expr, signal_name=d.signal_name,
                            scope_text=d.scope_text, file_content=fc, context_window=2,
                        )
        return result

    def find_multi_drivers_classified(
        self, verify: bool = True, include_false_positives: bool = False
    ) -> Dict[str, 'MultiDriverConflict']:
        """M5.2b: 多驱动检测 + 智能分类, 区分真 bug 和 false positive

        OpenTitan 验证发现: 之前 find_multi_drivers() 把以下都报为冲突:
        1. 跨 instance 同名 local (各 module 都有同名 error/control 信号)
        2. 按位分区写入 (不同 assign 写同一 signal 不同位段)
        3. generate 块内同名 local (不同 generate 分支)
        实际都不是真 multi-driver bug。

        本方法对每条冲突做 4 类分类:
        - 'real_conflict'      — 同一 instance 同一文件真有多个 scope 写同一 signal (真 bug)
        - 'cross_instance'     — 跨 instance, 各写各的同名 local (false positive)
        - 'bit_partition'      — 位选区间不重叠, 按位分区写 (false positive)
        - 'generate_block'     — generate 块内同名 local (false positive, 设计意图)

        Args:
            verify: 是否自动填充 evidence (默认 True)
            include_false_positives: 是否含 false positive (默认 False, 只返回真冲突)

        Returns:
            Dict[信号名, MultiDriverConflict], 含 classification/note/is_likely_bug
            若 include_false_positives=False (默认), 只返回 is_likely_bug=True 的真冲突
        """
        if not self._built:
            self.build()

        from signal_tracer.models import MultiDriverConflict, _classify_multi_drivers

        result: Dict[str, MultiDriverConflict] = {}
        for sig_name, drivers in self._drivers.items():
            # 收集所有不同的 scope_text
            unique_scopes = set()
            for d in drivers:
                if d.scope_text:
                    unique_scopes.add(d.scope_text)
            if len(unique_scopes) < 2:
                continue

            # 分类
            classification, note = _classify_multi_drivers(sig_name, drivers)
            unique_hpaths = len(set(d.hierarchical_path for d in drivers if d.hierarchical_path))
            bit_ranges = []
            from signal_tracer.models import _get_lhs_bit_range, _bit_ranges_overlap
            for d in drivers:
                br = _get_lhs_bit_range(d)
                if br is not None:
                    bit_ranges.append(br)
            overlap = None
            if len(bit_ranges) >= 2:
                overlap = any(_bit_ranges_overlap(bit_ranges[i], bit_ranges[j])
                              for i in range(len(bit_ranges))
                              for j in range(i+1, len(bit_ranges)))

            conflict = MultiDriverConflict(
                signal_name=sig_name,
                drivers=drivers,
                classification=classification,
                unique_scopes=len(unique_scopes),
                unique_hpaths=unique_hpaths,
                bit_range_overlap=overlap if overlap is not None else False,
                cross_files=sorted(set(d.file.split('/')[-1] for d in drivers if d.file)),
                note=note,
            )

            # 过滤
            if not include_false_positives and not conflict.is_likely_bug:
                continue
            result[sig_name] = conflict

        # 填充 evidence (跟 find_multi_drivers 一致)
        if verify and result:
            from signal_tracer.models import build_evidence
            for sig_name, conflict in result.items():
                for d in conflict.drivers:
                    fc = self._get_file_content(d.file)
                    if fc:
                        d._evidence_override = build_evidence(
                            file=d.file, line=d.line,
                            source_expr=d.source_expr, signal_name=d.signal_name,
                            scope_text=d.scope_text, file_content=fc, context_window=2,
                        )
        return result

    def dump_multi_drivers(
        self,
        verify: bool = True,
        include_context_window: bool = True,
        include_scope_text: bool = False,
        summary_only: bool = False,
        classify: bool = True,
    ) -> Dict:
        """M5.1g: 一次 dump 整个多驱动检测结果 (含 summary + 每个冲突的 evidence 详细)

        与 find_multi_drivers 配对使用, 但返回的是**整冲突列表的 dict**, 含:
        - conflicts: 每个多驱动信号的完整信息 (含每个 driver 的 evidence)
        - summary: 整链统计 (冲突信号数 / 总 driver 数 / 跨文件范围)

        Args:
            verify: 是否自动填充 evidence (默认 True)
            include_context_window: 是否含 context_window (默认 True)
            include_scope_text: 是否含完整 scope_text (默认 False)
            summary_only: 只返回 summary 不要 conflicts (默认 False)

        Returns:
            Dict 含 2 个顶层字段: summary / conflicts
            (与 dump_chain 不同, 这里没有 direction 因为方向是固定的: 多驱动检测)
        """
        # M5.2b: 默认 classify=True, 走分类方法排除 false positive
        classified_lookup = {}
        if classify:
            classified_lookup = self.find_multi_drivers_classified(
                verify=verify, include_false_positives=True
            )
            # 转成老格式 (sig -> List[TraceResult]) 给下面循环用
            multi = {sig: conflict.drivers for sig, conflict in classified_lookup.items()
                     if conflict.is_likely_bug}
        else:
            multi = self.find_multi_drivers(verify=verify)
        if not multi and not (classify and classified_lookup):
            return {
                'summary': {
                    'total_conflict_signals': 0,
                    'total_drivers': 0,
                    'avg_drivers_per_conflict': 0.0,
                    'avg_credibility': 0.0,
                    'min_credibility': 0.0,
                    'all_verified': True,
                    'cross_files': [],
                    'real_conflict_count': 0,
                    'cross_instance_count': 0,
                    'bit_partition_count': 0,
                    'generate_block_count': 0,
                },
                'conflicts': [],
            }

        # 对每个冲突的每个 driver, 转成精简 dict (复用 _dump_chain 的 hop 格式)
        conflicts = []
        total_drivers = 0
        credibilities = []
        cross_files = set()
        all_verified_count = 0
        total_driver_count = 0

        # M5.2b: 收集 summary 统计 (从所有 driver, 不只是 filter 后的)
        all_drivers_for_stats = []
        if classify and classified_lookup:
            for conflict in classified_lookup.values():
                all_drivers_for_stats.extend(conflict.drivers)
        else:
            for drivers in multi.values():
                all_drivers_for_stats.extend(drivers)
        for d in all_drivers_for_stats:
            if d.file:
                cross_files.add(d.file.split('/')[-1])

        for sig, drivers in multi.items():
            # scope 数 (去重)
            unique_scopes = set()
            for d in drivers:
                if d.scope_text:
                    unique_scopes.add(d.scope_text)

            # 每个 driver 转 dict
            driver_dicts = []
            for d in drivers:
                ctx = d.to_context()
                ce = ctx.code_evidence
                try:
                    cred = round(ce.credibility_score, 2)
                except Exception:
                    cred = 0.0
                credibilities.append(cred)
                if ce and ce.is_verified:
                    all_verified_count += 1
                if d.file:
                    cross_files.add(d.file.split('/')[-1])
                total_driver_count += 1

                d_dict = {
                    'signal_name': d.signal_name,
                    'file': d.file.split('/')[-1] if d.file else '',
                    'line': d.line,
                    'hierarchical_path': d.hierarchical_path,
                    'source_expr': d.source_expr,
                    'source_signals': list(d.source_signals) if d.source_signals else [],
                    'scope_kind': str(d.scope_kind) if d.scope_kind else '',
                    'credibility': cred,
                    'is_verified': ce.is_verified if ce else False,
                    'matches_source_expr': ce.matches_source_expr if ce else False,
                    'matches_signal_name': ce.matches_signal_name if ce else False,
                    'snippet': ce.snippet if ce else '',
                }
                if include_scope_text:
                    d_dict['scope_text'] = d.scope_text or ''
                if include_context_window and ce:
                    d_dict['context_window'] = {
                        'before': list(ce.context_before),
                        'after': list(ce.context_after),
                    }
                driver_dicts.append(d_dict)

            conflict_dict = {
                'signal_name': sig,
                'scope_count': len(unique_scopes),
                'driver_count': len(drivers),
                'drivers': driver_dicts,
            }
            if classify:
                conflict_info = classified_lookup.get(sig)
                if conflict_info:
                    conflict_dict['classification'] = conflict_info.classification
                    conflict_dict['is_likely_bug'] = conflict_info.is_likely_bug
                    conflict_dict['note'] = conflict_info.note
                    conflict_dict['bit_range_overlap'] = conflict_info.bit_range_overlap
            conflicts.append(conflict_dict)

        # M5.2b: 统计 4 类分类数
        # 注意: 用 classified_lookup (全部) 而非 conflicts (过滤后), 拿完整分类统计
        if classify and classified_lookup:
            real_conflict_count = sum(1 for c in classified_lookup.values() if c.is_likely_bug)
            cross_instance_count = sum(1 for c in classified_lookup.values() if c.classification == 'cross_instance')
            bit_partition_count = sum(1 for c in classified_lookup.values() if c.classification == 'bit_partition')
            generate_block_count = sum(1 for c in classified_lookup.values() if c.classification == 'generate_block')
        else:
            real_conflict_count = len(conflicts)
            cross_instance_count = 0
            bit_partition_count = 0
            generate_block_count = 0

        # M5.2b: total_conflict_signals 反映所有分类的总数 (含 false positive)
        if classify and classified_lookup:
            total_conflict_signals_all = len(classified_lookup)
            total_drivers_all = sum(len(c.drivers) for c in classified_lookup.values())
        else:
            total_conflict_signals_all = len(conflicts)
            total_drivers_all = total_driver_count
        summary = {
            'total_conflict_signals': total_conflict_signals_all,
            'total_drivers': total_drivers_all,
            'avg_drivers_per_conflict': round(total_drivers_all / total_conflict_signals_all, 2) if total_conflict_signals_all else 0.0,
            'avg_credibility': round(sum(credibilities) / len(credibilities), 2) if credibilities else 0.0,
            'min_credibility': min(credibilities) if credibilities else 0.0,
            'all_verified': all_verified_count == total_driver_count,
            'cross_files': sorted(cross_files),
            'real_conflict_count': real_conflict_count,
            'cross_instance_count': cross_instance_count,
            'bit_partition_count': bit_partition_count,
            'generate_block_count': generate_block_count,
        }

        result = {'summary': summary}
        if not summary_only:
            result['conflicts'] = conflicts
        return result

    def get_driver_count(self, signal_name: str) -> int:
        """返回驱动某信号的不同 scope 数

        便捷方法，等价于 len({d.scope_text for d in self._drivers[signal_name] if d.scope_text})
        """
        if not self._built:
            self.build()
        drivers = self._drivers.get(signal_name, [])
        return len({d.scope_text for d in drivers if d.scope_text})

    def get_driver_chain(
        self, signal_name: str, max_depth: int = 10, verify: bool = True
    ) -> List[TraceResult]:
        """递归查询信号的完整驱动链 (从 output 追溯到 input)

        与 TraceSummary.get_driver_chain() 不同:
        - TraceSummary 版: 只看直接 driver 的 source_signals
        - 本方法: 实际查 _drivers[candidate], 递归所有上游

        例如:
            always_comb b = a + 1;
            always_ff @(posedge clk) c <= b;
        调 get_driver_chain('c') 返回 [DriverTrace(c<=b), DriverTrace(b<=a+1)]

        循环依赖 (a = b; b = a) 会自动检测, 不死循环。

        M5.1b: 默认 verify=True, 为驱动链上每个 trace 自动填充 evidence。
        调用 d.to_context() 立刻拿到带 credibility_score 的 ContextBundle,
        让用户能看到链上每一跳的"真凭实据"。

        Args:
            signal_name: 起始信号
            max_depth: 最大递归深度 (防复杂网状电路)
            verify: M5.1b: 是否自动填充 evidence (默认 True)

        Returns:
            List[TraceResult], 顺序是 从信号本身向其上游
        """
        if not self._built:
            self.build()

        chain: List[TraceResult] = []
        visited: Set[str] = set()

        def walk(sig: str, depth: int):
            if depth > max_depth or sig in visited:
                return
            visited.add(sig)

            # 当前 sig 的所有 driver
            drivers = self._drivers.get(sig, [])
            for d in drivers:
                chain.append(d)
                # 下一跳: d.source_signals 中的所有信号名
                for src in d.source_signals:
                    if src and self._is_real_signal(src):
                        walk(src, depth + 1)

        walk(signal_name, 0)

        # M5.1b: 自动填充 evidence (用 in-memory 文件内容)
        if verify and chain:
            from signal_tracer.models import build_evidence
            for d in chain:
                fc = self._get_file_content(d.file)
                if fc:
                    d._evidence_override = build_evidence(
                        file=d.file, line=d.line,
                        source_expr=d.source_expr, signal_name=d.signal_name,
                        scope_text=d.scope_text, file_content=fc, context_window=2,
                    )
        return chain

    def get_load_chain(
        self, signal_name: str, max_depth: int = 10, verify: bool = True
    ) -> List[TraceResult]:
        """递归查询信号的完整负载链 (从 signal 顺藤摸瓜到所有下游)

        与 get_driver_chain 方向相反:
        - get_driver_chain: 顺藤摸瓜查上游 (谁驱动了 signal)
        - get_load_chain: 顺藤摸瓜查下游 (谁读了 signal, 又被谁读)

        递归逻辑:
        1. 找 s 的所有 loads (谁读了 s)
        2. 每个 load 的 LHS 是下一跳信号
        3. 对下一跳信号递归查 loads
        4. cycle detection (visited set)

        例如:
            always_comb b = a + 1;  // b 读 a
            always_comb c = b + 1;  // c 读 b
            always_comb d = c;      // d 读 c
        调 get_load_chain('a') 返回 [
            LoadTrace(b 读 a, uart_core.sv:4),
            LoadTrace(c 读 b, uart_core.sv:5),
            LoadTrace(d 读 c, uart_core.sv:6),
        ]

        M5.1e: 默认 verify=True, 链上每条 load 自动填充 evidence。
        跟 get_driver_chain (M5.1c) 完全对称, 一查就反查, 顺藤摸瓜带 credibility。

        Args:
            signal_name: 起始信号 (查询"谁读了这个信号")
            max_depth: 最大递归深度
            verify: M5.1e: 是否自动填充 evidence (默认 True)

        Returns:
            List[TraceResult] (load 类型), 顺序是 从 signal 顺流到下游。
            若 verify=True, 每个 load 的 _evidence_override 已填充。
        """
        if not self._built:
            self.build()

        chain: List[TraceResult] = []
        visited: Set[str] = set()

        def walk(sig: str, depth: int):
            if depth > max_depth or sig in visited:
                return
            visited.add(sig)

            # 找所有读 sig 的 load
            loads = self._loads.get(sig, [])
            for l in loads:
                chain.append(l)
                # 下一跳: load 的 source_signals (LHS — 谁写了, 也就是谁读了 sig)
                # load.signal_name 是查询的 signal, source_signals 是 LHS 列表
                for next_sig in l.source_signals:
                    if next_sig and next_sig != sig and self._is_real_signal(next_sig):
                        walk(next_sig, depth + 1)
                # 注意: 一个 load 可能让 chain 同 LHS 出现多次 (因为 source_signals 含多个 LHS)
                # 但 visited 集合会避免死循环

        walk(signal_name, 0)

        # M5.1e: 自动填充 evidence (用 in-memory 文件内容)
        if verify and chain:
            from signal_tracer.models import build_evidence
            for l in chain:
                fc = self._get_file_content(l.file)
                if fc:
                    l._evidence_override = build_evidence(
                        file=l.file, line=l.line,
                        source_expr=l.source_expr, signal_name=l.signal_name,
                        scope_text=l.scope_text, file_content=fc, context_window=2,
                    )
        return chain

    def dump_driver_chain(
        self, signal_name: str, max_depth: int = 10,
        include_context_window: bool = True,
        include_scope_text: bool = False,
        summary_only: bool = False,
    ) -> Dict:
        """M5.1f: 一次 dump 整个 driver chain 为 dict (含 summary, 喂 LLM 友好)

        与 get_driver_chain 配对使用, 但返回的是**整链的字典**, 含:
        - hops: 每跳的精简 dict (含 credibility / snippet / context_window)
        - summary: 整链统计 (avg_credibility / min / verified_count / cross_files)

        Args:
            signal_name: 起始信号
            max_depth: 最大递归深度
            include_context_window: 是否含 context_window.before/after (默认 True)
            include_scope_text: 是否含完整 scope_text (默认 False, 字符串可能较长)
            summary_only: 只返回 summary 不要 hops (默认 False)

        Returns:
            Dict 含 4 个顶层字段: signal_name / direction / hops / summary
        """
        chain = self.get_driver_chain(signal_name, max_depth=max_depth, verify=True)
        return _dump_chain(
            chain, signal_name, 'upstream',
            include_context_window=include_context_window,
            include_scope_text=include_scope_text,
            summary_only=summary_only,
        )

    def dump_load_chain(
        self, signal_name: str, max_depth: int = 10,
        include_context_window: bool = True,
        include_scope_text: bool = False,
        summary_only: bool = False,
    ) -> Dict:
        """M5.1f: 一次 dump 整个 load chain 为 dict (与 dump_driver_chain 对称)

        Args:
            signal_name: 起始信号
            max_depth: 最大递归深度
            include_context_window: 是否含 context_window (默认 True)
            include_scope_text: 是否含 scope_text (默认 False)
            summary_only: 只返回 summary 不要 hops (默认 False)

        Returns:
            Dict 含 4 个顶层字段: signal_name / direction / hops / summary
        """
        chain = self.get_load_chain(signal_name, max_depth=max_depth, verify=True)
        return _dump_chain(
            chain, signal_name, 'downstream',
            include_context_window=include_context_window,
            include_scope_text=include_scope_text,
            summary_only=summary_only,
        )

    def _is_real_signal(self, name: str) -> bool:
        """判断 name 是否是真实信号名 (不是字面常量 / 关键字)

        过滤:
        - 数字字面量: 0, 1, 8'h00
        - 关键字: '0', '1', 'x', 'z'
        - 空字符串
        """
        if not name:
            return False
        # 数字字面量
        if name[0].isdigit():
            return False
        # SystemVerilog literal 前缀
        if name.startswith("'") or name in ('0', '1', 'x', 'z', 'X', 'Z'):
            return False
        # 表达式
        if any(op in name for op in ('+', '-', '*', '/', '&', '|', '^', '~', '?', ':', '<', '>')):
            return False
        return True


class SignalTracerFromFile(SignalTracer):
    """从文件加载的信号追踪器"""
    
    def __init__(self, file_path: str):
        with open(file_path) as f:
            sv_code = f.read()
        super().__init__(sv_code, file_path)


def trace_signal(signal_name: str, sv_code: str, file_path: str = "") -> TraceSummary:
    """追踪信号 (便捷函数)"""
    tracer = SignalTracer(sv_code, file_path)
    return tracer.trace(signal_name)


def trace_signal_from_file(signal_name: str, file_path: str) -> TraceSummary:
    """从文件追踪信号 (便捷函数)"""
    tracer = SignalTracerFromFile(file_path)
    return tracer.trace(signal_name)