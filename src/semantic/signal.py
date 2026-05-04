"""
Signal Node - 信号节点
"""
from dataclasses import dataclass
from typing import Optional, List


class PortDirection:
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"
    INTERNAL = "internal"


@dataclass(frozen=True)
class SignalNode:
    """不可变信号节点"""
    full_path: str           # "top.mod_a.data[7:0]"
    width: int               # 位宽 (1 for single bit, 0 for scalar)
    
    # 定义字段 (冻结对象可hash)
    kind: str               # 'reg', 'wire', 'port', 'logic', 'parameter'
    direction: str          # PortDirection
    clock_domain: Optional[str] = None
    reset_domain: Optional[str] = None
    
    # 驱动关系
    drivers: tuple[str, ...] = ()   # 源信号路径 (frozen tuple)
    loads: tuple[str, ...] = ()     # 负载信号路径 (frozen tuple)
    
    # 模块位置
    module_path: str = ""           # "top.mod_a"
    
    def __hash__(self):
        return hash(self.full_path)
    
    def __eq__(self, other):
        if not isinstance(other, SignalNode):
            return False
        return self.full_path == other.full_path
    
    @property
    def name(self) -> str:
        """获取信号名"""
        return self.full_path.split('.')[-1].split('[')[0]
    
    @property
    def is_clock(self) -> bool:
        return 'clk' in self.full_path.lower()
    
    @property
    def is_reset(self) -> bool:
        return 'rst' in self.full_path.lower()


@dataclass(frozen=True)
class SignalSlice:
    """信号切片"""
    source_path: str         # 原始信号路径
    slice_range: tuple[int, int]  # (msb, lsb)
    parent: str             # 父节点全路径


@dataclass(frozen=True)
class SignalConcat:
    """信号拼接"""
    paths: tuple[str, ...]  # 拼接的信号路径


__all__ = ['SignalNode', 'PortDirection', 'SignalSlice', 'SignalConcat']
