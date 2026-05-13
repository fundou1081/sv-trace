"""Semantic Base - 兼容层

⚠️ 已废弃：使用 extractors/base.py 替代

本文件作为兼容层，将旧的 SemanticCollector API 桥接到新的 extractors 架构。

符合铁律 21: 此模块内部调用 extractors，不直接遍历 AST。
"""

import warnings as _warnings

# 重新导出 extractors 的类型（保持向后兼容）
from extractors.base import (
    SemanticGraph,
    LoadPoint,
    DriverPoint,
    Connection,
    Extractor,
    ConfidenceLevel,
)

# 旧的类名作为别名
SemanticCollector = None  # 类型标注用，不可用
LoadItem = LoadPoint
DriverItem = DriverPoint

# 警告
__all__ = [
    'SemanticGraph',
    'LoadPoint',
    'DriverPoint',
    'Connection',
    'Extractor',
    'ConfidenceLevel',
    'SemanticCollector',
    'LoadItem',
    'DriverItem',
]
