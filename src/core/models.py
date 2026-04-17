"""
核心数据模型
定义信号、驱动、加载等基础数据结构
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List
from dataclasses import dataclass


class SignalType(Enum):
    """信号类型"""
    LOGIC = auto()
    WIRE = auto()
    REG = auto()
    INT = auto()
    UINT = auto()
    REAL = auto()
    STRING = auto()
    UNKNOWN = auto()


class DriverKind(Enum):
    """驱动类型"""
    ASSIGN = auto()          # assign 语句
    ALWAYS_FF = auto()      # always_ff 块
    ALWAYS_COMB = auto()    # always_comb 块
    ALWAYS_LATCH = auto()   # always_latch 块
    INITIAL = auto()        # initial 块
    MODULE_INST = auto()     # 模块实例输出


class ConnectionKind(Enum):
    """连接类型"""
    PORT = auto()           # 端口连接
    WIRE = auto()          # 线连接
    INTERFACE = auto()      # 接口连接


@dataclass
class Signal:
    """信号定义"""
    name: str
    signal_type: SignalType = SignalType.LOGIC
    width: int = 1         # 位宽
    signed: bool = False
    constant: bool = False   # const
    array_dims: List[int] = field(default_factory=list)  # 数组维度
    lifetime: str = "static"  # "static" or "automatic"
    
    # 位置信息
    file: str = ""
    line: int = 0
    
    def __str__(self):
        suffix = f"[{self.width-1}:0]" if self.width > 1 else ""
        sign = "signed " if self.signed else ""
        return f"{sign}{self.signal_type.name.lower()} {self.name}{suffix}"


@dataclass
class Driver:
    """信号驱动源"""
    signal_name: str
    driver_kind: DriverKind
    source_expr: str = ""      # 驱动表达式
    
    # 位置
    file: str = ""
    line: int = 0
    
    # 时序信息
    clock_edge: str = ""       # "posedge" / "negedge"
    clock_signal: str = ""
    level_sensitive: bool = False
    
    def __str__(self):
        return f"{self.driver_kind.name}: {self.source_expr}"


@dataclass
class Load:
    """信号加载点"""
    signal_name: str
    context: str = ""         # 使用的上下文
    
    file: str = ""
    line: int = 0
    
    def __str__(self):
        return f"Load: {self.signal_name} @ {self.file}:{self.line}"


@dataclass
class Connection:
    """信号连接关系"""
    src_signal: str          # 源信号
    dst_signal: str          # 目标信号
    conn_kind: ConnectionKind = ConnectionKind.PORT
    
    # 实例信息
    inst_name: str = ""
    port_name: str = ""
    
    def __str__(self):
        return f"{self.src_signal} -> {self.dst_signal}"


@dataclass 
class Parameter:
    """参数定义"""
    name: str
    value: str = ""          # 原始值字符串
    
    # 展开后的值
    resolved_value: Optional[int] = None
    
    # 类型
    is_localparam: bool = False
    data_type: str = "logic"
    
    file: str = ""
    line: int = 0
    
    def __str__(self):
        return f"parameter {self.name} = {self.value}"
