"""
Reset Items - 复位语义类型
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List, Optional
import pyslang

from .base import SemanticItem


@dataclass
class ResetSignalItem(SemanticItem):
    """
    复位信号
    
    AST: ImplicitAnsiPort (reset 端口)
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'ImplicitAnsiPort',
    }
    
    signal_path: str = ""
    polarity: str = "low"
    is_async: bool = True
    
    affected_registers: List[str] = field(default_factory=list)


@dataclass
class ResetDomainItem(SemanticItem):
    """
    复位域
    
    AST: AlwaysFFBlock (包含复位信息)
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'AlwaysFFBlock',
    }
    
    reset_signal: str = ""
    polarity: str = "low"
    is_async: bool = True
    
    registers: List[str] = field(default_factory=list)


__all__ = ['ResetSignalItem', 'ResetDomainItem']
