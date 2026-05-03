"""Debug 模块 - SystemVerilog 调试与分析工具。

提供代码分析、复杂度评估、类相关功能等调试工具。

主要功能：
- FSM 状态机提取
- 设计评估
- 类相关分析
- 复杂度分析

Example:
    >>> from debug import DesignEvaluator, FSMExtractor
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> evaluator = DesignEvaluator(parser)
    >>> print(evaluator.get_summary())
"""
from .fsm import FSMExtractor

__all__ = ['FSMExtractor']
