"""signal_tracer.tracer - 信号追踪核心实现

给一个信号，返回它的所有驱动和负载，包含文件位置和 scope 源码。
"""

import pyslang
from pyslang import SyntaxKind, TokenKind
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

from signal_tracer.models import (
    TraceResult, TraceType, ScopeKind, DriverTrace, LoadTrace,
    ScopeInfo, SignalInfo, TraceSummary
)
from signal_tracer.port_resolver import PortResolver, PortConnection


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
        
        # Get left (target) and right (source) from semantic expressions
        lhs_name = self._get_lhs_name_semantic(assign_expr.left)
        rhs_info = self._get_rhs_info_semantic(assign_expr.right)
        
        if not lhs_name:
            return
        
        # Get location info (SourceLocation has offset, not line)
        loc = getattr(sym, 'location', None)
        if loc and hasattr(loc, 'offset'):
            line = self._sv_code[:loc.offset].count('\n') + 1 if loc.offset > 0 else 1
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
            file=self._file_path,
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
                    file=self._file_path,
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

        # Get location info (SourceLocation has offset, not line)
        loc = getattr(block, 'location', None)
        if loc and hasattr(loc, 'offset'):
            line_start = self._sv_code[:loc.offset].count('\n') + 1 if loc.offset > 0 else 1
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
                file=self._file_path,
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
                    file=self._file_path,
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
                    file=self._file_path,
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
                            file=self._file_path,
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
                    file=self._file_path,
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
            file=self._file_path,
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
                    file=self._file_path,
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

    def _get_expr_location(self, expr, scope) -> Tuple[int, int]:
        """获取表达式的精确位置 (行号, 字符偏移)

        M2: 返回 AssignmentExpression 的真实位置, 不是 scope 起始位置。
        多个 fallback:
        1. expr.sourceRange (pyslang 语义层提供)
        2. expr.syntax.sourceRange (语法层 fallback)
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
            if offset > 0 and offset <= len(self._sv_code):
                line = self._sv_code[:offset].count('\n') + 1
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
        elif kind == 'NamedValue':
            # Simple variable like data
            symbol = getattr(expr, 'symbol', None)
            if symbol:
                return getattr(symbol, 'name', '') or ''
        
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
            literal = getattr(expr, 'literal', None)
            if literal:
                return getattr(literal, 'valueText', '') or ''
        
        return ""
    
    def _get_rhs_info_semantic(self, expr) -> Dict:
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
    
    def trace(self, signal_name: str) -> TraceSummary:
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

        return TraceSummary(
            signal_name=signal_name,
            drivers=[DriverTrace(**d.__dict__) for d in drivers],
            loads=[LoadTrace(**l.__dict__) for l in loads],
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
    
    def trace_drivers(self, signal_name: str) -> List[DriverTrace]:
        """只追踪驱动"""
        if not self._built:
            self.build()
        return [DriverTrace(**d.__dict__) for d in self._drivers.get(signal_name, [])]
    
    def trace_loads(self, signal_name: str) -> List[LoadTrace]:
        """只追踪负载"""
        if not self._built:
            self.build()
        return [LoadTrace(**l.__dict__) for l in self._loads.get(signal_name, [])]

    def find_multi_drivers(self) -> Dict[str, List[TraceResult]]:
        """找出所有被多个 scope 驱动的信号 (>= 2 个不同 scope)

        在 always 风格的 RTL 里，同一信号被 >= 2 个不同 scope 驱动通常是 bug
        (例如两个 always_ff 都写 count，或 always_ff + assign 同时写)。

        去重规则：按 scope_text 去重。同一 always 块内的 if/else 多分支
        算 1 个 driver（它们实际是同一块代码在不同条件下的输出）。

        Returns:
            Dict[信号名, List[TraceResult]]，只含 >= 2 个 scope 的信号
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
        self, signal_name: str, max_depth: int = 10
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

        Args:
            signal_name: 起始信号
            max_depth: 最大递归深度 (防复杂网状电路)

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
        return chain

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