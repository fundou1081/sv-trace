"""
Semantic Layer - 语义层 (基于pyslang)

设计原则:
- pyslang 是唯一数据源
- 语义类型 = pyslang 节点 + 业务语义
- 可通过 kind 筛选获得想要的信息
- 降低后续工具开发复杂度
"""

from .base import SemanticItem, SemanticKind, filter_by_kind, filter_by_node_kind
from .clocked import ClockedAlwaysFF, RegisterSignal, ClockDomain
from .port import PortSignal
from .fsm import FSMState, FSMTransition, FSMBlock
from .driver import DriverSignal, DriverConnection, AssignmentInfo
from .load import LoadSignal, LoadConnection
from .reset import ResetSignal, ResetDomain
from .builder import SemanticCollector, build_semantic

__all__ = [
    # 基类
    'SemanticItem',
    'SemanticKind',
    'filter_by_kind',
    'filter_by_node_kind',
    
    # 时钟相关
    'ClockedAlwaysFF',
    'RegisterSignal', 
    'ClockDomain',
    
    # 端口
    'PortSignal',
    
    # FSM
    'FSMState',
    'FSMTransition', 
    'FSMBlock',
    
    # 驱动/负载
    'DriverSignal',
    'DriverConnection',
    'AssignmentInfo',
    'LoadSignal',
    'LoadConnection',
    
    # 复位
    'ResetSignal',
    'ResetDomain',
    
    # 构建器
    'SemanticCollector',
    'build_semantic',
]

