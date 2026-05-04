"""SignalChainQuery 测试

测试场景化查询层的功能：
- 场景A: 信号完整链路追踪 (drivers → loads)

遵循开发纪律铁律7: 新功能必须先有边界测试

测试设计原则：
1. 先阅读源代码理解预期行为
2. 设计测试用例验证这些行为
3. 运行测试检查是否符合预期
"""

import sys
import os
import tempfile

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.query import SignalChainQuery
from trace.load_ext import LoadTracerExt


# ============== 测试数据 ==============

TEST_SINGLE_DRIVER = '''
module top;
  logic clk;
  logic [7:0] data_in;
  logic [7:0] data_out;
  
  always_ff @(posedge clk) begin
    data_out <= data_in;
  end
endmodule
'''

TEST_CONTINUOUS_ASSIGN = '''
module top;
  logic [7:0] a;
  logic [7:0] b;
  
  assign b = a;
endmodule
'''

TEST_COMPLEX_CHAIN = '''
module top;
  logic clk;
  logic rst_n;
  logic [7:0] data_in;
  logic [7:0] temp;
  logic [7:0] data_out;
  
  assign temp = data_in;
  
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      data_out <= 8'b0;
    else
      data_out <= temp;
  end
endmodule
'''

TEST_NO_DRIVER = '''
module top;
  logic [7:0] undriven_signal;
  logic [7:0] driven;
  
  assign driven = undriven_signal;
endmodule
'''

TEST_MIXED_DRIVERS = '''
module top;
  logic clk;
  logic rst;
  logic [7:0] data_in;
  logic [7:0] data_out;
  
  // 多个 always_ff 驱动同一个信号
  always_ff @(posedge clk) begin
    data_out <= data_in;
  end
  
  always @(posedge clk) begin
    if (rst)
      data_out <= 8'hFF;
  end
endmodule
'''


# ============== 辅助函数 ==============

def parse_code(code: str) -> SVParser:
    """解析代码文本"""
    parser = SVParser()
    parser.parse_text(code, '<test>')
    return parser


def assert_result(result, expected_confidence, expected_drivers_min=0, 
                  expected_loads_min=0, test_name=""):
    """断言结果"""
    print(f"  Confidence: {result.confidence}")
    if result.caveats:
        print(f"  Caveats: {result.caveats}")
    
    # 检查置信度
    assert result.confidence == expected_confidence, \
        f"{test_name}: Expected confidence={expected_confidence}, got {result.confidence}"
    
    # 检查数据存在
    assert result.data is not None, \
        f"{test_name}: Expected data, got None"
    
    # 检查 drivers
    actual_drivers = len(result.data.drivers)
    assert actual_drivers >= expected_drivers_min, \
        f"{test_name}: Expected >= {expected_drivers_min} drivers, got {actual_drivers}"
    
    # 检查 loads
    actual_loads = len(result.data.loads)
    assert actual_loads >= expected_loads_min, \
        f"{test_name}: Expected >= {expected_loads_min} loads, got {actual_loads}"
    
    print(f"  ✅ {test_name} 通过")


# ============== 测试用例 ==============

def test_single_driver():
    """测试单驱动场景
    
    预期行为:
    - data_out 被 data_in 驱动 (always_ff)
    - data_in 没有驱动源 (输入)
    - data_in 被 data_out 使用 (load)
    """
    print("\n=== Test: Single Driver ===")
    
    parser = parse_code(TEST_SINGLE_DRIVER)
    query = SignalChainQuery(parser)
    
    # 追踪 data_out - 应该有驱动，无负载
    result = query.trace('data_out', 'top')
    print(f"  Drivers for data_out: {len(result.data.drivers)}")
    for d in result.data.drivers:
        print(f"    - [{d.kind}] sources={d.sources}")
    print(f"  Loads for data_out: {len(result.data.loads)}")
    
    # 预期: 至少 1 个驱动，0 个负载
    assert len(result.data.drivers) >= 1, "data_out should have at least 1 driver"
    assert len(result.data.loads) == 0, "data_out should have 0 loads (no signal uses it)"
    
    # 检查驱动源
    driver_sources = set()
    for d in result.data.drivers:
        driver_sources.update(d.sources)
    assert 'data_in' in driver_sources, "data_out should be driven by data_in"
    
    # 追踪 data_in - 应该无驱动，有负载 (data_out 使用它)
    result2 = query.trace('data_in', 'top')
    print(f"\n  Drivers for data_in: {len(result2.data.drivers)}")
    print(f"  Loads for data_in: {len(result2.data.loads)}")
    for l in result2.data.loads:
        print(f"    - {l.signal}: {l.context}")
    
    # 预期: 0 个驱动 (input)，至少 1 个负载
    assert len(result2.data.drivers) == 0, "data_in should have 0 drivers (it's an input)"
    assert len(result2.data.loads) >= 1, "data_in should have at least 1 load (used by data_out)"
    
    print("  ✅ Single driver test passed")


def test_continuous_assign():
    """测试连续赋值
    
    预期行为:
    - b = a (连续赋值)
    - trace('b') 应该找到驱动 sources=['a']
    """
    print("\n=== Test: Continuous Assignment ===")
    
    parser = parse_code(TEST_CONTINUOUS_ASSIGN)
    query = SignalChainQuery(parser)
    
    result = query.trace('b', 'top')
    print(f"  Drivers for b: {len(result.data.drivers)}")
    for d in result.data.drivers:
        print(f"    - [{d.kind}] sources={d.sources}")
    
    # 预期: 至少 1 个连续赋值驱动
    assert len(result.data.drivers) >= 1, "b should have at least 1 driver"
    
    # 应该有 assign 类型的驱动
    assign_drivers = [d for d in result.data.drivers if d.kind == 'continuous']
    assert len(assign_drivers) >= 1, "b should have at least 1 continuous driver"
    
    # 检查源信号
    for d in assign_drivers:
        if d.sources:
            print(f"    ✅ Found source: {d.sources}")
    
    print("  ✅ Continuous assignment test passed")


def test_complex_chain():
    """测试复杂链路
    
    预期行为:
    - data_out <- temp <- data_in
    - trace('data_out') 应该找到完整链路
    - trace('data_in') 应该找到下游负载
    """
    print("\n=== Test: Complex Chain ===")
    
    parser = parse_code(TEST_COMPLEX_CHAIN)
    query = SignalChainQuery(parser)
    
    # 追踪 data_out
    result = query.trace('data_out', 'top')
    print(f"  Trace data_out:")
    print(f"    Drivers: {len(result.data.drivers)}")
    for d in result.data.drivers:
        print(f"      - [{d.kind}] sources={d.sources}")
    print(f"    Loads: {len(result.data.loads)}")
    print(f"    Data path: {result.data.data_path_signals}")
    
    # 预期: 至少有 2 个驱动 (复位分支 + 主分支)
    assert len(result.data.drivers) >= 2, \
        f"data_out should have >= 2 drivers (reset + main), got {len(result.data.drivers)}"
    
    # 检查 temp 在数据路径中
    assert 'temp' in result.data.data_path_signals, \
        "temp should be in data_path_signals"
    
    # 追踪 data_in
    result2 = query.trace('data_in', 'top')
    print(f"\n  Trace data_in:")
    print(f"    Drivers: {len(result2.data.drivers)}")
    print(f"    Loads: {len(result2.data.loads)}")
    for l in result2.data.loads:
        print(f"      - {l.signal}")
    
    # 预期: 0 个驱动 (输入)，至少 1 个负载
    assert len(result2.data.drivers) == 0, "data_in should have 0 drivers"
    assert len(result2.data.loads) >= 1, "data_in should have at least 1 load"
    
    print("  ✅ Complex chain test passed")


def test_no_driver():
    """测试无驱动信号
    
    预期行为:
    - trace('undriven_signal') 应该返回 uncertain
    """
    print("\n=== Test: No Driver ===")
    
    parser = parse_code(TEST_NO_DRIVER)
    query = SignalChainQuery(parser)
    
    result = query.trace('undriven_signal', 'top')
    print(f"  Confidence: {result.confidence}")
    print(f"  Caveats: {result.caveats}")
    
    # 预期: uncertain (无驱动源)
    assert result.confidence == "uncertain", \
        f"Expected uncertain, got {result.confidence}"
    assert len(result.caveats) > 0, "Should have caveats for undriven signal"
    
    print("  ✅ No driver test passed")


def test_signal_classification():
    """测试信号分类 (时钟/复位)
    
    预期行为:
    - clk 应该被分类为时钟信号
    - rst_n 应该被分类为复位信号
    """
    print("\n=== Test: Signal Classification ===")
    
    parser = parse_code(TEST_COMPLEX_CHAIN)
    query = SignalChainQuery(parser)
    
    print(f"  Clock signals: {query._clock_signals}")
    print(f"  Reset signals: {query._reset_signals}")
    
    # 预期: clk 在时钟集合中
    assert 'clk' in query._clock_signals, "clk should be classified as clock"
    
    # 预期: rst_n 在复位集合中
    assert 'rst_n' in query._reset_signals, "rst_n should be classified as reset"
    
    print("  ✅ Signal classification test passed")


def test_load_tracer_ext():
    """测试 LoadTracerExt 反向查找
    
    预期行为:
    - reverse_lookup('data_in') 应该返回使用 data_in 的信号
    """
    print("\n=== Test: LoadTracerExt Reverse Lookup ===")
    
    parser = parse_code(TEST_SINGLE_DRIVER)
    lt = LoadTracerExt(parser)
    
    # 反向查找: 谁使用 data_in 作为源
    loads = lt.reverse_lookup('data_in')
    print(f"  reverse_lookup('data_in'): {len(loads)} loads")
    for load in loads:
        print(f"    - signal={load.signal}, driver={load.driver}, type={load.driver_type}")
    
    # 预期: data_out 使用 data_in
    assert len(loads) >= 1, "data_in should have at least 1 load"
    
    load_signals = [l.signal for l in loads]
    assert 'data_out' in load_signals, "data_out should use data_in"
    
    print("  ✅ LoadTracerExt test passed")


def test_result_structure():
    """测试结果结构完整性
    
    预期行为:
    - TraceResult 必须包含 confidence 和 caveats
    - SignalChainResult 必须包含所有必需字段
    """
    print("\n=== Test: Result Structure ===")
    
    parser = parse_code(TEST_SINGLE_DRIVER)
    query = SignalChainQuery(parser)
    
    result = query.trace('data_out', 'top')
    
    # 检查 TraceResult 结构
    assert hasattr(result, 'confidence'), "TraceResult should have confidence"
    assert hasattr(result, 'caveats'), "TraceResult should have caveats"
    assert hasattr(result, 'data'), "TraceResult should have data"
    assert result.confidence in ('high', 'medium', 'uncertain'), \
        f"Invalid confidence: {result.confidence}"
    
    # 检查 SignalChainResult 结构
    chain = result.data
    assert chain.root_signal == 'data_out', "root_signal should be data_out"
    assert chain.root_module == 'top', "root_module should be top"
    assert isinstance(chain.drivers, list), "drivers should be list"
    assert isinstance(chain.loads, list), "loads should be list"
    assert isinstance(chain.data_path_signals, list), "data_path_signals should be list"
    
    # 检查 to_dict 方法
    d = chain.to_dict()
    assert 'drivers' in d, "to_dict should include drivers"
    assert 'confidence' in d, "to_dict should include confidence"
    
    print("  ✅ Result structure test passed")


def test_trace_result_api():
    """测试 TraceResult API
    
    预期行为:
    - TraceResult.ok() 应该创建高置信度结果
    - TraceResult.uncertain() 应该创建低置信度结果
    """
    print("\n=== Test: TraceResult API ===")
    
    from trace.core.interfaces import TraceResult
    
    # 测试 ok()
    ok_result = TraceResult.ok({'test': 123})
    assert ok_result.confidence == 'high', "ok() should create high confidence"
    assert ok_result.is_trusted == True, "ok() should be trusted"
    assert ok_result.data == {'test': 123}
    print("  ✅ TraceResult.ok() works")
    
    # 测试 uncertain()
    uncertain_result = TraceResult.uncertain(None, "signal not found")
    assert uncertain_result.confidence == 'uncertain', "uncertain() should create uncertain"
    assert len(uncertain_result.caveats) > 0, "uncertain() should have caveats"
    print("  ✅ TraceResult.uncertain() works")
    
    print("  ✅ TraceResult API test passed")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("SignalChainQuery 测试套件")
    print("=" * 60)
    
    tests = [
        test_single_driver,
        test_continuous_assign,
        test_complex_chain,
        test_no_driver,
        test_signal_classification,
        test_load_tracer_ext,
        test_result_structure,
        test_trace_result_api,
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
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
