#!/usr/bin/env python3
"""
CoverageStimulusSuggester 边界测试
测试嵌套if、间接信号、复合case等场景
"""
import sys
import os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from verify.coverage_guide.stimulus_suggester import CoverageStimulusSuggester


# 边界测试用例
EDGE_CASES = [
    # 1. 嵌套if
    ("nested_if", '''
module nested_if(input a, b, c, d, output [7:0] y);
    always @(*) begin
        if (a) begin
            if (b)
                y = 8'h01;
            else
                y = 8'h02;
        end else begin
            if (c && d)
                y = 8'h03;
            else
                y = 8'h04;
        end
    end
endmodule
'''),
    
    # 2. 间接信号 (信号作为条件)
    ("indirect_signal", '''
module indirect(input a, b, c, output y);
    wire cond1 = a & b;
    wire cond2 = ~c;
    assign y = cond1 | cond2;
endmodule
'''),
    
    # 3. 复合case
    ("complex_case", '''
module complex_case(input [2:0] sel, input a, b, c, d, e, f, g, h, output [7:0] y);
    always @(*) begin
        case (sel)
            3'b000: y = a ? 8'h01 : 8'h00;
            3'b001: y = b ? 8'h02 : 8'h00;
            3'b010: y = c ? 8'h03 : 8'h00;
            3'b011: y = d ? 8'h04 : 8'h00;
            3'b100: y = e ? 8'h05 : 8'h00;
            3'b101: y = f ? 8'h06 : 8'h00;
            3'b110: y = g ? 8'h07 : 8'h00;
            default: y = h ? 8'h08 : 8'h00;
        endcase
    end
endmodule
'''),
    
    # 4. casez (带x/z)
    ("casez", '''
module casez_test(input [2:0] sel, output [7:0] y);
    always @(*) begin
        casez (sel)
            3'b??1: y = 8'h01;
            3'b?1?: y = 8'h02;
            3'b1??: y = 8'h03;
            default: y = 8'h00;
        endcasez
    end
endmodule
'''),
    
    # 5. 三元嵌套
    ("ternary_nested", '''
module ternary(input [1:0] a, b, c, output y);
    assign y = a[0] ? (b[0] ? c[0] : c[1]) : (b[1] ? c[2] : c[3]);
endmodule
'''),
    
    # 6. 多层选择
    ("multi_select", '''
module multi_sel(input [3:0] sel, input [7:0] a, b, c, d, output y);
    assign y = sel[3] ? d : (sel[2] ? c : (sel[1] ? b : a));
endmodule
'''),
    
    # 7. 状态机风格
    ("fsm_style", '''
module fsm_style(input clk, rst, go, output [1:0] state);
    localparam IDLE=0, RUN=1, DONE=2;
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
    
    # 8. 优先级编码
    ("priority_enc", '''
module priority(input [3:0] req, output [1:0] grant);
    always @(*) begin
        grant = 0;
        if (req[3]) grant = 3;
        else if (req[2]) grant = 2;
        else if (req[1]) grant = 1;
        else if (req[0]) grant = 0;
    end
endmodule
'''),
    
    # 9. 边界条件
    ("boundary", '''
module boundary(input [7:0] data, output y);
    always @(*) begin
        if (data == 0)
            y = 1;
        else if (data == 255)
            y = 2;
        else if (data > 128)
            y = 3;
        else if (data < 64)
            y = 4;
        else
            y = 0;
    end
endmodule
'''),
    
    # 10. 组合逻辑环形
    ("combo_loop_check", '''
module combo(input a, b, c, output y);
    wire w1 = a & b;
    wire w2 = w1 | c;
    assign y = w2;
endmodule
'''),
]


def test_edge_case(name, code):
    """测试单个边界用例"""
    try:
        parser = SVParser()
        parser.parse_text(code)
        
        suggester = CoverageStimulusSuggester(parser)
        
        print(f"  ✅ {name}")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:40]}")
        return False


def main():
    print("=" * 60)
    print("CoverageStimulusSuggester 边界测试")
    print("=" * 60)
    
    passed = 0
    for name, code in EDGE_CASES:
        if test_edge_case(name, code):
            passed += 1
    
    print("=" * 60)
    print(f"结果: {passed}/{len(EDGE_CASES)} 通过")
    print("=" * 60)
    
    return passed == len(EDGE_CASES)


if __name__ == '__main__':
    main()


# 更多组合条件测试
COMBO_CASES = [
    # 1. 多位选信号
    ("bit_select", '''
module bit_sel(input [3:0] data, [1:0] sel, output y);
    assign y = data[sel];
endmodule
'''),
    
    # 2. 部分选择
    ("part_select", '''
module part_sel(input [7:0] data, output [3:0] y);
    assign y = data[7:4];
endmodule
'''),
    
    # 3. 动态部分选择
    ("dynamic_part_sel", '''
module dyn_part(input [7:0] data, [2:0] idx, output [1:0] y);
    assign y = data[idx+:2];
endmodule
'''),
    
    # 4. 多条件与
    ("multi_and", '''
module multi_and(input a, b, c, d, output y);
    assign y = a & b & c & d;
endmodule
'''),
    
    # 5. 多条件或
    ("multi_or", '''
module multi_or(input a, b, c, d, output y);
    assign y = a | b | c | d;
endmodule
'''),
    
    # 6. 混合与或
    ("mixed_and_or", '''
module mixed(input a, b, c, d, output y);
    assign y = (a & b) | (c & d);
endmodule
'''),
    
    # 7. 移位条件
    ("shift_cond", '''
module shift_cond(input [7:0] data, [2:0] sel, output [7:0] y);
    assign y = data << sel;
endmodule
'''),
    
    # 8. 重复选择
    ("repeat_sel", '''
module repeat_sel(input [1:0] sel, input a, b, c, d, output y);
    assign y = sel==0 ? a : (sel==1 ? b : (sel==2 ? c : d));
endmodule
'''),
    
    # 9. 跨位选
    ("cross_bit", '''
module cross(input [7:0] a, [7:0] b, sel, output y);
    assign y = sel ? a[7:4] : b[3:0];
endmodule
'''),
    
    # 10. 条件移位
    ("cond_shift", '''
module cond_shift(input [7:0] data, input en, input [1:0] amount, output [7:0] y);
    assign y = en ? (data << amount) : data;
endmodule
'''),
]


# 运行额外测试
def test_combo():
    print("\n=== 组合条件测试 ===")
    passed = 0
    for name, code in COMBO_CASES:
        try:
            parser = SVParser()
            parser.parse_text(code)
            suggester = CoverageStimulusSuggester(parser)
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {str(e)[:30]}")
    print(f"\n组合测试: {passed}/{len(COMBO_CASES)} 通过")
    return passed == len(COMBO_CASES)


if __name__ == '__main__':
    test_combo()
