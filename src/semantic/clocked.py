"""
Clocked - 时钟域相关语义类型
"""
from dataclasses import dataclass, field
from typing import Optional, List
import pyslang

from .base import SemanticItem, SemanticKind


@dataclass
class ClockDomain:
    """时钟域"""
    name: str                           # 时钟域名
    clock_signal: str                   # 时钟信号路径
    reset_signal: Optional[str] = None  # 复位信号路径 (可选)
    is_async: bool = False              # 是否异步复位
    
    # 包含的寄存器
    registers: List[str] = field(default_factory=list)  # 寄存器信号路径列表


@dataclass
class RegisterSignal:
    """寄存器信号"""
    kind: SemanticKind = field(default=SemanticKind.REGISTER_SIGNAL)
    node: pyslang.SyntaxNode = None
    
    signal_path: str = ""              # 信号路径
    width: int = 1                     # 位宽
    
    # 时钟域关联
    clock_domain: Optional[str] = None  # 时钟域名
    clock_signal: Optional[str] = None   # 时钟信号路径
    
    # 复位关联
    reset_signal: Optional[str] = None
    reset_value: Optional[int] = None   # 复位值
    
    # 所在模块
    module_path: str = ""
    
    @property
    def is_clock_gated(self) -> bool:
        """是否门控时钟"""
        return 'gated' in self.signal_path.lower()
    
    @property
    def is_async_reset(self) -> bool:
        """是否异步复位"""
        return self.reset_signal is not None


@dataclass
class ClockedAlwaysFF:
    """时序 always_ff 块"""
    kind: SemanticKind = field(default=SemanticKind.CLOCKED_ALWAYS_FF)
    node: pyslang.SyntaxNode = None
    
    # 基本信息
    block_path: str = ""              # 块路径 (module.block)
    line_number: int = 0
    
    # 时钟信息
    clock_signal: str = ""             # 时钟信号路径
    clock_edge: str = "posedge"        # 时钟边沿 (posedge/negedge)
    
    # 复位信息
    reset_signal: Optional[str] = None  # 复位信号路径
    reset_edge: str = "negedge"        # 复位边沿
    is_async_reset: bool = False       # 是否异步
    
    # 包含的寄存器
    registers: List[str] = field(default_factory=list)  # 寄存器信号路径
    
    # 时钟域
    clock_domain: Optional[str] = None  # 关联的时钟域名
    
    # 模块路径
    module_path: str = ""
    
    def get_clock_domain(self) -> ClockDomain:
        """获取关联的时钟域"""
        return ClockDomain(
            name=self.clock_domain or f"domain_{self.clock_signal}",
            clock_signal=self.clock_signal,
            reset_signal=self.reset_signal,
            is_async=self.is_async_reset,
            registers=self.registers,
        )
    
    def to_register_signals(self) -> List[RegisterSignal]:
        """转换为寄存器信号列表"""
        return [
            RegisterSignal(
                signal_path=reg_path,
                clock_signal=self.clock_signal,
                clock_domain=self.clock_domain,
                reset_signal=self.reset_signal,
                module_path=self.module_path,
            )
            for reg_path in self.registers
        ]


__all__ = ['ClockDomain', 'RegisterSignal', 'ClockedAlwaysFF']
