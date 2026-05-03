"""Debug Analyzers - SystemVerilog 调试分析器模块。

提供多种代码分析器：
- XValueDetector: X 值检测
- MultiDriverDetector: 多驱动检测
- UninitializedDetector: 未初始化检测
- ClockDomainAnalyzer: 时钟域分析
- CDCAnalyzer: 跨时钟域分析
- DanglingPortDetector: 悬空端口检测
- RootCauseAnalyzer: 根本原因分析

Example:
    >>> from debug.analyzers import XValueDetector, MultiDriverDetector
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> detector = XValueDetector(parser)
    >>> issues = detector.detect("signal_name")
"""

from .xvalue import XValueDetector
from .multi_driver import MultiDriverDetector
from .uninitialized import UninitializedDetector

__all__ = [
    'XValueDetector', 
    'MultiDriverDetector', 
    'UninitializedDetector', 
    'ClockDomainAnalyzer', 
    'CDCAnalyzer', 
    'DanglingPortDetector', 
    'RootCauseAnalyzer'
]
