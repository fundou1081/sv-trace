"""Trace Query 模块 - 跨模块追踪查询

提供场景化的追踪接口，组合底层模块实现跨模块追踪。

遵循开发纪律:
- 铁律5: 原子化必须保持 - 使用组合而非新建
- 铁律10: API 返回必须有置信度标注
- 铁律11: 必须提供 Agent 调用示例
- 铁律13: 金标准测试

Example:
    >>> from trace.query import SignalChainQuery
    >>> 
    >>> query = SignalChainQuery(parser)
    >>> result = query.trace("data_out", module="Top")
    >>> print(result.data.drivers)    # 上游驱动
    >>> print(result.data.loads)       # 下游负载
    >>> print(result.confidence)        # high/medium/uncertain
"""

from .signal_chain import SignalChainQuery, SignalChainResult
from .module_connections import ModuleConnectionsQuery, ModuleConnectionsResult, PortConnection
from .clock_domain import ClockDomainTracer, ClockDomainResult, RegisterInfo

__all__ = [
    # 场景A
    "SignalChainQuery",
    "SignalChainResult",
    # 场景B
    "ModuleConnectionsQuery",
    "ModuleConnectionsResult",
    "PortConnection",
    # 场景C
    "ClockDomainTracer",
    "ClockDomainResult",
    "RegisterInfo",
]
