"""
Driver 高级复杂语法测试 (TDD)

覆盖: generate, concat, 数组, 多维数组
遵循铁律13: 金标准测试
"""

import pytest
import sys
sys.path.insert(0, 'src')
from parse import SVParser
from trace.driver import DriverCollector


# =============================================================================
# 金标准: Generate 语法
# =============================================================================

# 金标准 G1: generate for 循环
RTL_GEN_FOR = '''module dut(
    input  logic clk,
    input  logic [7:0] data,
    output logic [7:0] q
);
    generate
        for (genvar i = 0; i < 8; i++) begin : gen_loop
            always_ff @(posedge clk)
                q[i] <= data[i];
        end
    endgenerate
endmodule'''
# 预期: q[7:0] 有 8 个驱动


# 金标准 G2: generate if
RTL_GEN_IF = '''module dut(
    input  logic clk,
    input  logic gen_en,
    input  logic [7:0] data,
    output logic [7:0] q
);
    generate
        if (gen_en) begin : gen_block
            always_ff @(posedge clk)
                q <= data;
        end
    endgenerate
endmodule'''
# 预期: gen_en=1 时 q 有驱动


# =============================================================================
# 金标准: 位拼接
# =============================================================================

# 金标准 C1: 简单拼接
RTL_CONCAT = '''module dut(
    input  logic clk,
    input  logic [3:0] a,
    input  logic [3:0] b,
    output logic [7:0] q
);
    always_ff @(posedge clk)
        q <= {a, b};
endmodule'''
# 预期: source = {a, b}


# 金标准 C2: 多重拼接
RTL_CONCAT_MULTI = '''module dut(
    input  logic clk,
    input  logic [1:0] a,
    input  logic [1:0] b,
    input  logic [1:0] c,
    input  logic [1:0] d,
    output logic [7:0] q
);
    always_ff @(posedge clk)
        q <= {{a, b}, {c, d}};
endmodule'''
# 预期: source = {{a, b}, {c, d}}


# =============================================================================
# 金标准: 数组
# =============================================================================

# 金标准 A1: 简单数组
RTL_ARRAY = '''module dut(
    input  logic clk,
    input  logic [2:0] addr,
    input  logic [7:0] data,
    output logic [7:0] q
);
    logic [7:0] mem [0:7];
    
    always_ff @(posedge clk)
        mem[addr] <= data;
    
    assign q = mem[addr];
endmodule'''
# 预期: mem 是数组类型


# 金标准 A2: 数组赋值
RTL_ARRAY_ASSIGN = '''module dut(
    input  logic clk,
    input  logic [7:0] data,
    output logic [7:0] q
);
    logic [7:0] mem [0:3] = '{8'h0, 8'h1, 8'h2, 8'h3};
    
    always_ff @(posedge clk)
        mem[0] <= data;
    
    assign q = mem[0];
endmodule'''
# 预期: mem[0] 有驱动


# =============================================================================
# 金标准: 多维数组
# =============================================================================

# 金标准 M1: 二维数组
RTL_ARRAY_2D = '''module dut(
    input  logic clk,
    input  logic [1:0] row,
    input  logic [1:0] col,
    input  logic [7:0] data,
    output logic [7:0] q
);
    logic [7:0] mem [0:3][0:3];
    
    always_ff @(posedge clk)
        mem[row][col] <= data;
    
    assign q = mem[row][col];
endmodule'''
# 预期: 二维数组驱动


# =============================================================================
# 测试类
# =============================================================================

class TestGenerateSyntax:
    """Generate 语法测试"""
    
    @pytest.mark.unit
    def test_generate_for_loop(self):
        """Generate for 循环"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_GEN_FOR)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.drivers
        print(f"  drivers: {drivers}")
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_generate_if(self):
        """Generate if"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_GEN_IF)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.drivers
        print(f"  drivers: {drivers}")
        assert len(drivers) > 0


class TestConcatSyntax:
    """位拼接语法测试"""
    
    @pytest.mark.unit
    def test_simple_concat(self):
        """简单拼接 {a, b}"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CONCAT)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert len(drivers) > 0
        
        d = drivers['q'][0]
        print(f"  q source: {d.sources}")
        
        # 验证 confidence
        assert d.confidence in ['high', 'medium', 'uncertain']
    
    @pytest.mark.unit
    def test_multi_concat(self):
        """多重拼接 {{a,b},{c,d}}"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CONCAT_MULTI)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  drivers: {len(drivers)}")
        assert len(drivers) > 0


class TestArraySyntax:
    """数组语法测试"""
    
    @pytest.mark.unit
    def test_simple_array(self):
        """简单数组"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_ARRAY)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.drivers
        print(f"  drivers: {drivers}")
        # 数组应该能被检测
    
    @pytest.mark.unit
    def test_array_assignment(self):
        """数组赋值"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_ARRAY_ASSIGN)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.drivers
        print(f"  drivers: {drivers}")
        assert len(drivers) > 0


class TestMultiDimArray:
    """多维数组测试"""
    
    @pytest.mark.unit
    def test_2d_array(self):
        """二维数组"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_ARRAY_2D)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.drivers
        print(f"  drivers: {drivers}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
