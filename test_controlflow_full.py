import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.controlflow import ControlFlowTracer

# 更多测试用例
tests = [
    ("Priority Encoder", '''module t;
        logic [3:0] in;
        logic [1:0] out;
        always_comb begin
            if (in[3]) out = 2'b11;
            else if (in[2]) out = 2'b10;
            else if (in[1]) out = 2'b01;
            else out = 2'b00;
        end
    endmodule''', 'out'),
    
    ("Mux with Case", '''module t;
        logic [1:0] sel;
        logic [31:0] a, b, c, d, out;
        always_comb begin
            case(sel)
                2'd0: out = a;
                2'd1: out = b;
                2'd2: out = c;
                default: out = d;
            endcase
        end
    endmodule''', 'out'),
    
    ("Register with Reset", '''module t;
        logic clk, rst, en, data, q;
        always_ff @(posedge clk) begin
            if (rst)
                q <= 1'b0;
            else if (en)
                q <= data;
        end
    endmodule''', 'q'),
    
    ("Complex Control", '''module t;
        logic clk, rst, vld;
        logic [31:0] a, b, c, result;
        logic [1:0] mode;
        
        always_ff @(posedge clk) begin
            if (rst)
                result <= 0;
            else if (vld && mode == 2'b00)
                result <= a + b;
            else if (vld && mode == 2'b01)
                result <= a - b;
            else if (vld)
                result <= c;
        end
    endmodule''', 'result'),
]

print("="*60)
print("控制流分析 - 完整测试")
print("="*60)

passed = 0
for name, code, sig in tests:
    print(f"\n{'='*50}")
    print(f"测试: {name}")
    print("="*50)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        tracer = ControlFlowTracer(parser)
        flow = tracer.find_control_dependencies(sig)
        
        print(flow.visualize())
        passed += 1
        print(f"\n✅ 通过")
            
    except Exception as e:
        import traceback
        print(f"❌ 失败: {e}")
    finally:
        os.unlink(tmp)

print(f"\n{'='*60}")
print(f"测试结果: {passed}/{len(tests)} 通过")
print("="*60)
