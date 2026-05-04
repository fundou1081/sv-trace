"""
Clock Domain Items - 时钟域语义类型

实际 pyslang kind:
- AlwaysFFBlock: always_ff 块
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List, Optional
import pyslang

from .base import SemanticItem


@dataclass
class ClockDomainItem(SemanticItem):
    """
    时钟域
    
    AST: AlwaysFFBlock
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'AlwaysFFBlock',
    }
    
    clock_signal: str = ""
    clock_edge: str = "posedge"
    reset_signal: Optional[str] = None
    is_async_reset: bool = False
    
    registers: List[str] = field(default_factory=list)


@dataclass
class RegisterItem(SemanticItem):
    """
    寄存器项
    
    多种 AST 来源:
    - Declarator: 变量声明
    - NonblockingAssignmentExpression: 非阻塞赋值左值
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'Declarator',
        'NonblockingAssignmentExpression',
    }
    
    signal_path: str = ""
    width: int = 1
    
    @property
    def is_register(self) -> bool:
        return True


__all__ = ['ClockDomainItem', 'RegisterItem']
