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

    def to_context(self) -> 'ContextBundle':
        """把自己打包成 ContextBundle

        用于 agent 一次性拿到 trace 的所有上下文 (file/line/scope/clock/reset/cond_stack/port)。
        返回的 ContextBundle 是 frozen 的, 可以安全地传给 LLM 或序列化。

        Returns:
            ContextBundle 实例
        """
        from signal_tracer.models import ContextBundle
        return ContextBundle(
            file=self.file,
            line=self.line,
            char_offset=self.char_offset,
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

    def to_contexts(self) -> List['ContextBundle']:
        """把这次 trace 的所有 driver 打包为 ContextBundle 列表

        agent 拿到一个 List[ContextBundle] 可以一次性看到所有 driver 上下文,
        不必自己遍历 drivers 列表逐个 to_context()。

        Returns:
            List[ContextBundle], 顺序与 self.drivers 一致
        """
        return [d.to_context() for d in self.drivers]
    
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

    def to_dict(self) -> dict:
        """转为 dict 便于 JSON 序列化"""
        return {
            'file': self.file,
            'line': self.line,
            'char_offset': self.char_offset,
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