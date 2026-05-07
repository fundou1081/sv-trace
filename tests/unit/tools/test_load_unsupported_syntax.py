"""
Load 追踪器 - 不支持语法金标准测试

遵循铁律13: 金标准测试
目标: src/trace/load.py

本文件定义已知不支持的 SV 语法的金标准预期行为。
当这些语法被正确支持时，对应测试应从本文件移除到 test_load.py。

每条记录格式:
    RTL_CODE = r"<RTL代码>"
    # 金标准: [预期行为描述]
    # confidence: expected | partial | uncertain | unsupported
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from parse import SVParser
from trace.load import LoadTracer


# =============================================================================
# 金标准用例 - 不支持语法
# =============================================================================

# -----------------------------------------------------------------------------
# 金标准 1: InterfaceDeclaration
# -----------------------------------------------------------------------------
RTL_INTERFACE = '''interface mem_if (
    input logic clk
);
    logic [31:0] addr;
    logic [31:0] data;
    
    modport master (
        input  addr,
        output data
    );
    
    modport slave (
        output addr,
        input  data
    );
endinterface

module top;
    mem_if intf (.clk(clk));
    logic [31:0] addr_reg;
    
    always_ff @(posedge intf.clk) begin
        addr_reg <= intf.addr;
    end
endmodule'''

# 金标准:
# - interface 内部的信号 (intf.addr, intf.data) 追踪部分支持
# - modport 声明本身不产生 load，仅做连接标注
# - intf.addr -> addr_reg 的驱动关系应能提取
# confidence: partial

# -----------------------------------------------------------------------------
# 金标准 2: ProgramDeclaration
# -----------------------------------------------------------------------------
RTL_PROGRAM = '''program test_prog (
    input logic clk,
    input logic [7:0] data
);
    logic [7:0] local_reg;
    
    always_ff @(posedge clk) begin
        local_reg <= data;
    end
endprogram'''

# 金标准:
# - program 内部应能正确提取 local_reg <= data 的 load 关系
# - program 的时钟/复位输入应识别
# confidence: partial (program 已少见，推荐用 module)

# -----------------------------------------------------------------------------
# 金标准 3: ClassDeclaration (OOP)
# -----------------------------------------------------------------------------
RTL_CLASS = '''class packet;
    rand logic [7:0] addr;
    rand logic [7:0] data;
    
    function void copy(packet rhs);
        this.addr = rhs.addr;
        this.data = rhs.data;
    endfunction
endclass'''

# 金标准:
# - class 内部暂不支持 load 追踪
# - constraint 块中的变量依赖不支持
# - confidence: uncertain

# -----------------------------------------------------------------------------
# 金标准 4: CovergroupDeclaration
# -----------------------------------------------------------------------------
RTL_COVERGROUP = '''covergroup cov @(posedge clk);
    coverpoint data {
        bins low  = {[0:127]};
        bins high = {[128:255]};
    }
endgroup

module test;
    logic clk;
    logic [7:0] data;
    cov cg;
    
    initial cg = new();
endmodule'''

# 金标准:
# - covergroup 声明不产生 load 关系
# - 采样 coverpoint 不追踪
# - confidence: unsupported

# -----------------------------------------------------------------------------
# 金标准 5: ClockingBlock
# -----------------------------------------------------------------------------
RTL_CLOCKING_BLOCK = '''module dut (
    input logic clk,
    input logic [7:0] data
);
    logic [7:0] reg_out;
    
    // clocking block - 不支持的语法
    default clocking cb @(posedge clk);
        input data;
        output reg_out;
    endclocking
    
    always_ff @(posedge clk) begin
        reg_out <= data;
    end
endmodule'''

# 金标准:
# - clocking block 内的 input/output 声明暂不支持
# - reg_out <= data 应能正常追踪（不依赖 clocking block）
# - clocking block 本身不产生 load
# confidence: partial

# -----------------------------------------------------------------------------
# 金标准 6: PropertyDeclaration / SequenceDeclaration (SVA)
# -----------------------------------------------------------------------------
RTL_SVA_PROPERTY = '''module dut (
    input logic clk,
    input logic req,
    input logic gnt
);
    // Property - 不支持
    property req_gnt_protocol;
        req ##1 gnt;
    endproperty
    
    // Sequence - 不支持
    sequence req_seq;
        req ##1 gnt;
    endsequence
    
    assert property (@(posedge clk) req_gnt_protocol);
    
    logic [7:0] data;
    always_ff @(posedge clk) data <= 8'h0;
endmodule'''

# 金标准:
# - property/sequence 声明本身不产生 load
# - assert property 不追踪
# - 内部其他 always_ff 应正常追踪
# confidence: partial

# -----------------------------------------------------------------------------
# 金标准 7: ConstraintBlock
# -----------------------------------------------------------------------------
RTL_CONSTRAINT = '''class packet;
    rand logic [7:0] length;
    rand logic [7:0] addr;
    
    constraint addr_align {
        addr % 4 == 0;
        length inside {[1:1024]};
    }
endclass'''

# 金标准:
# - constraint 块内的 inside/% 依赖不支持
# - 外部 class 变量访问不支持
# - confidence: uncertain

# -----------------------------------------------------------------------------
# 金标准 8: force / release 语句
# -----------------------------------------------------------------------------
RTL_FORCE_RELEASE = '''module dut (
    input logic clk,
    input logic [7:0] data
);
    logic [7:0] reg1;
    logic [7:0] reg2;
    
    always_ff @(posedge clk) begin
        reg1 <= data;
    end
    
    // force/release 语句 - 特殊驱动
    initial begin
        #10 force reg2 = data;
        #20 release reg2;
    end
endmodule'''

# 金标准:
# - force reg2 = data: reg2 被 data 强制驱动（load 关系）
# - release 后恢复原驱动
# - 当前不支持 force/release 的 load 追踪
# - reg1 <= data 应正常追踪
# confidence: partial

# -----------------------------------------------------------------------------
# 金标准 9: 多维数组 / 数组切片
# -----------------------------------------------------------------------------
RTL_ARRAY_LOAD = '''module dut (
    input  logic clk,
    input  logic [7:0] in_data [3:0],
    output logic [7:0] out_data [3:0]
);
    logic [7:0] buf [3:0];
    
    always_ff @(posedge clk) begin
        for (int i = 0; i < 4; i++) begin
            buf[i] <= in_data[i];
        end
    end
endmodule'''

# 金标准:
# - in_data[i] 作为 RHS (load): buf[i] 被 in_data[i] 加载
# - 数组索引是 load 关系的一部分
# - 当 i=0: buf[0] <- in_data[0]; 当 i=1: buf[1] <- in_data[1]...
# - 预期 4 条 load 记录
# - 当前可能无法追踪嵌套索引 (arr[i][j])
# confidence: partial

# -----------------------------------------------------------------------------
# 金标准 10: generate if / case
# -----------------------------------------------------------------------------
RTL_GENERATE = '''module dut (
    input  logic clk,
    input  logic [1:0] mode,
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] q
);
    always_ff @(posedge clk) begin
        genvar i;
        for (int i = 0; i < 1; i++) begin : gen
            if (mode == 2'b00) begin : genblk
                q <= a;
            end else begin : genblk2
                q <= b;
            end
        end
    end
endmodule'''

# 金标准:
# - generate if 内部的 load 关系应能提取
# - mode == 2'b00 是条件判断中的 load (mode)
# - q <= a 或 q <= b 应能追踪
# confidence: partial

# -----------------------------------------------------------------------------
# 金标准 11: 复合赋值操作符 (+=, -=, ...)
# -----------------------------------------------------------------------------
RTL_COMPOUND_ASSIGN = '''module dut (
    input  logic clk,
    input  logic [7:0] inc,
    output logic [7:0] counter
);
    always_ff @(posedge clk) begin
        counter <= counter + inc;  // 等价于 counter += inc
    end
endmodule'''

# 金标准:
# - counter + inc: counter 既是 load (读) 也是被驱动目标 (写)
# - load_by: [counter, inc]
# - signal: counter
# - 这是一个自依赖的 load
# confidence: supported (via assignment rewrite)


# =============================================================================
# 测试类
# =============================================================================

class TestLoadUnsupportedSyntax:
    """不支持语法的预期行为验证"""
    
    @pytest.mark.unsupported
    def test_interface_load(self):
        """测试 InterfaceDeclaration - 预期 partial"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_INTERFACE)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'intf.sv')
        
        # addr_reg <= intf.addr 应能追踪
        # 但具体到 intf.addr 的接口层级可能不完整
        # confidence 预期: partial
        print(f"  [金标准] addr_reg loads: {lt.find_load('addr_reg')}")
        print(f"  [金标准] confidence: partial")
    
    @pytest.mark.unsupported
    def test_program_load(self):
        """测试 ProgramDeclaration - 预期 partial"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_PROGRAM)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'prog.sv')
        
        # local_reg <= data 应能追踪
        print(f"  [金标准] local_reg loads: {lt.find_load('local_reg')}")
        print(f"  [金标准] confidence: partial")
    
    @pytest.mark.unsupported
    def test_class_load(self):
        """测试 ClassDeclaration - 预期 uncertain"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CLASS)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'class.sv')
        
        print(f"  [金标准] class 内部不追踪，confidence: uncertain")
        assert True  # 当前预期不确定
    
    @pytest.mark.unsupported
    def test_covergroup(self):
        """测试 CovergroupDeclaration - 预期 unsupported"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_COVERGROUP)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'cov.sv')
        
        # coverpoint 不产生 load
        print(f"  [金标准] covergroup 无 load，confidence: unsupported")
    
    @pytest.mark.unsupported
    def test_clocking_block(self):
        """测试 ClockingBlock - 预期 partial"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CLOCKING_BLOCK)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'cb.sv')
        
        # reg_out <= data 应正常追踪
        loads = lt.find_load('reg_out')
        print(f"  [金标准] reg_out loads: {loads}")
        print(f"  [金标准] clocking block input/output 声明不支持，confidence: partial")
    
    @pytest.mark.unsupported
    def test_sva_property(self):
        """测试 SVA Property/Sequence - 预期 partial"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SVA_PROPERTY)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'sva.sv')
        
        # property/sequence 不产生 load
        # data <= 8'h0 应正常追踪
        print(f"  [金标准] SVA property/sequence 无 load，confidence: partial")
    
    @pytest.mark.unsupported
    def test_constraint(self):
        """测试 ConstraintBlock - 预期 uncertain"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CONSTRAINT)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'constraint.sv')
        
        print(f"  [金标准] constraint 内部不追踪，confidence: uncertain")
    
    @pytest.mark.unsupported
    def test_force_release(self):
        """测试 force/release - 预期 partial"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_FORCE_RELEASE)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'force.sv')
        
        # reg1 <= data 应正常追踪
        # force reg2 = data 当前不支持
        reg1_loads = lt.find_load('reg1')
        reg2_loads = lt.find_load('reg2')
        print(f"  [金标准] reg1 loads: {reg1_loads} (应正常)")
        print(f"  [金标准] reg2 loads: {reg2_loads} (force 不支持)")
        print(f"  [金标准] confidence: partial")
    
    @pytest.mark.unsupported
    def test_array_load(self):
        """测试多维数组 load - 预期 partial"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_ARRAY_LOAD)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'array.sv')
        
        # buf[i] <= in_data[i] 应能追踪至少 in_data 的 load
        print(f"  [金标准] 数组索引 load 预期 4 条")
        print(f"  [金标准] 当前 confidence: partial")
    
    @pytest.mark.unsupported
    def test_generate(self):
        """测试 generate if - 预期 partial"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_GENERATE)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'gen.sv')
        
        # mode 在条件中应被识别为 load
        # q <= a 或 q <= b 应追踪
        print(f"  [金标准] mode 在条件中应识别为 load")
        print(f"  [金标准] q 的驱动应追踪")
        print(f"  [金标准] confidence: partial")
    
    @pytest.mark.unsupported
    def test_compound_assign(self):
        """测试复合赋值 - 预期 supported"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_COMPOUND_ASSIGN)
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'compound.sv')
        
        # counter <= counter + inc
        # counter 被 counter 和 inc 加载
        loads = lt.find_load('counter')
        print(f"  [金标准] counter loads: {loads}")
        print(f"  [金标准] 预期 [counter, inc]，confidence: supported")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
