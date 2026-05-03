"""Query 模块 - SystemVerilog 查询接口。

提供信号、路径、层级等查询功能。

Classes:
    SignalQuery: 统一信号查询接口
    PathQuery: 路径查询
    HierarchyQuery: 层级查询
    HierarchicalResolver: 层级解析器
    CodeExtractor: 代码提取器
    SourceViewer: 源码查看器

Example:
    >>> from query import SignalQuery, PathQuery
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> sq = SignalQuery(parser)
    >>> signal = sq.find_signal("clk")
"""
from .signal import SignalQuery
from .path import PathQuery, HierarchyQuery
from .hierarchy import HierarchicalResolver, CodeExtractor, SourceViewer

__all__ = [
    "SignalQuery",
    "PathQuery", 
    "HierarchyQuery",
    "HierarchicalResolver",
    "CodeExtractor", 
    "SourceViewer",
]
