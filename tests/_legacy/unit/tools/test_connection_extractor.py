"""ConnectionExtractor 金标准测试

测试 ConnectionExtractor 从 AST 提取端口连接关系的能力。

符合铁律:
- 铁律13: 金标准测试 (先推导、后验证)
- 铁律18: 继承 Extractor 基类，接收 ScopeTree + SymbolTable
"""

import pytest
from parse import SVParser
from scope.builder import ScopeBuilder
from extractors.base import SemanticGraph
from extractors.connection import ConnectionExtractor


# =============================================================================
# RTL 代码片段
# =============================================================================

RTL_SIMPLE_INSTANCE = '''module top(
    input clk,
    input [7:0] data,
    output [7:0] q
);
    sub #(.DEPTH(8)) u_sub(
        .clk(clk),
        .din(data),
        .dout(q)
    );
endmodule

module sub(
    input clk,
    input [7:0] din,
    output [7:0] dout
);
    parameter DEPTH = 4;
    always_ff @(posedge clk) dout <= din;
endmodule'''

RTL_HIERARCHY = '''module top();
    level1 u_l1(.clk(clk));
endmodule

module level1(
    input clk
);
    level2 u_l2(.clk(clk));
endmodule

module level2(
    input clk
);
endmodule'''

RTL_GEN_FOR = '''module top(
    input clk
);
    genvar i;
    for (i = 0; i < 4; i = i + 1) begin : GEN
        buffer #(.IDX(i)) u_buf (.clk(clk));
    end
endmodule

module buffer(
    input clk
);
    parameter IDX = 0;
endmodule'''

RTL_GEN_IF = '''module top(
    input cond,
    input clk
);
    if (cond) begin : GEN_IF
        sub #(.P(1)) u_sub1(.clk(clk));
    end else begin
        sub #(.P(2)) u_sub2(.clk(clk));
    end
endmodule

module sub(
    input logic clk
);
    parameter P = 0;
endmodule'''

RTL_LITERAL_FILTER = '''module top();
    sub #(.WIDTH(32'hA5A5A5A5)) u_sub(.data(32'hdeadbeef));
endmodule

module sub(
    input [31:0] data
);
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestConnectionExtractorSimple:
    """简单实例连接测试"""
    
    @pytest.mark.unit
    def test_simple_instance(self):
        """测试简单模块实例连接
        
        验证: ConnectionExtractor 能从 AST 提取命名端口连接
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SIMPLE_INSTANCE)
        
        # Pass 1: ScopeBuilder
        builder = ScopeBuilder()
        scope_tree, symbol_table = builder.build(tree)
        
        # Pass 2: ConnectionExtractor
        graph = SemanticGraph(scope_tree, symbol_table)
        extractor = ConnectionExtractor(scope_tree, symbol_table, graph)
        extractor.extract(tree)
        
        # 验证有连接关系 (核心断言)
        assert len(graph.connections) > 0, \
            f"ConnectionExtractor 应该提取到连接关系，实际: {len(graph.connections)}"
        
        # 验证连接属性完整性
        for conn in graph.connections:
            assert conn.to_instance, f"连接应该有 to_instance: {conn}"
            assert conn.to_port, f"连接应该有 to_port: {conn}"
            assert conn.signal, f"连接应该有 signal: {conn}"
    
    @pytest.mark.unit
    def test_hierarchy(self):
        """测试多层模块层次
        
        验证: ConnectionExtractor 能正确处理嵌套模块实例化
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_HIERARCHY)
        
        builder = ScopeBuilder()
        scope_tree, symbol_table = builder.build(tree)
        
        graph = SemanticGraph(scope_tree, symbol_table)
        extractor = ConnectionExtractor(scope_tree, symbol_table, graph)
        extractor.extract(tree)
        
        # 验证有连接
        assert len(graph.connections) > 0, \
            f"应该有连接关系，实际: {len(graph.connections)}"
    
    @pytest.mark.unit
    def test_connection_properties(self):
        """测试连接属性正确性
        
        验证: 连接对象的所有字段都正确填充
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SIMPLE_INSTANCE)
        
        builder = ScopeBuilder()
        scope_tree, symbol_table = builder.build(tree)
        
        graph = SemanticGraph(scope_tree, symbol_table)
        extractor = ConnectionExtractor(scope_tree, symbol_table, graph)
        extractor.extract(tree)
        
        # 验证连接数量
        assert len(graph.connections) == 3, \
            f"应该有 3 个连接 (.clk, .din, .dout)，实际: {len(graph.connections)}"
        
        # 验证每个连接都有完整信息
        port_names = [conn.to_port for conn in graph.connections]
        assert 'clk' in port_names, f"应该有 clk 连接，实际: {port_names}"
        assert 'din' in port_names, f"应该有 din 连接，实际: {port_names}"
        assert 'dout' in port_names, f"应该有 dout 连接，实际: {port_names}"
        
        # 验证 signal 非空
        for conn in graph.connections:
            assert conn.signal, f"signal 不应该为空: {conn}"


class TestConnectionExtractorGenerate:
    """Generate 块内实例化测试"""
    
    @pytest.mark.unit
    def test_gen_for_instance(self):
        """测试 generate for 块内实例化
        
        验证: ConnectionExtractor 能处理 generate for 块内的模块实例化
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_GEN_FOR)
        
        builder = ScopeBuilder()
        scope_tree, symbol_table = builder.build(tree)
        
        graph = SemanticGraph(scope_tree, symbol_table)
        extractor = ConnectionExtractor(scope_tree, symbol_table, graph)
        extractor.extract(tree)
        
        # 验证有连接 (generate 块内实例也应该被提取)
        assert len(graph.connections) > 0, \
            f"generate for 块内实例应该有连接，实际: {len(graph.connections)}"
    
    @pytest.mark.unit
    def test_gen_if_instance(self):
        """测试 generate if 块内实例化
        
        验证: ConnectionExtractor 能处理 generate if 块内的模块实例化
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_GEN_IF)
        
        builder = ScopeBuilder()
        scope_tree, symbol_table = builder.build(tree)
        
        graph = SemanticGraph(scope_tree, symbol_table)
        extractor = ConnectionExtractor(scope_tree, symbol_table, graph)
        extractor.extract(tree)
        
        # 验证有连接 (generate if 块内实例也应该被提取)
        assert len(graph.connections) > 0, \
            f"generate if 块内实例应该有连接，实际: {len(graph.connections)}"
        
        # 验证有多个实例的连接
        inst_names = list(set(conn.to_instance for conn in graph.connections))
        assert len(inst_names) >= 2, \
            f"应该有至少 2 个实例的连接，实际: {inst_names}"


class TestConnectionExtractorLiteralFilter:
    """Spurious literal-value 过滤测试"""
    
    @pytest.mark.unit
    def test_literal_filter(self):
        """测试字面量值过滤
        
        验证: ConnectionExtractor 正确过滤基于 literal-value 的连接 (spurious nodes)
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_LITERAL_FILTER)
        
        builder = ScopeBuilder()
        scope_tree, symbol_table = builder.build(tree)
        
        graph = SemanticGraph(scope_tree, symbol_table)
        extractor = ConnectionExtractor(scope_tree, symbol_table, graph)
        extractor.extract(tree)
        
        # 检查没有 spurious literal-value connections
        for conn in graph.connections:
            assert not extractor._is_literal_value(conn.from_port), \
                f"from_port 不应该是 literal-value: {conn.from_port}"
            assert not extractor._is_literal_value(conn.to_port), \
                f"to_port 不应该是 literal-value: {conn.to_port}"


class TestConnectionExtractorIntegration:
    """集成测试"""
    
    @pytest.mark.unit
    def test_simple_rtl(self):
        """测试简单 RTL 设计
        
        验证: ConnectionExtractor 在完整 RTL 设计上工作正常
        """
        rtl = '''module test(
    input clk,
    input [7:0] a,
    input [7:0] b,
    output [7:0] c
);
    inst u_inst(.clk(clk), .a(a), .b(b), .c(c));
endmodule

module inst(
    input clk,
    input [7:0] a,
    input [7:0] b,
    output [7:0] c
);
    assign c = a + b;
endmodule'''
        
        parser = SVParser(verbose=False)
        tree = parser.parse_text(rtl)
        
        builder = ScopeBuilder()
        scope_tree, symbol_table = builder.build(tree)
        
        graph = SemanticGraph(scope_tree, symbol_table)
        extractor = ConnectionExtractor(scope_tree, symbol_table, graph)
        extractor.extract(tree)
        
        # 验证有连接
        assert len(graph.connections) > 0, \
            f"应该有连接关系，实际: {len(graph.connections)}"
        
        # 验证连接包含实例名
        inst_names = [conn.to_instance for conn in graph.connections]
        assert 'u_inst' in inst_names, \
            f"应该有 'u_inst' 实例的连接，实际: {inst_names}"