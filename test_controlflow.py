import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.controlflow import ControlFlowTracer

# 测试用例
tests = [
    ("If-Else", '''module t;
        logic a, b, c, r;
        always_comb begin
            if (a)
                r = b;
            else
                r = c;
        end
    endmodule''', 'r'),
    
    ("Case Statement", '''module t;
        logic [1:0] sel;
        logic a, b, c, r;
        always_comb begin
            case(sel)
                2'b00: r = a;
                2'b01: r = b;
                default: r = c;
            endcase
        end
    endmodule''', 'r'),
    
    ("FSM Next State", '''module t;
        logic clk;
        logic [1:0] state, next_state;
        logic req, ack;
        always_ff @(posedge clk) begin
            state <= next_state;
        end
        always_comb begin
            case(state)
                2'b00: next_state = req ? 2'b01 : 2'b00;
                2'b01: next_state = ack ? 2'b10 : 2'b01;
                default: next_state = 2'b00;
            endcase
        end
    endmodule''', 'next_state'),
    
    ("FSM Current State", '''module t;
        logic clk;
        logic [1:0] state, next_state;
        logic req, ack;
        always_ff @(posedge clk) begin
            state <= next_state;
        end
        always_comb begin
            case(state)
                2'b00: next_state = req ? 2'b01 : 2'b00;
                2'b01: next_state = ack ? 2'b10 : 2'b01;
                default: next_state = 2'b00;
            endcase
        end
    endmodule''', 'state'),
]

print("="*60)
print("控制流分析测试")
print("="*60)

for name, code, sig in tests:
    print(f"\n{'='*50}")
    print(f"测试: {name} - {sig}")
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
            
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
    finally:
        os.unlink(tmp)
