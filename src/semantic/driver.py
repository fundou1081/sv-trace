"""
Driver Items - 驱动关系语义类型

支持的 AST kind:
- NonBlockingAssignmentStatement: data <= next; (always_ff)
- BlockingAssignmentStatement: data = next; (always_comb/always)
- ContinuousAssignmentStatement: assign data = next; (assign)
- ProceduralContinuousAssign: force data = next; (force 语句)
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List
import pyslang

from .base import SemanticItem


@dataclass
class DriverSignal(SemanticItem):
    """
    被驱动的信号语义项
    
    多种 AST 来源:
    - NonBlockingAssignmentStatement (左值)
    - BlockingAssignmentStatement (左值)
    - ContinuousAssignmentStatement (左值)
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'NonBlockingAssignmentStatement',
        'BlockingAssignmentStatement',
        'ContinuousAssignmentStatement',
        'ProceduralContinuousAssign',
    }
    
    signal_path: str = ""
    width: int = 1
    
    @property
    def is_nonblocking(self) -> bool:
        return self.kind_name == 'NonBlockingAssignmentStatement'
    
    @property
    def is_blocking(self) -> bool:
        return self.kind_name in ('BlockingAssignmentStatement', 'ContinuousAssignmentStatement')


@dataclass
class NonBlockingAssign(SemanticItem):
    """
    非阻塞赋值 (always_ff 内)
    
    AST 来源: NonBlockingAssignmentStatement
    
    Example: data <= next_data;
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'NonBlockingAssignmentStatement',
    }
    
    # 赋值信息
    lhs: str = ""           # 左值信号
    rhs: List[str] = field(default_factory=list)  # 右值信号列表
    
    # 时钟/复位上下文
    clock_signal: str = ""
    reset_signal: str = ""
    is_async_reset: bool = False
    
    def _extract_lhs(self) -> str:
        """提取左值"""
        for child in self.node:
            ckn = child.kind.name
            if 'Left' in ckn or 'Target' in ckn:
                for sub in child:
                    if sub.kind.name == 'Identifier':
                        return str(sub.value) if hasattr(sub, 'value') else str(sub)
        return ""
    
    @property
    def is_sequential(self) -> bool:
        return True


@dataclass
class BlockingAssign(SemanticItem):
    """
    阻塞赋值 (always_comb/always 内)
    
    AST 来源: BlockingAssignmentStatement
    
    Example: data = next_data;
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'BlockingAssignmentStatement',
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
    
    AST 来源: ContinuousAssignmentStatement
    
    Example: assign data = next_data;
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'ContinuousAssignmentStatement',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)
    
    @property
    def is_wire(self) -> bool:
        return True


__all__ = ['DriverSignal', 'NonBlockingAssign', 'BlockingAssign', 'ContinuousAssign']
