import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from lint.linter import SVLinter

# 测试1: 未使用的信号
TEST1 = '''module t;
    logic a, b, c;
    logic unused1, unused2;
    assign b = a;
    assign c = b;
    // unused1, unused2 未使用
endmodule'''

# 测试2: 正常信号
TEST2 = '''module t;
    logic clk, a, b, r;
    assign b = a;
    always_ff @(posedge clk) begin
        r <= b;
    end
endmodule'''

# 测试3: 多驱动
TEST3 = '''module t;
    logic a, b, r;
    assign r = a;
    always_comb begin
        r = b;
    end
endmodule'''

tests = [("Unused Signals", TEST1), ("Normal", TEST2), ("Multiple Drivers", TEST3)]

for name, code in tests:
    print(f"\n{'='*50}")
    print(f"测试: {name}")
    print("="*50)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        linter = SVLinter(parser)
        report = linter.run_all()
        
        print(report.visualize())
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
    finally:
        os.unlink(tmp)
