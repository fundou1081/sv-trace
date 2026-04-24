import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.datapath import DataPathAnalyzer

# Simple pipeline
TEST1 = '''module pipe;
    logic [31:0] data_in, stage1, stage2, data_out;
    logic clk;
    
    always_ff @(posedge clk) begin
        stage1 <= data_in;
        stage2 <= stage1;
        data_out <= stage2;
    end
endmodule'''

# Multi-stage pipeline
TEST2 = '''module multi_stage;
    logic [31:0] din, stage1, stage2, stage3, dout;
    logic clk, rst, valid;
    
    always_ff @(posedge clk) begin
        if (rst) begin
            stage1 <= 0;
            stage2 <= 0;
            stage3 <= 0;
        end else if (valid) begin
            stage1 <= din;
            stage2 <= stage1;
            stage3 <= stage2;
        end
    end
    
    assign dout = stage3;
endmodule'''

for name, test in [("Simple Pipeline", TEST1), ("Multi-Stage", TEST2)]:
    print(f"=== {name} ===")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(test)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        analyzer = DataPathAnalyzer(parser)
        
        # 分析整个模块
        dp = analyzer.analyze_module()
        print(dp.visualize())
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
    finally:
        os.unlink(tmp)
    print()
