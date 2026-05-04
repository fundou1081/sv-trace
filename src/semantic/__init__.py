"""
Semantic Layer - 语义层 (基于pyslang)

设计原则:
- pyslang 是唯一数据源
- 语义类型 = pyslang 节点 + 业务语义
- 每种语义通过 SUPPORTED_KINDS 声明支持的 AST 类型
- 可扩展：新增语义类型无需修改收集器
"""

from .base import SemanticItem, SemanticCollector

# 通用语义
from .signal import SignalItem, PortItem

# Driver 工具专用
from .driver import DriverSignal, NonBlockingAssign, BlockingAssign, ContinuousAssign

# FSM 工具专用
from .fsm import FSMStateItem, FSMTransitionItem

# Clock Domain 工具专用
from .clock import ClockDomainItem, RegisterItem

# Reset 工具专用
from .reset import ResetSignalItem

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
    'ResetSignalItem',
]

