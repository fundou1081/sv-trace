"""
Load - 负载信号语义类型
"""
from dataclasses import dataclass, field
from typing import List, Optional
import pyslang

from .base import SemanticItem, SemanticKind


@dataclass
class LoadSignal:
    """被负载的信号 (驱动目标)"""
    kind: SemanticKind = field(default=SemanticKind.LOAD_SIGNAL)
    node: pyslang.SyntaxNode = None
    
    signal_path: str = ""            # 信号路径
    width: int = 1                    # 位宽
    
    # 负载类型
    load_type: str = ""              # 'input', 'port', 'reg', 'wire'
    
    # 驱动来源 (反向 - 从驱动角度看负载)
    driven_by: List[str] = field(default_factory=list)  # 驱动此信号的信号路径
    
    module_path: str = ""
    
    @property
    def fan_out(self) -> int:
        """扇出数量"""
        return len(self.driven_by)
    
    def get_driver_signals(self) -> List[str]:
        """获取所有驱动信号"""
        return list(self.driven_by)


@dataclass
class LoadConnection:
    """负载连接"""
    source: str = ""                  # 被负载的信号
    sinks: List[str] = field(default_factory=list)  # 负载列表
    
    connection_type: str = ""
    module_path: str = ""


__all__ = ['LoadSignal', 'LoadConnection']
