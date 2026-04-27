import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""测试控制流分析和信号依赖分析"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.controlflow import ControlFlowTracer
from trace.dependency import DependencyAnalyzer


TEST_CODE = """
module top;
    logic [7:0] a;
    logic [7:0] b;
    logic [7:0] result;
    logic enable;
    logic sel;
    
    // 简单 assign
    assign result = a + b;
    
    // always_comb 中的 if
    always_comb begin
        if (enable) begin
            result = a;
        end else begin
            result = b;
        end
    end
    
    // always_ff 中的 if
    logic [7:0] reg_data;
    always_ff @(posedge clk) begin
        if (sel)
            reg_data <= a;
        else
            reg_data <= b;
    end
    
    // case 语句
    logic [1:0] mode;
    logic [7:0] out;
    always_comb begin
        case (mode)
            2'b00: out = a;
            2'b01: out = b;
            default: out = 8'h0;
        endcase
    end
endmodule
"""


def test_control_flow():
    print("=== Control Flow Test ===\n")
    
    parser = SVParser()
    parser.parse_text(TEST_CODE)
    
    tracer = ControlFlowTracer(parser)
    
    # 测试 result 的控制流
    flow = tracer.find_control_dependencies("result")
    print(f"Signal: result")
    print(f"  Controlling: {flow.controlling_signals}")
    print(f"  Dependent: {flow.dependent_signals}")
    print(f"  Conditions: {len(flow.conditions)}")
    
    # 可视化
    print("\n" + tracer.visualize_control_flow("result"))
    
    # 测试 reg_data
    print("\n" + tracer.visualize_control_flow("reg_data"))
    
    # 测试 out (case)
    print("\n" + tracer.visualize_control_flow("out"))


def test_dependency():
    print("\n=== Dependency Test ===\n")
    
    parser = SVParser()
    parser.parse_text(TEST_CODE)
    
    analyzer = DependencyAnalyzer(parser)
    
    # 分析 result 的依赖
    print("Signal: result")
    print(analyzer.visualize("result"))
    
    # 分析 reg_data
    print("\n" + analyzer.visualize("reg_data"))


def test_tiny_gpu():
    print("\n=== Tiny-GPU Real Project Test ===\n")
    
    parser = SVParser()
    files = [
        "/Users/fundou/my_dv_proj/tiny-gpu/src/core.sv",
        "/Users/fundou/my_dv_proj/tiny-gpu/src/alu.sv",
    ]
    
    for f in files:
        parser.parse_file(f)
    
    analyzer = DependencyAnalyzer(parser)
    
    # 尝试分析一个信号
    dep = analyzer.analyze("current_pc")
    print(f"current_pc:")
    print(f"  Depends on: {dep.depends_on[:5]}")
    print(f"  Influences: {dep.influences[:5]}")


if __name__ == "__main__":
    test_control_flow()
    test_dependency()
    test_tiny_gpu()
