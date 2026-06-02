from __future__ import annotations
"""signal_tracer.models - 数据模型

定义信号追踪的结果数据结构。
"""

from dataclasses import dataclass, field
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
    
    def __repr__(self) -> str:
        direction = "<=" if self.trace_type == TraceType.DRIVER else "->"
        return f"TraceResult({self.signal_name} {direction} {self.source_expr!r}@{self.line})"

    def to_context(self, file_content: Optional[str] = None, context_window: int = 2) -> 'ContextBundle':
        """把自己打包成 ContextBundle (M5.1: 含 code evidence)

        用于 agent 一次性拿到 trace 的所有上下文 (file/line/scope/clock/reset/cond_stack/port)
        + 代码证据链 (读回 file:line, 验证 source_expr / signal_name 是否真的在该行)。

        Args:
            file_content: 可选, 直接传文件内容避免 I/O (用于测试)
            context_window: 前后各取几行作为上下文 (默认 2)

        Returns:
            ContextBundle 实例, 含 code_evidence 字段
        """
        from signal_tracer.models import ContextBundle, build_evidence

        # M5.1: 如果 SignalTracer.trace_verified 预先注入了 evidence, 优先用
        evidence = getattr(self, '_evidence_override', None)
        if evidence is None:
            # 否则自动构建
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
    
    def get_driver_chain(self, max_depth: int = 10) -> List[str]:
        """获取驱动链 (从输入到输出)"""
        chain = []
        visited = set()
        
        def build_chain(sig_name: str, depth: int):
            if depth > max_depth or sig_name in visited:
                return
            visited.add(sig_name)
            
            # 找到这个信号的驱动源
            for d in self.drivers:
                if d.signal_name == sig_name:
                    for src in d.source_signals:
                        if src and src not in ('0', '1', 'true', 'false'):
                            chain.append(src)
                            build_chain(src, depth + 1)
        
        build_chain(self.signal_name, 0)
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

    @property
    def is_verified(self) -> bool:
        """是否交叉验证通过

        "代码召回"成功的定义:
        - 文件可读
        - line 实际存在
        - 该行真的包含 source_expr 或 signal_name
        """
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
        return '\n'.join(lines)


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
