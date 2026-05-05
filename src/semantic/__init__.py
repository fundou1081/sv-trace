"""
Semantic Layer - 语义层 (基于pyslang)

按项目纪律：
- 每种语义通过 SUPPORTED_KINDS 声明
- __post_init__ 提取具体信息
"""

from .base import SemanticItem, SemanticCollector
from .signal import SignalItem, PortItem
from .driver import DriverSignal, NonBlockingAssign, BlockingAssign, ContinuousAssign
from .fsm import FSMStateItem, FSMTransitionItem
from .clock import ClockDomainItem, RegisterItem, ClockSignalItem, ResetSignalItem
from .reset import ResetSignalItem as RstItem

__all__ = [
    'SemanticItem',
    'SemanticCollector',
    'SignalItem',
    'PortItem',
    'DriverSignal',
    'NonBlockingAssign',
    'BlockingAssign',
    'ContinuousAssign',
    'FSMStateItem',
    'FSMTransitionItem',
    'ClockDomainItem',
    'RegisterItem',
    'ClockSignalItem',
    'ResetSignalItem',
]
