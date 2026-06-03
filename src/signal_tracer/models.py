from __future__ import annotations
"""signal_tracer.models - 数据模型

定义信号追踪的结果数据结构。
"""

from dataclasses import dataclass, field
import pyslang
from typing import List, Optional, Tuple
from enum import Enum


class TraceType(Enum):
    """追踪类型"""
    DRIVER = "driver"      # 作为被驱动目标 (output of this signal)
    LOAD = "load"          # 作为被读取源 (input to other signals)


class ScopeKind(Enum):
    """作用域类型"""
    ALWAYS_FF = "always_ff"
    ALWAYS_COMB = "always_comb"
    ALWAYS_LATCH = "always_latch"
    ALWAYS = "always"
    CONTINUOUS_ASSIGN = "continuous_assign"


@dataclass
class TraceResult:
    """一次驱动或负载跟踪结果"""
    
    # 基础信息
    trace_type: TraceType              # 'driver' | 'load'
    signal_name: str                   # 查询的信号名
    source_expr: str                   # 驱动/负载源表达式 (如 'a' 或 'a + b')
    source_signals: List[str] = field(default_factory=list)  # 源信号列表 (用于构建依赖图)
    
    # 位置信息
    file: str = ""                     # 文件路径
    line: int = 0                      # 语句行号 (1-indexed)
    char_offset: int = 0              # 字符偏移
    
    # 层次路径信息
    hierarchical_path: str = ""        # 完整层次路径 (如 'top.u_dut.data_out')
    
    # 端口信息
    is_port: bool = False              # 是否是端口
    port_direction: str = ""           # 端口方向 ('in', 'out', 'inout')
    
    # Scope 信息
    scope_kind: ScopeKind = None      # always_ff | always_comb | continuous_assign
    scope_line_start: int = 0         # scope 起始行 (1-indexed)
    scope_line_end: int = 0           # scope 结束行 (1-indexed)
    scope_text: str = ""              # 整个 scope 的源码 (如整个 always_ff 块)
    scope_offset_start: int = 0       # scope 起始字符偏移
    scope_offset_end: int = 0         # scope 结束字符偏移
    
    # 时钟域信息 (always_ff 时)
    clock: str = ""
    reset: str = ""
    
    # 条件信息 (if/else 内部时)
    condition: str = ""
    condition_stack: List[str] = field(default_factory=list)  # 嵌套 if 条件栈
    
    # 元数据
    confidence: str = "high"

    # M5.2c: 内部 _syntax_node (pyslang syntax 节点, 用于 syntax-based evidence)
    # 不在 __init__ 必传, tracer 在 build 时 setattr 注入
    _syntax_node: Any = field(default=None, repr=False, compare=False)

    def __repr__(self) -> str:
        direction = "<=" if self.trace_type == TraceType.DRIVER else "->"
        return f"TraceResult({self.signal_name} {direction} {self.source_expr!r}@{self.line})"

    def to_context(self, file_content: Optional[str] = None, context_window: int = 2,
                source_mode: str = 'auto') -> 'ContextBundle':
        """把自己打包成 ContextBundle (M5.1: 含 code evidence)

        用于 agent 一次性拿到 trace 的所有上下文 (file/line/scope/clock/reset/cond_stack/port)
        + 代码证据链 (读回 file:line, 验证 source_expr / signal_name 是否真的在该行)。

        Args:
            file_content: 可选, 直接传文件内容避免 I/O (用于测试)
            context_window: 前后各取几行作为上下文 (默认 2)
            source_mode: M5.2c - evidence 来源
                - 'file' (旧): 读文件按行号取 snippet
                - 'syntax' (新): 走 pyslang syntax tree, 从 _syntax_node 拿
                - 'auto' (默认): 优先 syntax (如果有), 否则 file

        Returns:
            ContextBundle 实例, 含 code_evidence 字段 (含 source 标识)
        """
        from signal_tracer.models import ContextBundle, build_evidence, build_evidence_via_syntax

        pre_built = getattr(self, '_evidence_override', None)
        syn_node = getattr(self, '_syntax_node', None)

        if source_mode == 'syntax' and syn_node is not None:
            # M5.2c step 6: load trace 才 narrow 到 signal_name (RHS sub-expr),
            # driver trace 用整节点 (因为 signal_name 是 LHS, narrow 丢 source_expr=RHS)
            narrow = self.signal_name if self.trace_type == TraceType.LOAD else None
            evidence = build_evidence_via_syntax(
                syntax_node=syn_node,
                source_expr=self.source_expr,
                signal_name=self.signal_name,
                scope_text=self.scope_text,
                file=self.file,
                context_window=context_window,
                narrow_to=narrow,
            )
        elif source_mode == 'auto' and syn_node is not None and pre_built is None:
            # auto + 有 syntax node + 没 pre-built: 走 syntax
            narrow = self.signal_name if self.trace_type == TraceType.LOAD else None
            evidence = build_evidence_via_syntax(
                syntax_node=syn_node,
                source_expr=self.source_expr,
                signal_name=self.signal_name,
                scope_text=self.scope_text,
                file=self.file,
                context_window=context_window,
                narrow_to=narrow,
            )
        elif pre_built is not None:
            evidence = pre_built
        else:
            evidence = build_evidence(
                file=self.file,
                line=self.line,
                source_expr=self.source_expr,
                signal_name=self.signal_name,
                scope_text=self.scope_text,
                file_content=file_content,
                context_window=context_window,
            )
        return ContextBundle(
            file=self.file,
            line=self.line,
            char_offset=self.char_offset,
            source_expr=self.source_expr,
            signal_name=self.signal_name,
            scope_text=self.scope_text,
            scope_line_start=self.scope_line_start,
            scope_line_end=self.scope_line_end,
            scope_kind=self.scope_kind.value if self.scope_kind else '',
            clock=self.clock,
            reset=self.reset,
            condition=self.condition,
            condition_stack=tuple(self.condition_stack),
            is_port=self.is_port,
            port_direction=self.port_direction,
            hierarchical_path=self.hierarchical_path,
            confidence=self.confidence,
            code_evidence=evidence,
        )


@dataclass
class DriverTrace(TraceResult):
    """驱动追踪结果 (继承 TraceResult)"""
    pass


@dataclass  
class LoadTrace(TraceResult):
    """负载追踪结果 (继承 TraceResult)"""
    pass


@dataclass
class ScopeInfo:
    """Scope 辅助信息"""
    kind: ScopeKind
    name: str                          # scope 名称 (如 "always_ff_0")
    parent_name: str = ""             # 父 scope 名称
    instance_path: str = ""           # 实例层次路径 (如 "top.u_dut")
    line_start: int = 0
    line_end: int = 0
    text: str = ""
    offset_start: int = 0
    offset_end: int = 0
    clock: str = ""
    reset: str = ""
    file_path: str = ""               # M4: 跨文件, scope 实际所在文件 (pyslang SourceManager 解析)


@dataclass
class SignalInfo:
    """信号基本信息"""
    name: str
    declared_scope: str               # 声明所在 scope
    width: int = 1
    is_input: bool = False
    is_output: bool = False
    is_register: bool = False         # 在 always_ff 中赋值


@dataclass
class TraceSummary:
    """追踪汇总"""
    signal_name: str
    drivers: List[DriverTrace] = field(default_factory=list)
    loads: List[LoadTrace] = field(default_factory=list)
    
    @property
    def all_traces(self) -> List[TraceResult]:
        return self.drivers + self.loads
    
    def get_clock_domains(self) -> List[str]:
        """获取涉及的时钟域"""
        clocks = set()
        for d in self.drivers:
            if d.clock:
                clocks.add(d.clock)
        return sorted(clocks)

    def is_multi_driver(self) -> bool:
        """判断该信号是否被多个不同 scope 驱动 (≥2)

        多驱动在 always 风格的 RTL 里通常是 bug (多 driver race),
        在 agent 视角是重要检查点。

        同一 always 块内的 if/else 多分支算 1 个 driver (按 scope_text 去重),
        因为它们实际是同一块代码在不同条件下的输出。

        Returns:
            True: >= 2 个不同 scope 驱动该信号
            False: 0 或 1 个 scope 驱动
        """
        unique_scopes = {d.scope_text for d in self.drivers if d.scope_text}
        return len(unique_scopes) >= 2

    def get_driver_scopes(self) -> List[str]:
        """返回驱动该信号的所有不同 scope 源码 (去重)

        供 agent 快速查看所有驱动源。同一 scope 多个分支只返回一次。
        """
        seen = []
        for d in self.drivers:
            if d.scope_text and d.scope_text not in seen:
                seen.append(d.scope_text)
        return seen

    def to_contexts(self, file_content: Optional[str] = None, context_window: int = 2) -> List['ContextBundle']:
        """把这次 trace 的所有 driver 打包为 ContextBundle 列表

        agent 拿到一个 List[ContextBundle] 可以一次性看到所有 driver 上下文,
        不必自己遍历 drivers 列表逐个 to_context()。

        M5.1: 可传 file_content 让证据链读到真实代码 (不传则尝试从 disk 读)

        Args:
            file_content: 可选, 已知 file 内容时直接传 (避免 I/O, 跨文件场景下不适用)
            context_window: 前后各取几行作为证据 (默认 2)

        Returns:
            List[ContextBundle], 顺序与 self.drivers 一致, 每个含 code_evidence
        """
        return [d.to_context(file_content=file_content, context_window=context_window) for d in self.drivers]
    
    def get_load_chain(self, max_depth: int = 10, verify: bool = True) -> List[TraceResult]:
        """获取负载链 (从 signal 顺藤摸瓜到下游), 返回 load TraceResult 列表 (M5.1e)

        与 SignalTracer.get_load_chain 类似, 但基于 self.loads 工作。
        区别:
        - SignalTracer.get_load_chain: 全图遍历, 跨整个项目
        - TraceSummary.get_load_chain: 只看本次 trace 的 loads

        M5.1e: 默认 verify=True, 链上每条 load 自动填充 evidence (与 M5.1c 对称)。

        Args:
            max_depth: 最大递归深度
            verify: 是否自动填充 evidence (默认 True)

        Returns:
            List[TraceResult] (load 类型), 顺序是 从 signal 顺流到下游
        """
        from signal_tracer.models import build_evidence
        chain: List['TraceResult'] = []
        visited = set()

        def build_chain(sig_name: str, depth: int):
            if depth > max_depth or sig_name in visited:
                return
            visited.add(sig_name)
            for l in self.loads:
                # 当前 load 的 source_signals 包含 sig_name
                if sig_name in l.source_signals:
                    chain.append(l)
                    # 下一跳: load 的 source_signals (LHS — 读 sig_name 的消费者)
                    for next_sig in l.source_signals:
                        if next_sig and next_sig != sig_name:
                            build_chain(next_sig, depth + 1)

        build_chain(self.signal_name, 0)

        # M5.1e: 自动填充 evidence
        if verify and chain:
            tracer = getattr(self, '_tracer', None)
            if tracer:
                for l in chain:
                    fc = tracer._get_file_content(l.file)
                    if fc:
                        l._evidence_override = build_evidence(
                            file=l.file, line=l.line,
                            source_expr=l.source_expr, signal_name=l.signal_name,
                            scope_text=l.scope_text, file_content=fc, context_window=2,
                        )
        return chain

    def get_driver_chain(self, max_depth: int = 10, verify: bool = True) -> List[TraceResult]:
        """获取驱动链 (从信号本身到上游), 返回 TraceResult 列表 (M5.1b)

        与 SignalTracer.get_driver_chain 类似, 但基于 self.drivers 工作。
        区别:
        - SignalTracer.get_driver_chain: 全图遍历, 跨整个项目
        - TraceSummary.get_driver_chain: 只看本次 trace 的 drivers

        M5.1b: 默认 verify=True, 为链上每个 trace 自动填充 evidence。

        Args:
            max_depth: 最大递归深度
            verify: 是否自动填充 evidence (默认 True)

        Returns:
            List[TraceResult], 顺序是 从信号本身向其上游
        """
        from signal_tracer.models import build_evidence
        chain: List['TraceResult'] = []
        visited = set()

        def build_chain(sig_name: str, depth: int):
            if depth > max_depth or sig_name in visited:
                return
            visited.add(sig_name)
            for d in self.drivers:
                if d.signal_name == sig_name:
                    chain.append(d)
                    for src in d.source_signals:
                        if src and src not in ('0', '1', 'true', 'false'):
                            build_chain(src, depth + 1)

        build_chain(self.signal_name, 0)

        # M5.1b: 自动填充 evidence
        if verify and chain:
            # M5.1b: 需要 SignalTracer 实例来获取 in-memory 内容
            # 没有实例时 (TraceSummary 单独使用), evidence 不会被自动填充,
            # 但用户仍可手动 build_evidence(...)
            tracer = getattr(self, '_tracer', None)
            if tracer:
                for d in chain:
                    fc = tracer._get_file_content(d.file)
                    if fc:
                        d._evidence_override = build_evidence(
                            file=d.file, line=d.line,
                            source_expr=d.source_expr, signal_name=d.signal_name,
                            scope_text=d.scope_text, file_content=fc, context_window=2,
                        )
        return chain


@dataclass(frozen=True)
class ContextBundle:
    """不可变的"上下文包" — 把一次 trace 的所有上下文信息打包

    设计动机:
    agent 拿到一条 trace 时, 需要同时知道: 在哪个文件哪一行, 周围整个 scope 的源码是什么,
    在什么 clock/reset 下, 嵌套在什么 if 条件里, 是 port 吗, 通过哪个 port 跨模块连过来...
    这些信息散在 TraceResult 的 10+ 个字段里, agent 自己拼装很烦。

    ContextBundle 把它们打包成一个 frozen dataclass, 可以一次性传给 LLM,
    也可以作为 dict / JSON 序列化。

    frozen=True 保证 immutable, 适合做 dict key 或 hash。
    """

    # 位置信息
    file: str
    line: int
    char_offset: int

    # Scope 信息
    scope_text: str
    scope_line_start: int
    scope_line_end: int
    scope_kind: str  # ScopeKind.value (e.g. 'always_ff'), str 便于序列化

    # 时钟/复位
    clock: str
    reset: str

    # 条件栈
    condition: str
    condition_stack: Tuple[str, ...]

    # 端口信息
    is_port: bool
    port_direction: str
    hierarchical_path: str

    # 元数据
    confidence: str

    # M5.1: 代码证据链 - 召回的代码上下文作为追踪的最核心证据
    # 含: 实际读回的行, 前后上下文, 与 source_expr/signal_name 的交叉验证
    code_evidence: "CodeEvidence" = None  # type: ignore  # forward ref, defined below

    # M5.1: 驱动的源表达式 + signal name (evidence 链中要被验证的)
    source_expr: str = ""
    signal_name: str = ""

    def to_dict(self) -> dict:
        """转为 dict 便于 JSON 序列化"""
        return {
            'file': self.file,
            'line': self.line,
            'char_offset': self.char_offset,
            'source_expr': self.source_expr,
            'signal_name': self.signal_name,
            'scope_text': self.scope_text,
            'scope_line_start': self.scope_line_start,
            'scope_line_end': self.scope_line_end,
            'scope_kind': self.scope_kind,
            'clock': self.clock,
            'reset': self.reset,
            'condition': self.condition,
            'condition_stack': list(self.condition_stack),
            'is_port': self.is_port,
            'port_direction': self.port_direction,
            'hierarchical_path': self.hierarchical_path,
            'confidence': self.confidence,
            'code_evidence': self.code_evidence.to_dict() if self.code_evidence else None,
            'credibility_score': self.code_evidence.credibility_score if self.code_evidence else None,
            'is_verified': self.code_evidence.is_verified if self.code_evidence else False,
            'matches_source_expr': self.code_evidence.matches_source_expr if self.code_evidence else None,
            'matches_signal_name': self.code_evidence.matches_signal_name if self.code_evidence else None,
            'evidence_snippet': self.code_evidence.snippet if self.code_evidence else '',
        }

    def summary(self) -> str:
        """生成一行可读摘要, 适合 LLM 看

        例: '01.sv:10 (always_ff) clk=clk, reset=rst_n, cond=[!rst_n]'
        """
        parts = [f'{self.file}:{self.line}']
        parts.append(f'({self.scope_kind})')
        if self.clock:
            parts.append(f'clock={self.clock}')
        if self.reset:
            parts.append(f'reset={self.reset}')
        if self.condition_stack:
            parts.append(f'cond={list(self.condition_stack)}')
        return ' '.join(parts)


@dataclass
class CodeEvidence:
    """代码证据 - 召回的代码上下文作为追踪证据链

    M5.1: 让 trace 不再是孤立的元数据, 而是能"自证" —
    通过读回实际文件, 证明:
    1. line 真的存在
    2. 该行真的有 source_expr
    3. 该行真的有 signal_name (LHS)
    4. scope_text 与文件一致

    M5.2c: 加 source 字段标识 evidence 来源 ('file' 或 'syntax'),
    让 caller 知道 snippet 是从文件 IO 读的还是 pyslang syntax tree 直接拿的。
    双版本 (file/syntax) 让用户可对比验证一致性。
    """
    file: str                                    # 路径
    line: int                                    # 1-indexed 行号
    snippet: str                                 # 实际读到的该行文本 (已 strip)
    context_before: List[str] = field(default_factory=list)  # 前 N 行
    context_after: List[str] = field(default_factory=list)   # 后 N 行
    scope_text: str = ""                         # 完整 always 块 (从 trace 传入)
    matches_source_expr: bool = False            # snippet 中能找到 source_expr
    matches_signal_name: bool = False           # snippet 中能找到 LHS signal_name
    file_readable: bool = False                  # 文件是否成功读取
    snippet_present: bool = False                # line 是否有内容
    source: str = "file"                        # M5.2c: 'file' (IO 读) 或 'syntax' (pyslang syntax tree)
    context_available: bool = True               # M5.2c fix: context_window 是否成功填充 (syntax 模式暂 False)

    @property
    def is_verified(self) -> bool:
        """是否交叉验证通过

        "代码召回"成功的定义:
        - 文件可读
        - line 实际存在
        - 该行真的包含 source_expr 或 signal_name

        M5.2c fix: 对 syntax 模式, file_readable=False (没读文件), 但
        snippet 仍可从 syntax tree 拿到, 仍能 contains source_expr/signal_name。
        所以 is_verified 同时支持 file 路径和 syntax 路径。
        """
        # 路径 1: file-based - 需要 file_readable
        # 路径 2: syntax-based - 不需要 file_readable, 但需要 source=syntax
        if self.source == 'syntax':
            return self.snippet_present and (
                self.matches_source_expr or self.matches_signal_name
            )
        return self.file_readable and self.snippet_present and (
            self.matches_source_expr or self.matches_signal_name
        )

    @property
    def credibility_score(self) -> float:
        """可信度量化 (0-1)

        - file_readable: 0.2
        - snippet_present: 0.2
        - matches_source_expr: 0.4
        - matches_signal_name: 0.2
        """
        score = 0.0
        if self.file_readable:
            score += 0.2
        if self.snippet_present:
            score += 0.2
        if self.matches_source_expr:
            score += 0.4
        if self.matches_signal_name:
            score += 0.2
        return min(1.0, score)

    def to_dict(self) -> dict:
        return {
            'file': self.file,
            'line': self.line,
            'snippet': self.snippet,
            'context_before': self.context_before,
            'context_after': self.context_after,
            'scope_text': self.scope_text,
            'matches_source_expr': self.matches_source_expr,
            'matches_signal_name': self.matches_signal_name,
            'file_readable': self.file_readable,
            'snippet_present': self.snippet_present,
            'source': self.source,  # M5.2c: 'file' 或 'syntax'
            'context_available': self.context_available,  # M5.2c step 3
            'is_verified': self.is_verified,
            'credibility_score': self.credibility_score,
        }

    def to_evidence_string(self, context_window: int = 2) -> str:
        """生成可读的证据字符串, 适合 LLM 看

        格式:
            Evidence for tx_enable @ uart_core.sv:77
              file_readable: True
              snippet: assign tx_enable = reg2hw.ctrl.tx.q;
              scope: always_ff @(posedge clk_i or negedge rst_ni) ...
              matches: source_expr='reg2hw.ctrl.tx.q' ✓, signal_name='tx_enable' ✓
              credibility: 1.0/1.0 (VERIFIED)
              context_before (2 lines):
                75 |  // some comment
                76 |  always_ff @(posedge clk_i or negedge rst_ni) begin
              context_after (2 lines):
                78 |    end
                79 |
        """
        lines = []
        lines.append(f"Evidence for {self.scope_text or 'trace'} @ {self.file}:{self.line}")
        lines.append(f"  source: {self.source}  # M5.2c: file | syntax")
        lines.append(f"  file_readable: {self.file_readable}")
        if self.snippet_present:
            lines.append(f"  snippet: {self.snippet}")
        if self.scope_text:
            scope_one_line = self.scope_text.replace('\n', ' ').strip()
            if len(scope_one_line) > 100:
                scope_one_line = scope_one_line[:100] + '...'
            lines.append(f"  scope: {scope_one_line}")
        checks = []
        checks.append(f"source_expr match: {'✓' if self.matches_source_expr else '✗'}")
        checks.append(f"signal_name match: {'✓' if self.matches_signal_name else '✗'}")
        lines.append(f"  matches: {', '.join(checks)}")
        lines.append(f"  credibility: {self.credibility_score:.2f}/1.0 ({'VERIFIED' if self.is_verified else 'UNVERIFIED'})")
        if not self.context_available and (self.context_before or self.context_after):
            # 防御: context_available=False 但有 context 数据, 说明状态不一致
            pass
        if self.context_available:
            if self.context_before:
                for i, ctx in enumerate(self.context_before):
                    actual_line = self.line - (len(self.context_before) - i)
                    lines.append(f"  {actual_line:4d} | {ctx}")
            if self.snippet_present:
                lines.append(f"  {self.line:4d} > {self.snippet}")
            if self.context_after:
                for i, ctx in enumerate(self.context_after):
                    actual_line = self.line + i + 1
                    lines.append(f"  {actual_line:4d} | {ctx}")
        else:
            # M5.2c step 3: syntax 模式暂无 context_window, 只显示当前行
            if self.snippet_present:
                lines.append(f"  {self.line:4d} > {self.snippet}  (syntax 模式暂无 context_window, M5.3 TODO)")
        return '\n'.join(lines)


@dataclass
class MultiDriverConflict:
    """多驱动冲突的分类结果 (M5.2b)

    区分真 bug vs false positive, 让 agent/用户能快速判断哪些是值得修的。
    """
    signal_name: str
    drivers: List['TraceResult']  # 所有 driver TraceResult
    classification: str            # 'real_conflict' / 'cross_instance' / 'bit_partition' / 'generate_block'
    unique_scopes: int            # 几个不同 scope_text
    unique_hpaths: int             # 几个不同 hierarchical_path
    bit_range_overlap: bool       # 位选区间是否重叠
    cross_files: List[str]        # 跨文件列表
    note: str                     # 解释: 为何这样分类

    @property
    def is_likely_bug(self) -> bool:
        """是否疑似真 multi-driver bug

        只有 real_conflict 是 (跨 instance 假阳性 + 按位分区都不是)。
        """
        return self.classification == 'real_conflict'


def _get_lhs_bit_range(driver) -> Optional[Tuple[int, int]]:
    """从 driver 的 LHS 提取位选区间 (lo, hi), 没有位选则返回 None

    用于按位分区检测:
    - assign sig[7:0] = ... → (0, 7)
    - assign sig[i] = ...   → None (i 是变量, 静态无法确定)
    - assign sig = ...      → None (整 signal)
    """
    if driver is None:
        return None
    # 拿 LHS — 通过 ScopeInfo 间接
    # 我们的 TraceResult 没有 lhs_expr, 但 scope_text 含 LHS
    scope = driver.scope_text or ''
    # 找第一个 '[' 后的数字
    import re
    m = re.search(r'\[(\d+)\s*:\s*(\d+)\]', scope)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return (min(lo, hi), max(lo, hi))
    # 单 bit [i]
    m2 = re.search(r'\[(\w+)\]', scope)
    if m2 and m2.group(1).isdigit():
        v = int(m2.group(1))
        return (v, v)
    return None


def _bit_ranges_overlap(r1, r2) -> bool:
    """两个位选区间 (lo, hi) 是否重叠"""
    if r1 is None or r2 is None:
        return None  # 未知
    l1, h1 = r1
    l2, h2 = r2
    return not (h1 < l2 or h2 < l1)


def _classify_multi_drivers(sig_name: str, drivers: List['TraceResult']) -> Tuple[str, str]:
    """分类 multi-driver: real_conflict / cross_instance / bit_partition / generate_block

    判定顺序 (从最确定的 false positive 排除开始):
    1. 跨 instance (unique_hpaths > 1) → cross_instance (false positive)
    2. 位选不重叠 → bit_partition (false positive)
    3. generate 块 (同一 always 内 instantiate 不同 generate 块) → generate_block (设计意图)
    4. 否则 → real_conflict (真 bug)

    Returns: (classification, note)
    """
    if not drivers:
        return 'real_conflict', 'no drivers'

    unique_hpaths = set()
    for d in drivers:
        if d.hierarchical_path:
            unique_hpaths.add(d.hierarchical_path)
        elif d.file:
            # 没 hpath 时用 file
            unique_hpaths.add(d.file.split('/')[-1])

    if len(unique_hpaths) > 1:
        return 'cross_instance', f'跨 {len(unique_hpaths)} 个 instance, 各写各的同名 local'

    # 同一 instance — 看位选
    bit_ranges = [_get_lhs_bit_range(d) for d in drivers]
    # 只看非 None 的
    known = [r for r in bit_ranges if r is not None]
    if len(known) >= 2:
        # 检查所有对是否都不重叠
        any_overlap = False
        for i in range(len(known)):
            for j in range(i+1, len(known)):
                if _bit_ranges_overlap(known[i], known[j]):
                    any_overlap = True
                    break
            if any_overlap:
                break
        if not any_overlap:
            return 'bit_partition', f'位选区间 {[r for r in known]} 不重叠, 按位分区写'

    # 看是否 generate 模式 (scope_text 包含 gen_ 关键字)
    if any('gen_' in (d.scope_text or '') for d in drivers):
        return 'generate_block', 'generate 块内同名 local 在不同 generate 分支各被驱动一次'

    return 'real_conflict', f'同一 instance 同一文件 {len(drivers)} 个 scope 写同一 signal'


def build_evidence(
    file: str,
    line: int,
    source_expr: str = "",
    signal_name: str = "",
    scope_text: str = "",
    file_content: Optional[str] = None,
    context_window: int = 2,
) -> CodeEvidence:
    """从实际文件读回代码, 构建交叉验证证据

    Args:
        file: SV 文件路径
        line: 1-indexed 行号
        source_expr: trace 的 source_expr (用于验证)
        signal_name: trace 的 LHS signal name
        scope_text: 完整 always 块
        file_content: 可选, 直接传文件内容 (避免 I/O, 方便测试)
        context_window: 前后各取几行 (默认 2)

    Returns:
        CodeEvidence 实例, 含 matches_*/is_verified/credibility_score
    """
    evidence = CodeEvidence(
        file=file,
        line=line,
        snippet="",
        scope_text=scope_text,
        source="file",  # M5.2c: file-based evidence
    )

    # 读文件
    content = file_content
    if content is None and file:
        try:
            with open(file) as f:
                content = f.read()
            evidence.file_readable = True
        except Exception:
            evidence.file_readable = False
            return evidence
    elif content is not None:
        evidence.file_readable = True

    if content is None or line < 1:
        return evidence

    # 拿指定行
    file_lines = content.split('\n')
    if line > len(file_lines):
        return evidence

    snippet = file_lines[line - 1].strip()  # 1-indexed
    if snippet:
        evidence.snippet = snippet
        evidence.snippet_present = True

    # 拿前后行
    start = max(0, line - context_window)
    evidence.context_before = [file_lines[i].rstrip() for i in range(start, line - 1)]
    end = min(len(file_lines), line + context_window)
    evidence.context_after = [file_lines[i].rstrip() for i in range(line, end)]

    # 验证
    if source_expr and source_expr in snippet:
        evidence.matches_source_expr = True
    if signal_name and signal_name in snippet:
        evidence.matches_signal_name = True

    return evidence


def build_evidence_via_syntax(
    syntax_node,
    source_expr: str = "",
    signal_name: str = "",
    scope_text: str = "",
    file: str = "",
    context_window: int = 2,
    narrow_to: Optional[str] = None,
) -> "CodeEvidence":
    """M5.2c: 从 pyslang syntax tree 直接拿 evidence (不走文件 IO)

    narrow_to: M5.2c step 6 - 如给定, 把 snippet 缩到包含该名字的最具体子节点
        (例: 'c = a + b' 中 load 'a' 拿到 'a' 而不是 'c = a + b')。
        默认为 None, 不缩 (保持整节点)。caller (to_context) 会按 trace_type
        传 signal_name (load) 或 None (driver, 因为 driver 的 signal_name 是
        LHS, 缩窄会丢 source_expr=RHS 上下文)。


    与 build_evidence (file-based) 对比:
    - file-based: 给定 file + line, 读文件 split('\n')[line-1]
    - syntax-based: 从 syntax_node.sourceRange 直接拿原文

    优势:
    - 不依赖文件存在 (memory-only SV code 也能工作)
    - 总是和 pyslang 解析结果 100% 一致
    - 多文件时不用记哪个 file 对应哪个 offset
    - 不依赖 line 准不准 (line 错了 syntax 仍指向正确)

    劣势:
    - 需要 trace 时把 syntax node 传过来
    - context_window 从行号改成 offset-based, 需 SourceManager
    """
    evidence = CodeEvidence(
        file=file,
        line=0,  # syntax-based 不依赖 line, 由 sourceRange.start.line 算
        snippet="",
        scope_text=scope_text,
        source="syntax",  # M5.2c: 标识是 syntax-based
    )

    if syntax_node is None:
        return evidence

    # M5.2c step 3 fix: 兼容 caller 传语义 Expression (e.g. 测试代码 / 旧 trace)
    # 语义节点 str() 返回类名, sourceRange 仍可用, 但 snippet 要走 .syntax
    if not hasattr(syntax_node, 'kind') or not hasattr(syntax_node, '__class__'):
        return evidence
    # 粗略判断: 语义 Expression 一般有 .kind == ExpressionKind.X, syntax 节点有 .kind == SyntaxKind.X
    # 更稳的判断: 有 .syntax 属性 且 无 .kind.name == 'Expression' — 直接走 .syntax
    if hasattr(syntax_node, 'syntax') and getattr(syntax_node, 'syntax', None) is not None \
            and getattr(syntax_node, 'kind', None) is not None \
            and 'Expression' in str(type(syntax_node.kind)):
        syntax_node = syntax_node.syntax

    # 拿 syntax 的 sourceRange
    sr = getattr(syntax_node, 'sourceRange', None)
    if sr is None:
        return evidence
    if not (hasattr(sr, 'start') and hasattr(sr, 'end')):
        return evidence

    # 拿 SourceManager 算 line + offset
    # 1. line from start.location
    try:
        # syntax 的 start 通常是 SourceLocation
        start_loc = sr.start
        line = _sm_get_line_number(start_loc)
    except Exception:
        line = 0
    evidence.line = line

    # 2. 拿 source text
    # 语法节点 str() 返回从 buffer 起点到 node 末的文本 (带前导空白)
    # 不影响 evidence 验证 (包含关系) 但 snippet 会包含 leading newline/indent
    #
    # M5.2c step 6: 如果给了 signal_name, narrowing 到该 signal 对应的最具体子节点
    # 例: trace 是 'c = a + b' 中 a 的 load, 整节点是 'a + b', narrowing 后是 'a'
    # 这样 snippet 更准确 (避免传 'a + b' 给用户, 而他实际只关心 'a')
    #
    # 防御: driver trace 的 signal_name 是 LHS (e.g. 'c'), narrowing 会把 snippet
    # 缩到 'c' 并丢掉 source_expr='a + b' 上下文。回退检查: narrowing 后
    # source_expr 不在 shrunk text 中 → 退回原节点。
    narrowed_node = syntax_node
    if narrow_to and syntax_node is not None:
        # 只有显式传 narrow_to 才缩 (caller 知道是 load trace 时才传)
        candidate = _find_subexpr_for_signal(syntax_node, narrow_to)
        if candidate is not None:
            narrowed_node = candidate
    syn_text = str(narrowed_node) if narrowed_node is not None else ''
    if syn_text and syn_text.strip():
        evidence.snippet = syn_text.strip()
        evidence.snippet_present = True

    # 3. context_window - M5.2c step 7 实现
    # 走 SourceManager + sourceRange 拿行号 + 拿 buffer 文本 + splitlines
    # 与 file-based build_evidence 算法一致, context_before/after 可对比
    before, after, ctx_line = _extract_syntax_context(sr, context_window=context_window)
    evidence.context_before = before
    evidence.context_after = after
    # ctx_line 应该等于 evidence.line; 如果不等说明 SourceManager 对该 loc 返回的行不对
    if before or after:
        evidence.context_available = True
    else:
        # 拿不到 context (SourceManager 未设, sr 无效, 越界等), 保留默认 False
        evidence.context_available = False

    # 验证 (用 narrowed syn_text, 防止 signal_name 只是大表达式一部分时误判)
    if source_expr and source_expr in syn_text:
        evidence.matches_source_expr = True
    if signal_name and signal_name in syn_text:
        evidence.matches_signal_name = True

    # 拿 file (从 location 拿, 如果有)
    sm = _get_source_manager()
    if not file:
        try:
            if hasattr(sr.start, 'buffer') and sm is not None:
                evidence.file = sm.getFileName(sr.start)
        except Exception:
            pass
    else:
        evidence.file = file

    return evidence


# M5.2c: helper 拿 SourceManager
_singleton_sm = None
def _get_source_manager():
    """从 SignalTracer 全局拿 SourceManager (懒初始化)

    SignalTracer.build() 时会设 self._source_manager.
    为了让 build_evidence_via_syntax 不依赖 tracer 实例, 我们用一个 module-level
    缓存。trace() 时应调 _set_source_manager() 同步过来。
    """
    global _singleton_sm
    return _singleton_sm


def _set_source_manager(sm) -> None:
    """SignalTracer 调这个同步 SourceManager"""
    global _singleton_sm
    _singleton_sm = sm


def _sm_get_line_number(loc) -> int:
    sm = _get_source_manager()
    if sm is None:
        return 0
    try:
        return sm.getLineNumber(loc)
    except Exception:
        return 0


def _sm_location_at(sm, buffer_id, offset):
    """拿 sourceManager 在 buffer 中给定 offset 的 SourceLocation"""
    if sm is None or offset < 0:
        return None
    try:
        return pyslang.SourceLocation(buffer_id, offset)
    except Exception:
        return None


def _extract_syntax_context(sr, context_window: int = 2) -> tuple:
    """M5.2c step 7: 从 SourceManager + sourceRange 拿 context_window 行 context

    与 file-based build_evidence 的算法保持一致 (同样的 start/end 索引, 同样
    的 rstrip), 让两路产出的 context_before/after 可直接对比。

    跨文件: sr.start.buffer 拿对应的 buffer_id, getSourceText 拿全文。

    防御: SourceManager 没设 / sr 无效 / 文本拿不到 → 返回空 (与 syntax 路径
    其他失败一致), 不影响主流程。

    Returns: (context_before, context_after, line)
    """
    sm = _get_source_manager()
    if sm is None or sr is None:
        return [], [], 0
    if context_window < 1:
        return [], [], 0
    try:
        start_loc = sr.start
        line = sm.getLineNumber(start_loc)
        if line < 1:
            return [], [], 0
        buffer_id = getattr(start_loc, 'buffer', None)
        if buffer_id is None:
            return [], [], line
        full_text = sm.getSourceText(buffer_id)
        if not full_text:
            return [], [], line
        # pyslang 在 in-memory 文本末尾加 \x00, 去掉避免影响 splitlines
        if full_text.endswith('\x00'):
            full_text = full_text[:-1]
        # splitlines() 同时处理 \n 和 \r\n
        file_lines = full_text.splitlines()
        if line > len(file_lines):
            return [], [], line
        # 与 file-based build_evidence 同样的 start/end 计算 (line 1-indexed)
        start = max(0, line - context_window)
        before = [file_lines[i].rstrip() for i in range(start, line - 1)]
        end = min(len(file_lines), line + context_window)
        after = [file_lines[i].rstrip() for i in range(line, end)]
        return before, after, line
    except Exception:
        return [], [], 0


def _find_subexpr_for_signal(syntax_node, signal_name: str):
    """M5.2c step 6: 后序 DFS 找包含 signal_name 的最具体 syntax 子节点

    背景: load trace 的 _syntax_node 注入的是整条 RHS (e.g. 'a + b')。
    验证上没问题 (matches_signal_name=True), 但 snippet 噪声大。
    本函数让 evidence 层 narrowing: 给定 signal_name='a' 返 IdentifierNameSyntax(a),
    'mem[3:0]' 返 IdentifierSelectNameSyntax(mem[3:0])。

    算法: 后序 DFS, 返回 str() 含 signal_name 的节点中 str 最短的 (最具体)。
    平局返回左起第一个 (与 source 顺序一致)。
    防御: Token 节点 (pyslang leaf) 迭代可能崩, 跳过。

    边界:
    - 'a' 在 'a + a' 出现两次 → 返回左起第一个
    - 'mem[3:0]' vs 'bigmem[3:0]' → 子串匹配会误中 (已知限制, TODO M5.3 用 word-boundary)
    - 没有匹配 → 返回原 syntax_node (不退化)
    """
    if syntax_node is None or not signal_name:
        return syntax_node

    def visit(node):
        """返回 (best_node, any_match_in_subtree)"""
        if node is None:
            return None, False
        # Token 没 sourceRange, str() 返回 'Token(X)' 不含 signal_name, 跳过
        node_type = type(node).__name__
        if node_type == 'Token':
            return None, False
        try:
            own_text = str(node).strip()
        except Exception:
            return None, False
        if not own_text or signal_name not in own_text:
            return None, False
        # 自己 match
        best = node
        best_len = len(own_text)
        # 已是最短可能, 不用再递归
        if best_len == len(signal_name):
            return best, True
        # 找子节点更具体的
        try:
            iter_children = list(node)
        except Exception:
            iter_children = []
        for child in iter_children:
            child_best, child_has = visit(child)
            if child_best is not None and child_has:
                try:
                    child_len = len(str(child_best).strip())
                except Exception:
                    continue
                if child_len < best_len:
                    best = child_best
                    best_len = child_len
                    if best_len == len(signal_name):
                        break
        return best, True

    result, _ = visit(syntax_node)
    return result if result is not None else syntax_node

