import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.datapath import DataPathAnalyzer

# 完整流水线测试
tests = [
    ("3-Stage Pipeline", '''module pipe3;
        logic [31:0] din, s1, s2, dout;
        logic clk;
        always_ff @(posedge clk) begin
            s1 <= din;
            s2 <= s1;
            dout <= s2;
        end
    endmodule''', 'dout'),
    
    ("With Enable", '''module pipe_en;
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
    
    ("With Reset", '''module pipe_rst;
        logic [31:0] din, s1, s2, dout;
        logic clk, rst;
        always_ff @(posedge clk) begin
            if (rst) begin
                s1 <= 0; s2 <= 0; dout <= 0;
            end else begin
                s1 <= din; s2 <= s1; dout <= s2;
            end
        end
    endmodule''', 'dout'),
]

for name, code, sig in tests:
    print(f"=== {name} ===")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        analyzer = DataPathAnalyzer(parser)
        dp = analyzer.analyze(sig)
        print(dp.visualize())
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
    finally:
        os.unlink(tmp)
    print()
