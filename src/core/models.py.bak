"""Data models for SV tracing"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set, Optional


class DriverKind(Enum):
    """Driver type based on always block kind"""
    Continuous = 0   # assign statement
    AlwaysComb = 1   # always_comb block
    AlwaysFF = 2      # always_ff block
    AlwaysLatch = 3    # always_latch block
    Always = 4         # always block


class AssignKind(Enum):
    """Assignment operator type"""
    Blocking = 0     # = 
    Nonblocking = 1  # <=




@dataclass
class Load:
    """Signal load information (where signal is read)"""
    signal_name: str
    context: str
    line: int = 0
    module: str = ""
    statement_type: str = ""
    condition: str = ""

@dataclass
class Signal:
    """Signal information"""
    name: str
    module: str
    width: int = 1
    is_input: bool = False
    is_output: bool = False
    is_reg: bool = False
    is_wire: bool = False
    is_logic: bool = False


@dataclass
class Driver:
    """Signal driver information"""
    signal: str
    kind: DriverKind
    module: str
    sources: List[str] = field(default_factory=list)
    clock: str = ""
    reset: str = ""
    enable: str = ""
    lines: List[int] = field(default_factory=list)
    assign_kind: AssignKind = AssignKind.Blocking
    condition: str = ""
    # 逻辑深度相关
    operator_count: int = 0  # 运算符数量


@dataclass
class DataFlowPath:
    """Data flow path"""
    source: str
    dest: str
    signals: List[str] = field(default_factory=list)
    logic_depth: int = 0  # 组合逻辑深度（运算符数）
    timing_depth: int = 0  # 时序深度（寄存器数）


@dataclass
class CaseInfo:
    """Case statement information"""
    signal: str
    module: str
    items: List[str] = field(default_factory=list)
    has_default: bool = False


@dataclass
class IfElseInfo:
    """If-else chain information"""
    signal: str
    module: str
    conditions: List[str] = field(default_factory=list)
    branches: int = 0


@dataclass
class TimingPath:
    """时序路径"""
    start_reg: str
    end_reg: str
    timing_depth: int = 0  # 时序深度（寄存器数 - 1）
    logic_depth: int = 0   # 逻辑深度（运算符数）
    signals: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)  # 经过的时钟域


@dataclass
class Register:
    """时序元素信息"""
    name: str
    module: str
    clock: str = ""
    lines: List[int] = field(default_factory=list)


@dataclass
class DomainInfo:
    name: str
    clock: str
    registers: List[str] = field(default_factory=list)


@dataclass
class Parameter:
    """参数信息"""
    name: str
    module: str
    value: str = ""
    width: int = 0


@dataclass
class Connection:
    """Connection between modules"""
    source_module: str
    dest_module: str
    source_signal: str
    dest_signal: str
    port_type: str = ""  # input, output, inout

