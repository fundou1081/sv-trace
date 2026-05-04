"""
Reset Items - 复位语义类型

支持的 AST kind:
- AlwaysFFBlock: always_ff 块 (包含复位信息)
- VariableDeclarator: 被复位的寄存器
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List, Optional
import pyslang

from .base import SemanticItem


@dataclass
class ResetSignalItem(SemanticItem):
    """
    复位信号
    
    AST 来源:
    - PortDeclaration: reset 端口
    - VariableDeclarator: 复位信号变量
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'PortDeclaration',
        'VariableDeclarator',
    }
    
    signal_path: str = ""
    polarity: str = "low"  # high/low
    is_async: bool = True
    
    affected_registers: List[str] = field(default_factory=list)
    
    def _detect_reset(self) -> None:
        """检测是否是复位信号"""
        name_lower = self.signal_path.lower()
        if 'rst' in name_lower or 'reset' in name_lower:
            self.signal_path = self.signal_path


@dataclass
class ResetDomainItem(SemanticItem):
    """
    复位域
    
    AST 来源: AlwaysFFBlock (包含复位信息)
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'AlwaysFFBlock',
    }
    
    reset_signal: str = ""
    polarity: str = "low"
    is_async: bool = True
    clock_domain: Optional[str] = None
    
    registers: List[str] = field(default_factory=list)


__all__ = ['ResetSignalItem', 'ResetDomainItem']
