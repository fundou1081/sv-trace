"""Lint - SystemVerilog 静态检查模块。

提供代码质量检查和静态分析功能：
- lint.linter: Lint 静态检查
- lint.code_quality: 代码质量综合检查
- lint.syntax_check: 语法兼容性检查

Example:
    >>> from lint.linter import SVLinter
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> linter = SVLinter(parser)
    >>> report = linter.run_all()
"""
