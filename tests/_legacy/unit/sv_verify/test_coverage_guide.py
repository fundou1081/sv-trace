#!/usr/bin/env python3
"""代码覆盖率指导测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
from trace.driver import DriverTracer
from trace.load import LoadTracer

CASES = [
    ("FSM覆盖率", '''
module fsm(input clk, input rst, input go, output [1:0] st);
    localparam S0=0, S1=1, S2=2;
    reg [1:0] st;
    always @(posedge clk) begin
        if (rst) st <= S0;
        else if (go && st==S0) st <= S1;
        else if (st==S1) st <= S2;
    end
endmodule
'''),
    ("分支覆盖", '''
module branch(input a, b, output y);
    always @(*) begin
        if (a && b) y = 1;
        else if (a) y = 0;
        else y = 0;
    end
endmodule
'''),
    ("条件覆盖", '''
module cond(input [2:0] sel, output [7:0] y);
    assign y = sel[0] ? 8'h01 :
               sel[1] ? 8'h02 :
               sel[2] ? 8'h04 : 8'h00;
endmodule
'''),
]

def main():
    print("代码覆盖率指导测试")
    passed = 0
    for name, code in CASES:
        try:
            parser = SVParser()
            parser.parse_text(code, f"{name}.sv")
            drv = DriverTracer(parser)
            ld = LoadTracer(parser)
            print(f"  ✅ {name}")
            passed += 1
        except:
            print(f"  ❌ {name}")
    print(f"\n{passed}/{len(CASES)} 通过")
main()
