"""Trace Core 模块 - 统一数据模型和基础类

遵循开发纪律:
- 铁律4: 模型即契约
- 铁律6: Schema 即宪法
- 铁律10: API 返回必须有置信度标注

Example:
    >>> from trace.core.base import ASTWalker
    >>> from trace.core.interfaces import TraceResult, Traceable
"""

from .base import ASTWalker, WalkResult
from .interfaces import (
    Traceable,
    TraceResult,
    SignalInfo,
    DriverInfo,
    LoadInfo,
    ConnectionInfo,
)

__all__ = [
    "ASTWalker",
    "WalkResult",
    "Traceable",
    "TraceResult",
    "SignalInfo",
    "DriverInfo",
    "LoadInfo",
    "ConnectionInfo",
]
