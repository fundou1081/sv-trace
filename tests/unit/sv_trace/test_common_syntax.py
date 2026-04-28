#!/usr/bin/env python3
"""常用语法测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
from trace.driver import DriverTracer

CASES = [
    # 1. always 类型
    ("always_ff", '''
module af(input clk, rst, d, output reg q);
    always @(posedge clk) begin
        if (rst) q <= 0;
        else q <= d;
    end
endmodule
'''),
    ("always_comb", '''
module ac(input a, b, output y);
    always @(*) begin
        y = a & b;
    end
endmodule
'''),
    ("always_latch", '''
module al(input a, b, output reg y);
    always @(*) begin
        if (a) y = b;
    end
endmodule
'''),
    # 2. 函数
    ("function_simple", '''
module fs(input [7:0] a, b, output [7:0] y);
    function [7:0] add;
        input [7:0] x, y;
        add = x + y;
    endfunction
    assign y = add(a, b);
endmodule
'''),
    ("function_recursive", '''
module fr(output [7:0] y);
    function [7:0] fact;
        input [3:0] n;
        if (n == 0) fact = 1;
        else fact = n * fact(n-1);
    endfunction
    assign y = fact(5);
endmodule
'''),
    # 3. 任务
    ("task", '''
module tsk(input clk, d, output reg q);
    task write;
        input data;
        begin
            q <= data;
        end
    endtask
    always @(posedge clk) write(d);
endmodule
'''),
    # 4. generate
    ("gen_for", '''
module gf(output [3:0] y);
    genvar i;
    wire [3:0] w;
    for (i=0; i<4; i=i+1) begin : GEN
        assign w[i] = 1'b1;
    end
    assign y = w;
endmodule
'''),
    ("gen_if", '''
module gi(input en, output y);
    generate
        if (en) begin : INV
            assign y = 1'b1;
        end else begin : BUF
            assign y = 1'b0;
        end
    endgenerate
endmodule
'''),
    ("gen_case", '''
module gc(input [1:0] sel, output y);
    generate
        case (sel)
            0: assign y = 1'b0;
            1: assign y = 1'b1;
            default: assign y = 1'bx;
        endcase
    endgenerate
endmodule
'''),
    # 5. 过程块
    ("initial", '''
module init(output reg [7:0] y);
    initial y = 8'h00;
endmodule
'''),
    ("final", '''
module fn(output [7:0] y);
    reg [7:0] cnt;
    final cnt = 0;
endmodule
'''),
    ("forever", '''
module fv(output reg clk);
    reg clk;
    initial forever #5 clk = ~clk;
endmodule
'''),
]

def main():
    print("常用语法测试")
    passed = 0
    for name, code in CASES:
        try:
            p = SVParser()
            p.parse_text(code)
            d = DriverTracer(p)
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}")
    print(f"\n{passed}/{len(CASES)} 通过")
main()
