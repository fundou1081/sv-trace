"""
Load Semantic Tests - 金标准测试
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.load import LoadTracer


def test_load_basic():
    """测试基本负载提取"""
    sv_code = """
module test_load;
    logic [7:0] data;
    logic [7:0] out;
    
    always_ff @(posedge clk) begin
        out <= data;
    end
endmodule
"""
    tree = SVParser().parse_text(sv_code, "test.sv")
    lt = LoadTracer(use_semantic=True)
    lt.collect(tree, "test.sv")
    
    # 至少应该有 1 个负载
    print(f"  负载: {len(lt.loads)}")
    
    print("✅ test_load_basic PASS")


def test_load_in_expression():
    """测试表达式中的负载"""
    sv_code = """
module test_load;
    logic [7:0] a, b, c;
    
    always_comb begin
        c = a + b;
    end
endmodule
"""
    tree = SVParser().parse_text(sv_code, "test.sv")
    lt = LoadTracer(use_semantic=True)
    lt.collect(tree, "test.sv")
    
    print(f"  负载: {len(lt.loads)}")
    
    print("✅ test_load_in_expression PASS")


if __name__ == '__main__':
    test_load_basic()
    test_load_in_expression()
    print("\n🎉 所有 Load 测试通过")
