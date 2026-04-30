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

# 新增 - SystemVerilog 独有语法
from .interface import InterfaceExtractor, InterfaceDef, ModportDef, ClockingDef
from .package import PackageExtractor, PackageDef, ProgramDef
from .generate import GenerateExtractor, GenerateBlock

__all__ = [
    # Core
    "SVParser",
    "ModuleExtractor", 
    "SignalExtractor",
    "PortAnalyzer",
    "ParameterResolver",
    "ClassExtractor",
    "ConstraintExtractor",
    "CovergroupExtractor",
    "AssertionExtractor",
    "get_source_safe",
    "GlobalParseCache",
    "parse_file_cached",
    # 新增 SV 语法
    "InterfaceExtractor",
    "InterfaceDef",
    "ModportDef", 
    "ClockingDef",
    "PackageExtractor",
    "PackageDef",
    "ProgramDef",
    "GenerateExtractor",
    "GenerateBlock",
]
