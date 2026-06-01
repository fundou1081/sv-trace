"""signal_tracer.models - 数据模型

定义信号追踪的结果数据结构。
"""

from dataclasses import dataclass, field
from typing import List, Optional
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