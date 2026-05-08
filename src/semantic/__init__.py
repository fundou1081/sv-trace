"""Semantic - 语义增强层

消费 extractors/ 输出的 SemanticGraph，提供语义增强。

符合铁律 21: Semantic 层不得直接遍历 AST
符合铁律 22: Enricher 必须标注 confidence 和 caveats

迁移说明:
- 原有的 SUPPORTED_KINDS + __post_init__ 模式已废弃
- semantic/base.py 已废弃，功能迁移到 extractors/
- 当前 semantic/ 是语义增强层，输出 EnrichedSemanticGraph
"""

# ============================================================
# ⚠️ 废弃声明 ⚠️
# 以下模块已废弃，功能迁移到 extractors/：
# ============================================================
import warnings as _warnings

# 标记废弃模块（仍可导入，但使用时会警告）
_deprecated = {
    'base': '使用 extractors/base.py',
    'driver': '使用 extractors/driver.py',
    'load': '使用 extractors/load.py',
    'clock': '使用 extractors/clock.py',
    'reset': '使用 extractors/reset.py',
    'connection': '使用 extractors/connection.py',
    'signal': '使用 extractors/signal.py',
    'fsm': '使用 extractors/fsm.py',
}

def __getattr__(name):
    if name in _deprecated:
        _warnings.warn(
            f"semantic.{name} 已废弃。 {_deprecated[name]}",
            DeprecationWarning,
            stacklevel=2
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# ============================================================
# 新增: 语义增强层
# ============================================================
from semantic.models import (
    EnrichedSignal,
    EnrichedSemanticGraph,
    EnrichedLoadPoint,
    EnrichedDriverPoint,
)

from semantic.enricher import SemanticEnricher
from semantic.agent_interface import AgentContext

__all__ = [
    # 废弃
    'base', 'driver', 'load', 'clock', 'reset', 'connection', 'signal', 'fsm',
    # 新增
    'EnrichedSignal',
    'EnrichedSemanticGraph',
    'EnrichedLoadPoint',
    'EnrichedDriverPoint',
    'SemanticEnricher',
    'AgentContext',
]
