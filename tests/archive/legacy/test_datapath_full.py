import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.datapath import DataPathAnalyzer

# 完整测试用例集
tests = [
    # 1. 简单 assign 链
    ("Simple Assign Chain", '''module t;
        logic a, b, c, r;
        assign b = a;
        assign c = b;
        assign r = c;
    endmodule''', 'r'),
    
    # 2. always_comb 算术
    ("ALU Operations", '''module t;
        logic [31:0] a, b, result;
        logic [1:0] op;
        always_comb begin
            case(op)
                2'b00: result = a + b;
                2'b01: result = a - b;
                2'b10: result = a & b;
                default: result = a | b;
            endcase
        end
    endmodule''', 'result'),
    
    # 3. 混合 always_ff + always_comb
    ("Mixed FF and Comb", '''module t;
        logic [31:0] a, b, reg1, reg2, out;
        logic clk;
        always_ff @(posedge clk) begin
            reg1 <= a + b;
        end
        always_comb begin
            reg2 = reg1 * 2;
        end
        assign out = reg2 + 1;
    endmodule''', 'out'),
    
    # 4. 多周期计算
    ("Multi-Cycle Compute", '''module t;
        logic [31:0] a, b, sum, sq, result;
        logic clk;
        always_ff @(posedge clk) begin
            sum <= a + b;
            sq <= sum * sum;
            result <= sq;
        end
    endmodule''', 'result'),
    
    # 5. 带条件寄存器的流水线
    ("Conditional Pipeline", '''module t;
        logic [31:0] din, s1, s2, dout;
        logic clk, vld;
        always_ff @(posedge clk) begin
            if (vld) begin
                s1 <= din;
                s2 <= s1;
                dout <= s2;
            end
        end
    endmodule''', 'dout'),
    
    # 6. 循环语句
    ("Array Sum with For", '''module t;
        logic [31:0] data [0:7], sum;
        logic [2:0] i;
        always_comb begin
            sum = 0;
            for (i = 0; i < 8; i++) begin
                sum = sum + data[i];
            end
        end
    endmodule''', 'sum'),
    
    # 7. 状态机
    ("Simple FSM", '''module t;
        logic [1:0] state, next_state;
        logic clk;
        logic a, b;
        
        always_ff @(posedge clk) begin
            state <= next_state;
        end
        
        always_comb begin
            case(state)
                2'b00: next_state = a ? 2'b01 : 2'b00;
                2'b01: next_state = b ? 2'b10 : 2'b01;
                2'b10: next_state = 2'b00;
                default: next_state = 2'b00;
            endcase
        end
    endmodule''', 'next_state'),
    
    # 8. 复杂数据流
    ("Complex DataFlow", '''module t;
        logic [31:0] x, y, z, tmp1, tmp2, out;
        logic clk;
        
        always_ff @(posedge clk) begin
            tmp1 <= x + y;
            tmp2 <= x - y;
        end
        
        always_comb begin
            out = (tmp1 * tmp2) + z;
        end
    endmodule''', 'out'),
]

print("=" * 60)
print("DataPath 深度分析完整测试")
print("=" * 60)

passed = 0
failed = 0

for name, code, target_sig in tests:
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"目标信号: {target_sig}")
    print("=" * 60)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        analyzer = DataPathAnalyzer(parser)
        dp = analyzer.analyze(target_sig)
        
        print(dp.visualize())
        print(f"\n✅ 测试通过")
        passed += 1
        
    except Exception as e:
        import traceback
        print(f"❌ 测试失败: {e}")
        traceback.print_exc()
        failed += 1
    finally:
        os.unlink(tmp)

print(f"\n{'='*60}")
print(f"测试结果: {passed} 通过, {failed} 失败")
print("=" * 60)
