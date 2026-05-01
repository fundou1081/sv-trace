"""
Parse 模块 - SystemVerilog 代码解析
"""
from .parser import SVParser, get_source_safe
from .extractors import (
    ModuleExtractor,
    SignalExtractor,
    PortAnalyzer,
    InstanceExtractor,
    AlwaysBlockExtractor,
    extract_signals,
    extract_instances,
    extract_always_blocks
)
from .class_utils import ClassExtractor, get_classes
from pyslang_helper import SVParser as PyslangHelperParser, extract_all

__all__ = [
    'SVParser',
    'get_source_safe',
    'ModuleExtractor',
    'SignalExtractor', 
    'PortAnalyzer',
    'InstanceExtractor',
    'AlwaysBlockExtractor',
    'extract_signals',
    'extract_instances',
    'extract_always_blocks',
    'ClassExtractor',
    'get_classes',
    'PyslangHelperParser',
    'extract_all',
]


# =============================================================================
# 扩展语法解析器 - 2026-05-01 添加
# =============================================================================

# Interface/Modport/Clocking 解析器
try:
    from .interface import InterfaceExtractor, extract_interfaces
    __all__.extend(['InterfaceExtractor', 'extract_interfaces'])
except ImportError as e:
    pass

# Package 解析器
try:
    from .package import PackageExtractor, extract_packages
    __all__.extend(['PackageExtractor', 'extract_packages'])
except ImportError as e:
    pass

# Covergroup 解析器  
try:
    from .covergroup import CovergroupExtractor, extract_covergroups
    __all__.extend(['CovergroupExtractor', 'extract_covergroups'])
except ImportError as e:
    pass

# Clocking 解析器
try:
    from .clocking import ClockingExtractor, extract_clockings
    __all__.extend(['ClockingExtractor', 'extract_clockings'])
except ImportError as e:
    pass

# 便捷函数 - 使用 pyslang
try:
    from pyslang_helper import (
        extract_interfaces as extract_interfaces_ast,
        extract_packages as extract_packages_ast,
        extract_covergroups as extract_covergroups_ast,
    )
except ImportError:
    pass
