"""
Parse 模块 - SystemVerilog 代码解析
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

# 新增 - SV 独有语法
from .interface import InterfaceExtractor, InterfaceDef, ModportDef, ClockingDef
from .package import PackageExtractor, PackageDef, ProgramDef, PackageItem
from .generate import GenerateExtractor, GenerateBlock, GenerateItem

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
    # SV 独有语法
    "InterfaceExtractor",
    "InterfaceDef",
    "ModportDef", 
    "ClockingDef",
    "PackageExtractor",
    "PackageDef",
    "ProgramDef",
    "PackageItem",
    "GenerateExtractor",
    "GenerateBlock",
    "GenerateItem",
]
