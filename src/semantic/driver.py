"""
Driver Items - 驱动关系语义类型

实际的 pyslang kind 名称:
- ContinuousAssign: assign 语句
- NonblockingAssignmentExpression: <= 赋值
- AssignmentExpression: = 赋值
- EventControlWithExpression: @(posedge clk)
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List
import pyslang

from .base import SemanticItem


@dataclass
class DriverSignal(SemanticItem):
    """
    被驱动的信号 - 语义类型
    
    多种 AST 来源:
    - NonblockingAssignmentExpression (左值)
    - AssignmentExpression (左值)
    - ContinuousAssign (左值)
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'NonblockingAssignmentExpression',
        'AssignmentExpression',
        'ContinuousAssign',
    }
    
    signal_path: str = ""
    width: int = 1
    
    @property
    def is_nonblocking(self) -> bool:
        return self.kind_name == 'NonblockingAssignmentExpression'
    
    @property
    def is_blocking(self) -> bool:
        return self.kind_name == 'AssignmentExpression'
    
    @property
    def is_continuous(self) -> bool:
        return self.kind_name == 'ContinuousAssign'


@dataclass
class NonBlockingAssign(SemanticItem):
    """
    非阻塞赋值 (always_ff 内)
    
    AST: NonblockingAssignmentExpression
    Example: data <= next_data;
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'NonblockingAssignmentExpression',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)
    clock_signal: str = ""
    
    @property
    def is_sequential(self) -> bool:
        return True


@dataclass
class BlockingAssign(SemanticItem):
    """
    阻塞赋值 (always_comb/always 内)
    
    AST: AssignmentExpression
    Example: data = next_data;
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'AssignmentExpression',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)
    
    @property
    def is_combinational(self) -> bool:
        return True


@dataclass
class ContinuousAssign(SemanticItem):
    """
    连续赋值 (assign 语句)
    
    AST: ContinuousAssign
    Example: assign data = next_data;
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'ContinuousAssign',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)
    
    @property
    def is_wire(self) -> bool:
        return True


__all__ = ['DriverSignal', 'NonBlockingAssign', 'BlockingAssign', 'ContinuousAssign']
