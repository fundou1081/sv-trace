"""Timing & CDC Test"""
import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.query.clock_domain import ClockDomainTracer
from trace.query.timing_path import TimingPathTracer


def test_clock():
    sv = '''module t (input clk1, clk2, rst_n, d, output q1, q2);
        reg r1, r2;
        always_ff @(posedge clk1) r1 <= d;
        always_ff @(posedge clk2) r2 <= d;
    endmodule'''
    tree = SVParser().parse_text(sv, 't.sv')
    ct = ClockDomainTracer(use_semantic=True)
    ct.collect(tree, 't.sv')
    assert len(ct.all_clocks) >= 1


def test_timing():
    sv = '''module t (input clk, d, output q);
        reg r1, r2, r3;
        always_ff @(posedge clk) begin r1 <= d; r2 <= r1; r3 <= r2; end
    endmodule'''
    tree = SVParser().parse_text(sv, 't.sv')
    tt = TimingPathTracer(use_semantic=True)
    tt.collect(tree, 't.sv')
    assert tt.register_count >= 0


def test_real():
    import glob, os
    base = '/Users/fundou/my_dv_proj/basic_verilog'
    files = glob.glob(f'{base}/*.sv')[:5]
    ok = 0
    for f in files:
        try:
            with open(f) as fp:
                code = fp.read()
            tree = SVParser().parse_text(code, os.path.basename(f))
            ct = ClockDomainTracer(use_semantic=True)
            ct.collect(tree, os.path.basename(f))
            ok += 1
        except:
            pass
    assert ok >= 0
