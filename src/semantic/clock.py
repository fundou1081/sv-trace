"""
Clock Domain Items - 时钟域语义类型

支持的 AST kind:
- AlwaysFFBlock: always_ff 块 (包含时钟信息)
- VariableDeclarator: 寄存器变量 (在 always_ff 内声明)
- EventControl: 时钟事件 @(posedge clk)
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List, Optional
import pyslang

from .base import SemanticItem


@dataclass
class ClockDomainItem(SemanticItem):
    """
    时钟域
    
    AST 来源: AlwaysFFBlock
    
    代表一个时钟域，包含时钟信号、复位信号、寄存器列表
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'AlwaysFFBlock',
    }
    
    clock_signal: str = ""
    clock_edge: str = "posedge"  # posedge/negedge
    
    reset_signal: Optional[str] = None
    reset_polarity: str = "low"
    is_async_reset: bool = False
    
    registers: List[str] = field(default_factory=list)


@dataclass
class RegisterItem(SemanticItem):
    """
    寄存器项
    
    多种 AST 来源:
    - VariableDeclarator: 寄存器变量 (logic [7:0] data;)
    - NonBlockingAssignmentStatement 左值: 寄存器赋值 data <= next;
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'VariableDeclarator',
        'NonBlockingAssignmentStatement',
    }
    
    signal_path: str = ""
    width: int = 1
    
    clock_domain: Optional[str] = None
    clock_signal: Optional[str] = None
    reset_signal: Optional[str] = None
    
    @property
    def is_register(self) -> bool:
        return True


__all__ = ['ClockDomainItem', 'RegisterItem']
