"""
Signal Items - 信号语义类型

支持的 AST kind:
- VariableDeclarator: logic [7:0] data;
- PortDeclaration: input wire [7:0] data;
- NetDeclaration: wire [7:0] data;
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
    - VariableDeclarator: 变量声明
    - PortDeclaration: 端口声明
    - NetDeclaration: 网络声明
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'VariableDeclarator',
        'PortDeclaration', 
        'NetDeclaration',
    }
    
    # 信号属性
    path: str = ""
    width: int = 1
    kind: str = "wire"  # reg/wire/port/logic
    
    def __post_init__(self):
        if not self.path and self.node:
            self.path = self._extract_path()
    
    def _extract_path(self) -> str:
        """从 AST 提取信号路径"""
        name = ""
        for child in self.node:
            if child.kind.name == 'Identifier':
                name = str(child.value) if hasattr(child, 'value') else str(child)
                break
        return f"{self.module_path}.{name}" if name else ""
    
    @property
    def name(self) -> str:
        """获取信号名"""
        return self.path.split('.')[-1].split('[')[0]
    
    @property
    def is_clock(self) -> bool:
        return 'clk' in self.name.lower() or 'clock' in self.name.lower()
    
    @property
    def is_reset(self) -> bool:
        return 'rst' in self.name.lower() or 'reset' in self.name.lower()


@dataclass
class PortItem(SignalItem):
    """
    端口语义项 - 信号的一种特例
    
    多种 AST 来源:
    - PortDeclaration: input/output/inout 端口
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'PortDeclaration',
    }
    
    direction: str = "input"  # input/output/inout
    is_clock: bool = False
    is_reset: bool = False
    is_enable: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        self._detect_special()
    
    def _detect_special(self) -> None:
        """检测是否是特殊端口"""
        name_lower = self.name.lower()
        if 'clk' in name_lower or 'clock' in name_lower:
            self.is_clock = True
        if 'rst' in name_lower or 'reset' in name_lower:
            self.is_reset = True
        if 'en' in name_lower or 'vld' in name_lower:
            self.is_enable = True
    
    @property
    def is_input(self) -> bool:
        return self.direction == "input"
    
    @property
    def is_output(self) -> bool:
        return self.direction == "output"


__all__ = ['SignalItem', 'PortItem']
