"""
Parse 模块 - 解析 SystemVerilog 代码
"""
from .parser import SVParser, get_source_safe, GlobalParseCache, parse_file_cached
from .extractors import (
    ModuleExtractor,
    SignalExtractor,
    PortAnalyzer,
)
from .params import ParameterResolver
from .class_utils import ClassExtractor
from .constraint import ConstraintExtractor
from .covergroup import CovergroupExtractor
from .assertion import AssertionExtractor

__all__ = [
    "SVParser",
    "ModuleExtractor", 
    "SignalExtractor",
    "PortAnalyzer",
    "ParameterResolver",
    "ClassExtractor",
    "ConstraintExtractor",
    "CovergroupExtractor",
    "AssertionExtractor",
    # 新增
    "get_source_safe",
    "GlobalParseCache",
    "parse_file_cached",
]
