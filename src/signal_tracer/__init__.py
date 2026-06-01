"""signal_tracer - 信号追踪器

给一个信号，返回它的所有驱动(drivers)和负载(loads)，包含文件位置和 scope 源码。

Usage:
    from signal_tracer import trace_signal

    result = trace_signal("b", sv_code, "test.sv")
    for d in result.drivers:
        print(f"b <- {d.source_expr}")
        print(f"  at line {d.line}")
        print(f"  in scope:")
        print(f"  {d.scope_text}")

    for l in result.loads:
        print(f"b -> {l.signal_name}")

    # 获取驱动链
    chain = result.get_driver_chain()
    print(f"Driver chain: {' <- '.join(chain)}")
"""

from signal_tracer.models import (
    TraceResult,
    TraceType,
    ScopeKind,
    DriverTrace,
    LoadTrace,
    ScopeInfo,
    SignalInfo,
    TraceSummary,
    ContextBundle,
)
from signal_tracer.tracer import (
    SignalTracer,
    SignalTracerFromFile,
    trace_signal,
    trace_signal_from_file,
)

__all__ = [
    # 数据模型
    'TraceResult',
    'TraceType',
    'ScopeKind',
    'DriverTrace',
    'LoadTrace',
    'ScopeInfo',
    'SignalInfo',
    'TraceSummary',
    'ContextBundle',
    # 核心类
    'SignalTracer',
    'SignalTracerFromFile',
    # 便捷函数
    'trace_signal',
    'trace_signal_from_file',
]