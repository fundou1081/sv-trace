"""Extractors - 纯 AST 遍历的语义提取器

符合铁律 18-20:
- 使用 pyslang.visit() 遍历
- 接收 ScopeTree 作为构造参数
- 输出结果写入 SemanticGraph
"""

from extractors.base import (
    Extractor,
    SemanticGraph,
    LoadPoint,
    DriverPoint,
    Connection,
)
from extractors.load import LoadExtractor
from extractors.driver import DriverExtractor
from extractors.connection import ConnectionExtractor

__all__ = [
    'Extractor',
    'SemanticGraph',
    'LoadPoint',
    'DriverPoint',
    'Connection',
    'LoadExtractor',
    'DriverExtractor',
    'ConnectionExtractor',
]
