"""Semantic Layer - 语义层 (基于pyslang)

按项目纪律：
- 每种语义通过 SUPPORTED_KINDS 声明
- __post_init__ 提取具体信息
- confidence 标注
"""

from .base import SemanticItem, SemanticCollector
from .utils import extract_identifier

# 信号/端口
from .signal import SignalItem, PortItem, RegisterItem

# 驱动
from .driver import DriverSignal, NonBlockingAssign, BlockingAssign, ContinuousAssign

# 时钟域
from .clock import ClockDomainItem, RegisterItem as ClockRegisterItem

# FSM
from .fsm import FSMStateItem, FSMTransitionItem

__all__ = [
    # Base
    'SemanticItem',
    'SemanticCollector',
    # Signal
    'SignalItem',
    'PortItem', 
    'RegisterItem',
    # Driver
    'DriverSignal',
    'NonBlockingAssign',
    'BlockingAssign',
    'ContinuousAssign',
    # Clock
    'ClockDomainItem',
    # FSM
    'FSMStateItem',
    'FSMTransitionItem',
]
