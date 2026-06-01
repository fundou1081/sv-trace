"""Semantic - 语义增强层

消费 extractors/ 输出的 SemanticGraph，提供语义增强。

符合铁律 21: Semantic 层不得直接遍历 AST
符合铁律 22: Enricher 必须标注 confidence 和 caveats

迁移说明:
- 原有的 SUPPORTED_KINDS + __post_init__ 模式已废弃
- 功能已迁移到 extractors/ 和 semantic/enricher.py
- semantic/base.py, semantic/driver.py 等仍可导入（会警告），
  内部重定向到新架构
"""

# ============================================================
# 新增: 语义增强层 (Phase 2)
# ============================================================
from semantic.models import (
    EnrichedSignal,
    EnrichedSemanticGraph,
    EnrichedLoadPoint,
    EnrichedDriverPoint,
)

from semantic.enricher import SemanticEnricher
from semantic.agent_interface import AgentContext

# ============================================================
# 兼容层: 重导出 extractors 的类型
# ============================================================
from extractors.base import (
    SemanticGraph,
    Extractor,
    LoadPoint,
    DriverPoint,
    Connection,
    ConfidenceLevel,
)

# ============================================================
# 废弃声明 (仍可导入，但会警告)
# ============================================================
import warnings as _warnings

_deprecated_modules = {
    'base': '使用 extractors.base',
    'driver': '使用 extractors.driver',
    'load': '使用 extractors.load',
    'clock': '使用 extractors.clock',
    'reset': '使用 extractors.reset',
    'connection': '使用 extractors.connection',
    'signal': '使用 extractors.signal',
    'fsm': '使用 extractors.fsm',
    'utils': '使用 scope.utils',
}

_deprecated_items = {
    'SemanticCollector': 'SemanticCollector 已废弃，使用 trace/driver.py 的 DriverCollector',
    'DriverCollector': '使用 trace/driver.py',
}

def __getattr__(name):
    # 兼容层导出
    if name in ('SemanticCollector', 'DriverCollector'):
        _warnings.warn(
            f"semantic.{name} 已废弃。 {_deprecated_items.get(name, '')}",
            DeprecationWarning,
            stacklevel=2
        )
        # 返回一个代理对象
        return type(name, (), {
            '__deprecated__': True,
            '__doc__': f'{name} 已废弃',
        })
    
    if name in _deprecated_modules:
        _warnings.warn(
            f"semantic.{name} 已废弃。 {_deprecated_modules[name]}",
            DeprecationWarning,
            stacklevel=2
        )
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # 增强层
    'EnrichedSignal',
    'EnrichedSemanticGraph',
    'EnrichedLoadPoint',
    'EnrichedDriverPoint',
    'SemanticEnricher',
    'AgentContext',
    
    # 兼容层
    'SemanticGraph',
    'Extractor',
    'LoadPoint',
    'DriverPoint',
    'Connection',
    'ConfidenceLevel',
    
    # 废弃但仍导出
    'SemanticCollector',
    'DriverCollector',
]
