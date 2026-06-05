"""
test_arrow_format.py — M5.1j 人类友好箭头式输出 (formatters + to_arrow methods)

覆盖:
- format_driver / format_load / format_all (formatters 模块函数)
- TraceResult.to_arrow() / to_arrow_all()
- TraceSummary.to_arrow() (一键 drivers + loads)
- ContextBundle.to_arrow() (从 code_evidence 拿 credibility)
- SignalTracer.to_arrow() / chain_to_arrow() / multi_drivers_to_arrow() / dump_to_arrow()
- ARROW_DRIVER / ARROW_LOAD 常量
"""
import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

import pytest
from signal_tracer import (
    trace_signal, SignalTracer,
    format_driver, format_load, format_trace_arrow,
    format_driver_chain, format_multi_driver,
    format_evidence_chain, format_dump_summary, format_all,
    ARROW_DRIVER, ARROW_LOAD,
)


COUNTER_SV = """
module counter (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] count
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) count <= 8'h00;
        else        count <= count + data_in;
    end
endmodule
"""

MULTI_SV = """
module buggy (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       mode,
    output logic [7:0] data
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (rst_n && mode == 1'b0) data <= 8'hAA;
    end
    always_ff @(posedge clk or negedge rst_n) begin
        if (rst_n && mode == 1'b1) data <= 8'h55;
    end
endmodule
"""


class TestArrowConstants:
    def test_arrow_driver_is_unicode(self):
        assert ARROW_DRIVER == "←"
        assert len(ARROW_DRIVER) == 1  # 单字符

    def test_arrow_load_is_unicode(self):
        assert ARROW_LOAD == "→"
        assert len(ARROW_LOAD) == 1


class TestFormatDriver:
    def test_basic_driver(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        d = result.drivers[0]
        out = format_driver(d)
        assert "count" in out
        assert ARROW_DRIVER in out
        assert "counter.sv" in out
        assert "8'h00" in out

    def test_driver_with_credibility(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        d = result.drivers[0]
        out = format_driver(d, show_credibility=True)
        assert "cred=" in out
        assert "✓" in out  # verified

    def test_driver_without_location(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        d = result.drivers[0]
        out = format_driver(d, show_location=False)
        assert "@" not in out  # 没 location

    def test_driver_with_long_expr_truncates(self):
        long_expr_sv = """
module m;
    logic [31:0] a, b, c, d, e, f;
    assign a = b + c + d + e + f + 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10;
endmodule
"""
        result = trace_signal("a", long_expr_sv, "long.sv")
        d = result.drivers[0]
        out = format_driver(d, max_expr_len=20)
        assert "…" in out  # 截断


class TestFormatLoad:
    def test_load_arrow_direction(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        # count 在这个模块没有 load, 但 format_load 可以强行调用
        # 用 result.drivers[0] 强行跑, 看箭头方向
        if result.loads:
            ld = result.loads[0]
        else:
            ld = result.drivers[0]
        out = format_load(ld)
        assert ARROW_LOAD in out
        assert "count" in out


class TestFormatAll:
    def test_format_all_includes_both(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        out = format_all(result)
        assert "DRIVERS (2):" in out
        assert "LOADS (0):" in out
        assert "(none)" in out
        assert ARROW_DRIVER in out


class TestTraceResultToArrow:
    def test_to_arrow_on_driver(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        for d in result.drivers:
            arrow = d.to_arrow()
            assert "count" in arrow
            assert ARROW_DRIVER in arrow

    def test_to_arrow_truncation(self):
        long_expr_sv = """
module m;
    logic [31:0] a, b, c, d, e;
    assign a = b + c + d + e + 1 + 2 + 3 + 4 + 5 + 6;
endmodule
"""
        result = trace_signal("a", long_expr_sv, "long.sv")
        arrow = result.drivers[0].to_arrow(max_expr_len=5)
        assert "…" in arrow


class TestTraceSummaryToArrow:
    def test_to_arrow_combines_drivers_loads(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        out = result.to_arrow()
        assert "DRIVERS" in out
        assert "LOADS" in out
        assert result.drivers[0].source_expr in out


class TestContextBundleToArrow:
    def test_to_arrow(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        for ctx in result.to_contexts(file_content=COUNTER_SV):
            arrow = ctx.to_arrow()
            assert "count" in arrow
            assert ARROW_DRIVER in arrow
            # 来自 code_evidence 的 cred
            assert "cred=" in arrow


class TestSignalTracerToArrow:
    def test_to_arrow(self):
        t = SignalTracer()
        t.add_file("counter.sv", COUNTER_SV)
        t.build()
        out = t.to_arrow("count")
        assert "DRIVERS (2):" in out
        assert ARROW_DRIVER in out

    def test_chain_to_arrow(self):
        t = SignalTracer()
        t.add_file("counter.sv", COUNTER_SV)
        t.build()
        out = t.chain_to_arrow("count", direction="driver", max_depth=5)
        # chain 含 count + data_in (or 8'h00)
        assert "count" in out
        assert ARROW_DRIVER in out

    def test_multi_drivers_to_arrow(self):
        t = SignalTracer()
        t.add_file("buggy.sv", MULTI_SV)
        t.build()
        out = t.multi_drivers_to_arrow()
        assert "⚠" in out
        assert "8'hAA" in out
        assert "8'h55" in out

    def test_dump_to_arrow(self):
        t = SignalTracer()
        t.add_file("counter.sv", COUNTER_SV)
        t.build()
        out = t.dump_to_arrow("count", direction="driver", max_depth=5)
        assert "Chain count" in out
        assert "hops" in out
        assert "avg_cred" in out


class TestFormatDriverChain:
    def test_chain_list_of_strings(self):
        out = format_driver_chain(["out", "c", "b", "a"], direction="driver")
        assert "out" in out
        assert "a" in out
        assert ARROW_DRIVER in out

    def test_chain_list_of_traceresult(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        # 直接传 TraceResult 列表 (get_driver_chain 返回类型)
        chain = result.get_driver_chain(max_depth=5)
        out = format_driver_chain(chain, direction="driver")
        assert "count" in out

    def test_chain_with_cycle_marker(self):
        out = format_driver_chain(["a", "b", "a"], direction="driver", has_cycle=True)
        assert "↻" in out

    def test_chain_with_crossfile(self):
        out = format_driver_chain(
            ["a", "b"], direction="driver",
            cross_files=["top.sv", "sub.sv"]
        )
        assert "⤴" in out

    def test_chain_load_direction(self):
        out = format_driver_chain(["a", "b"], direction="load")
        assert ARROW_LOAD in out

    def test_empty_chain(self):
        out = format_driver_chain([], direction="driver")
        assert "no driver chain" in out


class TestFormatMultiDriver:
    def test_two_drivers(self):
        t = SignalTracer()
        t.add_file("buggy.sv", MULTI_SV)
        t.build()
        multi = t.find_multi_drivers()
        sig, drivers = next(iter(multi.items()))
        out = format_multi_driver(sig, drivers)
        assert "⚠ 2 drivers" in out
        assert "8'hAA" in out
        assert "8'h55" in out

    def test_single_driver(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        out = format_multi_driver("count", [result.drivers[0]])
        assert "⚠" not in out
        # 单 driver 走 format_driver path
        assert "count" in out

    def test_no_drivers(self):
        out = format_multi_driver("x", [])
        assert "no drivers" in out


class TestFormatEvidenceChain:
    def test_format_evidence_chain(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        d = result.drivers[0]
        out = format_evidence_chain(d)
        assert "count" in out
        assert "cred" in out


class TestFormatDumpSummary:
    def test_chain_dump(self):
        t = SignalTracer()
        t.add_file("counter.sv", COUNTER_SV)
        t.build()
        dump = t.dump_driver_chain("count", max_depth=5, summary_only=False)
        out = format_dump_summary(dump)
        assert "Chain" in out
        assert "avg_cred" in out

    def test_multi_dump(self):
        t = SignalTracer()
        t.add_file("buggy.sv", MULTI_SV)
        t.build()
        dump = t.dump_multi_drivers(summary_only=False)
        out = format_dump_summary(dump)
        assert "Multi-drivers" in out
        assert "conflict signals" in out


# === M5.1k: tree / vertical / ascii 风格 ===

CHAIN_SV = """
module top (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] ext_in_data,
    output logic [7:0] ext_out_data
);
    mid u_mid (.clk(clk), .rst_n(rst_n), .in_data(ext_in_data), .out_data(ext_out_data));
endmodule
"""

CHAIN_MID = """
module mid (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] in_data,
    output logic [7:0] out_data
);
    leaf u_leaf_a (.clk(clk), .rst_n(rst_n), .in_data(in_data), .out_data(out_data));
endmodule
"""

CHAIN_LEAF = """
module leaf (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] in_data,
    output logic [7:0] out_data
);
    logic [7:0] mid_data;
    assign mid_data = in_data + 8'h01;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) out_data <= 8'h00;
        else        out_data <= mid_data + 8'hAA;
    end
endmodule
"""


def _build_chain_tracer():
    t = SignalTracer()
    t.add_file("top.sv", CHAIN_SV)
    t.add_file("mid.sv", CHAIN_MID)
    t.add_file("leaf.sv", CHAIN_LEAF)
    t.build()
    return t


class TestChainStyleArrow:
    """style='arrow' (默认): 一行箭头式"""

    def test_arrow_default(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", direction="driver", max_depth=5)
        assert "←" in out
        assert "Driver chain" not in out  # 1 行, 不含 tree head

    def test_explicit_arrow(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", style="arrow")
        assert "←" in out


class TestChainStyleTree:
    """style='tree': tree 风格, box-drawing"""

    def test_tree_unicode_box(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", style="tree")
        assert "Driver chain:" in out
        assert "├─" in out  # tee
        assert "└─" in out  # corner
        assert "│" in out   # vertical line
        assert "hop" in out  # 头部含 hop 数

    def test_tree_includes_location(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", style="tree")
        assert "[leaf.sv:" in out
        assert "mid_data" in out
        assert "out_data" in out


class TestChainStyleAscii:
    """style='ascii': ASCII 字符 tree"""

    def test_ascii_chars(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", style="ascii")
        assert "+--" in out
        assert "|" in out
        # 不应该用 Unicode box-drawing
        assert "├─" not in out
        assert "└─" not in out

    def test_ascii_includes_hops(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", style="ascii")
        assert "Driver chain:" in out
        assert "hop" in out


class TestChainStyleVertical:
    """style='vertical': 每行一个信号 + 箭头"""

    def test_vertical_multiline(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", style="vertical")
        lines = out.split("\n")
        assert len(lines) >= 2
        # 第一行只有 signal
        assert "out_data" in lines[0]
        # 后续行有箭头
        assert any("←" in line for line in lines[1:])

    def test_vertical_indentation(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", style="vertical")
        lines = out.split("\n")
        # 第一行没缩进, 后续行有缩进
        assert lines[0] == lines[0].lstrip()
        assert lines[1] != lines[1].lstrip()  # 至少有一行有缩进


class TestChainStyleAll:
    """style='all' / 'both': arrow + tree 都给"""

    def test_all_contains_both(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", style="all")
        assert "←" in out  # arrow 部分
        assert "Driver chain:" in out  # tree 部分
        assert "├─" in out  # tree 部分

    def test_both_alias(self):
        t = _build_chain_tracer()
        out = t.chain_to_arrow("top.u_mid.u_leaf_a.out_data", style="both")
        assert "Driver chain:" in out
        assert "←" in out


class TestChainToTreeAlias:
    """chain_to_tree 是 chain_to_arrow(style='tree') 的 alias"""

    def test_chain_to_tree_default(self):
        t = _build_chain_tracer()
        out = t.chain_to_tree("top.u_mid.u_leaf_a.out_data")
        assert "Driver chain:" in out
        assert "├─" in out

    def test_chain_to_tree_ascii(self):
        t = _build_chain_tracer()
        out = t.chain_to_tree("top.u_mid.u_leaf_a.out_data", use_box=False)
        assert "+--" in out
        assert "├─" not in out


class TestChainToVerticalAlias:
    def test_chain_to_vertical(self):
        t = _build_chain_tracer()
        out = t.chain_to_vertical("top.u_mid.u_leaf_a.out_data")
        assert "out_data" in out
        assert "←" in out
        assert "\n" in out  # 多行


class TestDumpToTree:
    """dump_to_arrow 支持 style=tree/vertical"""

    def test_dump_to_arrow_tree(self):
        t = _build_chain_tracer()
        out = t.dump_to_arrow("top.u_mid.u_leaf_a.out_data", style="tree")
        # dump 没 self-reference 识别 cycle, 不会标 cycle
        assert "Driver chain:" in out
        assert "├─" in out

    def test_dump_to_arrow_vertical(self):
        t = _build_chain_tracer()
        out = t.dump_to_arrow("top.u_mid.u_leaf_a.out_data", style="vertical")
        assert "out_data" in out
        assert "←" in out
        assert "\n" in out

    def test_dump_to_arrow_ascii(self):
        t = _build_chain_tracer()
        out = t.dump_to_arrow("top.u_mid.u_leaf_a.out_data", style="ascii")
        assert "+--" in out

    def test_dump_to_arrow_all(self):
        t = _build_chain_tracer()
        out = t.dump_to_arrow("top.u_mid.u_leaf_a.out_data", style="all")
        assert "Driver chain:" in out
        # arrow 部分
        assert "Chain " in out  # "Chain <sig>: N hops, avg_cred=..."


class TestDumpToTreeAlias:
    def test_dump_to_tree_default(self):
        t = _build_chain_tracer()
        out = t.dump_to_tree("top.u_mid.u_leaf_a.out_data")
        assert "Driver chain:" in out
        assert "├─" in out

    def test_dump_to_tree_ascii(self):
        t = _build_chain_tracer()
        out = t.dump_to_tree("top.u_mid.u_leaf_a.out_data", use_box=False)
        assert "+--" in out


class TestFormatDriverChainDirectly:
    """直接调 format_driver_chain 用 style"""

    def test_format_driver_chain_tree(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        chain = result.get_driver_chain(max_depth=5)
        out = format_driver_chain(chain, direction="driver", style="tree")
        assert "Driver chain:" in out
        assert "├─" in out or "└─" in out

    def test_format_driver_chain_vertical(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        chain = result.get_driver_chain(max_depth=5)
        out = format_driver_chain(chain, direction="driver", style="vertical")
        assert "count" in out
        assert "←" in out

    def test_format_driver_chain_ascii(self):
        result = trace_signal("count", COUNTER_SV, "counter.sv")
        chain = result.get_driver_chain(max_depth=5)
        out = format_driver_chain(chain, direction="driver", style="ascii")
        assert "+--" in out
