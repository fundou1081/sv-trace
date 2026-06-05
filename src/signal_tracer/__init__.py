"""signal_trace - 信号追踪器

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

import pyslang

# M5.1h fix: pyslang 11+ 将 SyntaxTree 移到了 pyslang.syntax 子模块
# 项目代码拿不到就让它可访问
try:
    SyntaxTree = pyslang.syntax.SyntaxTree
except AttributeError:
    SyntaxTree = pyslang.SyntaxTree

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
# M5.1j: 人类友好箭头式输出 (formatters 模块独立, 下面这些函数也直接可 import)
from signal_tracer.formatters import (
    format_driver,
    format_load,
    format_trace_arrow,
    format_driver_chain,
    format_multi_driver,
    format_evidence_chain,
    format_dump_summary,
    format_all,
    ARROW_DRIVER, ARROW_LOAD,
)

__version__ = "1.0.0"

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
    # M5.1j: 人类友好箭头式输出
    'format_driver',
    'format_load',
    'format_trace_arrow',
    'format_driver_chain',
    'format_multi_driver',
    'format_evidence_chain',
    'format_dump_summary',
    'format_all',
    'ARROW_DRIVER',
    'ARROW_LOAD',
]