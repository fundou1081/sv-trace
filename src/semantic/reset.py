"""
Reset - 复位相关语义类型
"""
from dataclasses import dataclass, field
from typing import List, Optional
import pyslang

from .base import SemanticItem, SemanticKind


@dataclass
class ResetSignal:
    """复位信号"""
    kind: SemanticKind = field(default=SemanticKind.RESET_SIGNAL)
    node: pyslang.SyntaxNode = None
    
    signal_path: str = ""            # 信号路径
    width: int = 1                    # 位宽
    
    # 复位类型
    reset_type: str = ""              # 'sync', 'async'
    polarity: str = "low"             # 'high', 'low'
    
    # 被此复位影响的寄存器
    affected_registers: List[str] = field(default_factory=list)
    
    module_path: str = ""
    
    @property
    def is_sync(self) -> bool:
        return self.reset_type == "sync"
    
    @property
    def is_async(self) -> bool:
        return self.reset_type == "async"
    
    @property
    def fan_out(self) -> int:
        """扇出"""
        return len(self.affected_registers)


@dataclass
class ResetDomain:
    """复位域"""
    name: str = ""                    # 域名
    reset_signal: str = ""           # 复位信号路径
    
    # 复位类型
    reset_type: str = "sync"         # sync/async
    polarity: str = "low"             # high/low
    
    # 包含的寄存器
    registers: List[str] = field(default_factory=list)
    
    # 时钟域关联
    clock_domain: Optional[str] = None
    
    def add_register(self, reg_path: str) -> None:
        if reg_path not in self.registers:
            self.registers.append(reg_path)
    
    @property
    def register_count(self) -> int:
        return len(self.registers)


__all__ = ['ResetSignal', 'ResetDomain']
