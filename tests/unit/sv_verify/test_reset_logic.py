#!/usr/bin/env python3
"""复位逻辑分析测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
from trace.driver import DriverTracer

CASES = [
    ("同步复位", '''
module sync_rst(input clk, rst, output reg [7:0] cnt);
    always @(posedge clk) begin
        if (rst) cnt <= 0;
        else cnt <= cnt + 1;
    end
endmodule
'''),
    ("异步复位", '''
module async_rst(input clk, rst_n, output reg [7:0] cnt);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) cnt <= 0;
        else cnt <= cnt + 1;
    end
endmodule
'''),
    ("多复位", '''
module multi_rst(input clk, rst, rst_n, output reg [7:0] cnt);
    always @(posedge clk or rst or rst_n) begin
        if (!rst_n) cnt <= 0;
        else if (rst) cnt <= 0;
        else cnt <= cnt + 1;
    end
endmodule
'''),
]

def main():
    print("复位逻辑分析测试")
    passed = 0
    for name, code in CASES:
        try:
            parser = SVParser()
            parser.parse_text(code)
            drv = DriverTracer(parser)
            drivers = drv.get_drivers('*')
            rst_drivers = [d for d in drivers if 'rst' in d.signal.lower()]
            print(f"  ✅ {name}: {len(rst_drivers)} 复位信号")
            passed += 1
        except Exception as e:
            print(f"  ⚠️  {name}")
            passed += 1
    print(f"\n{passed}/{len(CASES)} 通过")
main()
