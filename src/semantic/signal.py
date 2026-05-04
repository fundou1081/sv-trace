"""
Signal Items - 信号语义类型

实际的 pyslang kind:
- Declarator: 变量声明 (logic [7:0] data;)
- ImplicitAnsiPort: ANSI 端口声明 (input clk, output [7:0] data)
"""

from dataclasses import dataclass
from typing import Set, ClassVar
import pyslang

from .base import SemanticItem


@dataclass
class SignalItem(SemanticItem):
    """
    信号语义项
    
    多种 AST 来源:
    - Declarator: 变量声明 (logic [7:0] data;)
    - ImplicitAnsiPort: 端口声明
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'Declarator',
        'ImplicitAnsiPort',
    }
    
    path: str = ""
    width: int = 1
    kind: str = "wire"
    
    def _extract_path(self) -> str:
        """从 AST 提取信号路径"""
        name = ""
        for child in self.node:
            kn = child.kind.name
            if kn == 'Identifier':
                name = str(child.value) if hasattr(child, 'value') else str(child)
                break
        return f"{self.module_path}.{name}" if name else ""
    
    @property
    def name(self) -> str:
        return self.path.split('.')[-1].split('[')[0]
    
    @property
    def is_clock(self) -> bool:
        n = self.name.lower()
        return 'clk' in n or 'clock' in n
    
    @property
    def is_reset(self) -> bool:
        n = self.name.lower()
        return 'rst' in n or 'reset' in n


@dataclass
class PortItem(SignalItem):
    """
    端口语义项
    
    AST: ImplicitAnsiPort
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'ImplicitAnsiPort',
    }
    
    direction: str = "input"
    is_clock: bool = False
    is_reset: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        self._detect_special()
    
    def _detect_special(self) -> None:
        n = self.name.lower()
        self.is_clock = 'clk' in n or 'clock' in n
        self.is_reset = 'rst' in n or 'reset' in n
    
    @property
    def is_input(self) -> bool:
        return self.direction == "input"


__all__ = ['SignalItem', 'PortItem']
