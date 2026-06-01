"""
sv-trace - SystemVerilog 信号追踪器

目标: 给一个信号名，返回它在 .sv 源码里的所有 driver / load，
     以及完整的上下文（文件、行号、scope 源码、时钟/复位、条件栈、端口连接）。

公开 API:
    from signal_tracer import trace_signal
    result = trace_signal("data_out", sv_code, "test.sv")
    for d in result.drivers:
        print(d.file, d.line, d.source_expr)

详见:
    STRUCTURE.md - 项目结构
    TODO.md     - 路线图
"""

__version__ = "0.1.0"
