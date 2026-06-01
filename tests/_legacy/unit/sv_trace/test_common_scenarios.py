#!/usr/bin/env python3
"""
sv_trace 常用场景测试
"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer


COMMON_SCENARIOS = [
    # 1. 同步复位
    ("sync_reset", '''
module sync_reset(input clk, input rst_n, output reg [7:0] cnt);
    always @(posedge clk) begin
        if (!rst_n)
            cnt <= 0;
        else
            cnt <= cnt + 1;
    end
endmodule
'''),
    # 2. 异步复位
    ("async_reset", '''
module async_reset(input clk, input rst_n, output reg [7:0] cnt);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cnt <= 0;
        else
            cnt <= cnt + 1;
    end
endmodule
'''),
    # 3. 计数器
    ("counter", '''
module counter(input clk, input rst, input en, output [7:0] cnt);
    reg [7:0] cnt;
    always @(posedge clk) begin
        if (rst)
            cnt <= 0;
        else if (en)
            cnt <= cnt + 1;
    end
endmodule
'''),
    # 4. 状态机
    ("fsm", '''
module fsm(input clk, input rst, input go, output [1:0] state);
    localparam IDLE=0, RUN=1, DONE=2;
    reg [1:0] state;
    always @(posedge clk) begin
        if (rst)
            state <= IDLE;
        else if (go && state==IDLE)
            state <= RUN;
        else if (state==RUN)
            state <= DONE;
    end
endmodule
'''),
    # 5. FIFO 接口
    ("fifo_if", '''
module fifo_if(input clk, input rst, input wr, input rd, 
               input [7:0] wdata, output [7:0] rdata, output empty, full);
    reg [7:0] mem [0:15];
    reg [3:0] wr_ptr, rd_ptr;
    reg empty_reg, full_reg;
    
    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
        end else if (wr && !full) begin
            mem[wr_ptr[3:0]] <= wdata;
            wr_ptr <= wr_ptr + 1;
        end
    end
    
    assign empty = (wr_ptr == rd_ptr);
    assign full = (wr_ptr[3:0] == rd_ptr[3:0]) && (wr_ptr[4] != rd_ptr[4]);
endmodule
'''),
]


def test_scenario(name, code):
    try:
        parser = SVParser()
        parser.parse_text(code, f"{name}.sv")
        
        drv = DriverTracer(parser)
        drivers = drv.get_drivers('*')
        
        print(f"  ✅ {name}: {len(drivers)} drivers")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:30]}")
        return False


def main():
    print("=" * 60)
    print("sv_trace 常用场景测试")
    print("=" * 60)
    
    passed = 0
    for name, code in COMMON_SCENARIOS:
        if test_scenario(name, code):
            passed += 1
    
    print("=" * 60)
    print(f"结果: {passed}/{len(COMMON_SCENARIOS)} 通过")
    print("=" * 60)


if __name__ == '__main__':
    main()
