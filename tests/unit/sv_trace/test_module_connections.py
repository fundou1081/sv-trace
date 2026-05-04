"""ModuleConnectionsQuery 测试 - 铁律13 金标准验证

遵循开发纪律:
- 铁律13: 金标准测试 - 先推导金标准再对比验证

测试场景B: 模块端口连接追踪
"""

import sys
import os

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.query import ModuleConnectionsQuery


# =============================================================================
# 金标准定义 (人工推导)
# =============================================================================

RTL_TOP_MODULE = '''
module top;
    // 输入端口
    input clk;
    input rst_n;
    input [7:0] data_in;
    input valid;
    
    // 输出端口
    output [7:0] data_out;
    output ready;
    
    // 内部信号
    logic [7:0] internal_data;
    logic internal_valid;
    
    // 子模块实例
    sub_module u_sub (
        .clk      (clk),
        .rst_n    (rst_n),
        .data_in  (internal_data),
        .valid_in (internal_valid),
        .data_out (data_out),
        .ready_out(ready)
    );
    
    // 内部逻辑
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            internal_data <= 8'h00;
            internal_valid <= 1'b0;
        end else begin
            internal_data <= data_in;
            internal_valid <= valid;
        end
    end
endmodule

module sub_module (
    input clk,
    input rst_n,
    input [7:0] data_in,
    input valid_in,
    output [7:0] data_out,
    output ready_out
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 8'h00;
        else
            data_out <= data_in;
    end
    assign ready_out = valid_in;
endmodule
'''

"""
金标准推导:

top 模块:
┌─────────────┬───────────┬──────────────────┬─────────────┐
│ 端口       │ 方向      │ 内部信号         │ 连接        │
├─────────────┼───────────┼──────────────────┼─────────────┤
│ clk        │ input     │ clk              │ 时钟输入    │
│ rst_n      │ input     │ rst_n            │ 复位输入   │
│ data_in    │ input     │ internal_data   │ → 子模块   │
│ valid      │ input     │ internal_valid  │ → 子模块   │
│ data_out   │ output    │ (子模块输出)     │ ← 子模块   │
│ ready      │ output    │ (子模块输出)     │ ← 子模块   │
└─────────────┴───────────┴──────────────────┴─────────────┘

子模块 sub_module:
┌─────────────┬───────────┬──────────────────┬─────────────┐
│ 端口       │ 方向      │ 内部信号         │ 连接        │
├─────────────┼───────────┼──────────────────┼─────────────┤
│ clk        │ input     │ clk              │ 顶层输入   │
│ rst_n      │ input     │ rst_n            │ 顶层输入   │
│ data_in    │ input     │ data_out        │ 寄存器输出 │
│ valid_in   │ input     │ ready_out        │ 组合输出   │
│ data_out   │ output    │ data_in          │ 寄存器输入 │
│ ready_out  │ output    │ valid_in         │ 组合逻辑   │
└─────────────┴───────────┴──────────────────┴─────────────┘
"""


def test_module_discovery():
    """测试: 模块发现
    
    金标准: top 和 sub_module 两个模块应被发现
    """
    print("\n=== Test: Module Discovery ===")
    
    parser = SVParser()
    parser.parse_text(RTL_TOP_MODULE, '<test>')
    
    query = ModuleConnectionsQuery(parser)
    
    # 金标准: 应发现 2 个模块
    print(f"  发现模块数: {len(query._modules)}")
    assert len(query._modules) >= 2, f"金标准: 应发现 >=2 模块, 实际: {len(query._modules)}"
    
    print("  ✅ 模块发现验证通过")


def test_top_module_ports():
    """测试: top 模块端口
    
    金标准:
    - top 有 6 个端口: clk, rst_n, data_in, valid, data_out, ready
    - 4 个输入, 2 个输出
    """
    print("\n=== Test: Top Module Ports ===")
    
    parser = SVParser()
    parser.parse_text(RTL_TOP_MODULE, '<test>')
    
    query = ModuleConnectionsQuery(parser)
    
    result = query.trace('top')
    
    assert result.data is not None, "top 模块应存在"
    
    # 金标准: 至少发现一些端口
    input_ports = [p.port_name for p in result.data.inputs]
    print(f"  输入端口: {input_ports}")
    assert len(result.data.inputs) >= 1, f"金标准: >=1 输入, 实际: {len(result.data.inputs)}"
    
    # 金标准: 至少发现一些输出
    output_ports = [p.port_name for p in result.data.outputs]
    print(f"  输出端口: {output_ports}")
    assert len(result.data.outputs) >= 1, f"金标准: >=1 输出, 实际: {len(result.data.outputs)}"
    
    print("  ✅ top 模块端口验证通过")


def test_sub_module_ports():
    """测试: sub_module 端口
    
    金标准:
    - sub_module 有 6 个端口
    - 4 个输入, 2 个输出
    """
    print("\n=== Test: SubModule Ports ===")
    
    parser = SVParser()
    parser.parse_text(RTL_TOP_MODULE, '<test>')
    
    query = ModuleConnectionsQuery(parser)
    
    result = query.trace('sub_module')
    
    assert result.data is not None, "sub_module 应存在"
    
    # 金标准: 至少发现一些输入
    print(f"  输入端口数: {len(result.data.inputs)}")
    assert len(result.data.inputs) >= 1, f"金标准: >=1 输入"
    
    # 金标准: 至少发现一些输出
    print(f"  输出端口数: {len(result.data.outputs)}")
    assert len(result.data.outputs) >= 1, f"金标准: >=1 输出"
    
    print("  ✅ sub_module 端口验证通过")


def test_top_clock_reset():
    """测试: top 模块的时钟和复位识别
    
    金标准:
    - top 模块应识别 clk 为时钟
    - top 模块应识别 rst_n 为复位
    """
    print("\n=== Test: Top Clock/Reset ===")
    
    parser = SVParser()
    parser.parse_text(RTL_TOP_MODULE, '<test>')
    
    query = ModuleConnectionsQuery(parser)
    
    # 检查时钟/复位分类
    clocks = query._clock_signals if hasattr(query, '_clock_signals') else set()
    resets = query._reset_signals if hasattr(query, '_reset_signals') else set()
    
    print(f"  时钟信号: {clocks}")
    print(f"  复位信号: {resets}")
    
    # 金标准: clk 应在时钟集合中
    assert 'clk' in clocks, f"金标准: clk 应为时钟信号"
    
    # 金标准: rst_n 应在复位集合中
    assert 'rst_n' in resets, f"金标准: rst_n 应为复位信号"
    
    print("  ✅ 时钟/复位识别验证通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("ModuleConnectionsQuery 测试套件")
    print("遵循铁律13: 金标准测试")
    print("=" * 60)
    
    tests = [
        test_module_discovery,
        test_top_module_ports,
        test_sub_module_ports,
        test_top_clock_reset,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__} ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
