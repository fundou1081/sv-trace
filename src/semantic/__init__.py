"""
Semantic Graph - 中间语义层

将 pyslang AST 转换为可操作的语义图

设计原则:
- 无 pyslang 类型引用
- 只使用简单数据类型
- frozen=True (不可变) 确保可缓存
- 纯数据可序列化 (JSON/YAML)
"""

from .signal import SignalNode, PortDirection
from .connection import ConnectionEdge
from .graph import SemanticGraph
from .builder import SemanticBuilder
from .elaboration import ElabSignal, ElabDesign, ElabInstance

__all__ = [
    'SignalNode',
    'PortDirection', 
    'ConnectionEdge',
    'SemanticGraph',
    'SemanticBuilder',
    'ElabSignal',
    'ElabDesign',
    'ElabInstance',
]

