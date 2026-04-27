"""
sv-trace - SystemVerilog Static Analysis Library

A comprehensive library for SystemVerilog static analysis,
RTL tracing, verification support, and code quality checking.

Usage:
    import sys
    sys.path.insert(0, 'src')
    
    from parse import SVParser
    from verify.tb_analyzer import TBComplexityAnalyzer

CLI Tools:
    sv-constraint      - Constraint analysis with z3
    sv-constraint-prob - Constraint probability analysis
    sv-tb-complexity   - Testbench complexity analysis
    sv-datapath        - RTL data path analysis
    sv-quality         - Code quality analysis
    sv-signal          - Signal classification

For more information, see: https://github.com/yourusername/sv-trace
"""

__version__ = "0.1.0"
__author__ = "方浩博 (Fang Haobo)"
