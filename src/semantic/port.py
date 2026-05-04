"""
Port - 端口信号语义类型
"""
from dataclasses import dataclass, field
from typing import Optional
import pyslang

from .base import SemanticItem, SemanticKind


@dataclass
class PortSignal:
    """端口信号"""
    kind: SemanticKind = field(default=SemanticKind.PORT_SIGNAL)
    node: pyslang.SyntaxNode = None
    
    # 基本信息
    port_name: str = ""               # 端口名
    port_path: str = ""               # 完整路径 (module.port)
    width: int = 1                    # 位宽
    
    # 方向
    direction: str = "input"          # input/output/inout
    
    # 特殊属性
    is_clock: bool = False           # 是否时钟端口
    is_reset: bool = False            # 是否复位端口
    is_enable: bool = False           # 是否使能端口
    
    # 关联信号
    connected_signal: Optional[str] = None  # 连接的内部信号
    
    # 模块路径
    module_path: str = ""
    
    @property
    def is_input(self) -> bool:
        return self.direction == "input"
    
    @property
    def is_output(self) -> bool:
        return self.direction == "output"
    
    def detect_special(self) -> None:
        """检测是否是特殊端口 (clock/reset/enable)"""
        name_lower = self.port_name.lower()
        if 'clk' in name_lower or 'clock' in name_lower:
            self.is_clock = True
        if 'rst' in name_lower or 'reset' in name_lower:
            self.is_reset = True
        if 'en' in name_lower or 'vld' in name_lower or 'ready' in name_lower:
            self.is_enable = True


__all__ = ['PortSignal']
