"""
Driver - 驱动关系语义类型
"""
from dataclasses import dataclass, field
from typing import List, Optional
import pyslang

from .base import SemanticItem, SemanticKind


@dataclass
class DriverSignal:
    """被驱动的信号"""
    kind: SemanticKind = field(default=SemanticKind.DRIVER_SIGNAL)
    node: pyslang.SyntaxNode = None
    
    signal_path: str = ""           # 信号路径
    width: int = 1                   # 位宽
    
    # 驱动类型
    driver_type: str = ""             # 'reg', 'wire', 'logic'
    
    # 驱动来源
    drivers: List[str] = field(default_factory=list)  # 驱动信号路径列表
    
    module_path: str = ""
    
    @property
    def is_register(self) -> bool:
        return self.driver_type in ('reg', 'dff', 'dffe')
    
    @property
    def is_combinational(self) -> bool:
        return self.driver_type in ('wire', 'logic', 'assign')


@dataclass
class DriverConnection:
    """驱动连接 (边)"""
    kind: SemanticKind = field(default=SemanticKind.DRIVER_CONNECTION)
    node: pyslang.SyntaxNode = None
    
    source: str = ""                  # 驱动源信号路径
    sink: str = ""                   # 被驱动信号路径
    
    # 连接属性
    connection_type: str = ""         # 'blocking', 'nonblocking', 'continuous'
    
    # 位置信息
    line_number: int = 0
    
    # 路径
    module_path: str = ""
    
    @property
    def is_blocking(self) -> bool:
        return self.connection_type == "blocking"
    
    @property
    def is_nonblocking(self) -> bool:
        return self.connection_type == "nonblocking"
    
    @property
    def is_continuous(self) -> bool:
        return self.connection_type == "continuous"
    
    def reverse(self) -> 'DriverConnection':
        """反转连接方向"""
        return DriverConnection(
            source=self.sink,
            sink=self.source,
            connection_type=self.connection_type,
            module_path=self.module_path,
        )


@dataclass
class AssignmentInfo:
    """赋值信息"""
    node: pyslang.SyntaxNode = None
    
    lhs_signal: str = ""              # 左值信号
    rhs_signals: List[str] = field(default_factory=list)  # 右值信号列表
    
    assignment_type: str = ""        # 'blocking', 'nonblocking', 'continuous'
    
    line_number: int = 0
    module_path: str = ""
    
    @property
    def is_concurrent(self) -> bool:
        return self.assignment_type == "continuous"


__all__ = ['DriverSignal', 'DriverConnection', 'AssignmentInfo']
