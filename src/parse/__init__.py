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

# Backward compatibility stubs (铁律8)
# 这些类在旧版本中存在但尚未迁移到新架构
try:
    from .class_utils import ClassExtractor
    
    class ParameterResolver:
        """参数解析器 (stub)"""
        def __init__(self, parser=None):
            self.parser = parser
        def resolve(self, param_name):
            return None
    
    class ConstraintExtractor:
        """约束提取器 (stub)"""
        def __init__(self):
            pass
        def extract(self, tree):
            return []
    
    class AssertionExtractor:
        """断言提取器 (stub)"""
        def __init__(self):
            pass
        def extract(self, tree):
            return []
    
    __all__.extend(['ParameterResolver', 'ConstraintExtractor', 'AssertionExtractor'])
except ImportError:
    pass
