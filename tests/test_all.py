"""
全面测试 - 测试所有模块
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import (
    SVParser, 
    ParameterResolver,
    ClassExtractor,
    ConstraintExtractor,
    CovergroupExtractor,
    AssertionExtractor,
)
from query import SignalQuery
from trace import DriverTracer, LoadTracer
from trace.connection import ConnectionTracer


def test_parse():
    """基础解析测试"""
    print("=" * 50)
    print("Test: 基础解析")
    print("=" * 50)
    
    code = '''module top(input clk, input [7:0] data); endmodule'''
    parser = SVParser()
    parser.parse_text(code)
    
    assert parser.trees, "解析失败"
    print("✓ 基础解析 OK")
    return True


def test_parameter():
    """Parameter 测试"""
    print("\n" + "=" * 50)
    print("Test: Parameter")
    print("=" * 50)
    
    code = '''module mem #(parameter ADDR_W = 8, parameter DATA_W = 16) (input clk); endmodule'''
    parser = SVParser()
    parser.parse_text(code)
    
    resolver = ParameterResolver(parser)
    
    assert resolver.get_param("ADDR_W").resolved_value == 8, "ADDR_W 解析失败"
    assert resolver.get_param("DATA_W").resolved_value == 16, "DATA_W 解析失败"
    
    print(f"✓ ADDR_W = {resolver.get_param('ADDR_W').resolved_value}")
    print(f"✓ DATA_W = {resolver.get_param('DATA_W').resolved_value}")
    return True


def test_signal_query():
    """SignalQuery 测试"""
    print("\n" + "=" * 50)
    print("Test: SignalQuery")
    print("=" * 50)
    
    code = '''module top(input clk, input [7:0] data, output [7:0] out); endmodule'''
    parser = SVParser()
    parser.parse_text(code)
    
    sq = SignalQuery(parser)
    
    sig = sq.find_signal('data')
    assert sig is not None, "未找到 data"
    assert sig.width == 8, f"data width 应为 8，实际为 {sig.width}"
    
    print(f"✓ clk: width = {sq.find_signal('clk').width}")
    print(f"✓ data: width = {sq.find_signal('data').width}")
    print(f"✓ out: width = {sq.find_signal('out').width}")
    return True


def test_driver():
    """DriverTracer 测试"""
    print("\n" + "=" * 50)
    print("Test: DriverTracer")
    print("=" * 50)
    
    code = '''
module top;
    logic a, b, c;
    assign c = a + b;
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    tracer = DriverTracer(parser)
    drivers = tracer.find_driver('c')
    
    assert len(drivers) > 0, "未找到 driver"
    print(f"✓ c 的驱动: {len(drivers)}")
    for d in drivers:
        print(f"  - {d}")
    return True


def test_load():
    """LoadTracer 测试"""
    print("\n" + "=" * 50)
    print("Test: LoadTracer")
    print("=" * 50)
    
    code = '''
module top;
    logic a, b, c;
    assign c = a + b;
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    tracer = LoadTracer(parser)
    loads = tracer.find_load('a')
    
    print(f"✓ a 的负载: {len(loads)}")
    for l in loads:
        print(f"  - {l}")
    return True


def test_class():
    """ClassExtractor 测试"""
    print("\n" + "=" * 50)
    print("Test: ClassExtractor")
    print("=" * 50)
    
    code = '''
class packet;
    rand logic [7:0] data;
    function bit compare(packet other);
    endfunction
endclass
'''
    parser = SVParser()
    parser.parse_text(code)
    
    extractor = ClassExtractor(parser)
    
    cls = extractor.find_class("packet")
    assert cls is not None, "未找到 packet class"
    assert len(cls["members"]) >= 1, "未找到成员"
    assert len(cls["methods"]) >= 1, "未找到方法"
    
    print(f"✓ Class: packet, members={len(cls['members'])}, methods={len(cls['methods'])}")
    return True


def test_constraint():
    """ConstraintExtractor 测试"""
    print("\n" + "=" * 50)
    print("Test: ConstraintExtractor")
    print("=" * 50)
    
    code = '''
class packet;
    rand logic [7:0] data;
    constraint addr_range {
        data inside {[0:255]};
    }
endclass
'''
    parser = SVParser()
    parser.parse_text(code)
    
    extractor = ConstraintExtractor(parser)
    
    constraints = extractor.find_constraints("packet")
    assert len(constraints) >= 1, "未找到 constraint"
    
    print(f"✓ Constraints: {len(constraints)}")
    for c in constraints:
        print(f"  - {c.name}: {len(c.constraints)} items")
    return True


def test_covergroup():
    """CovergroupExtractor 测试"""
    print("\n" + "=" * 50)
    print("Test: CovergroupExtractor")
    print("=" * 50)
    
    code = '''
covergroup mem_cg;
    coverpoint data { bins zero = {0}; }
endgroup
'''
    parser = SVParser()
    parser.parse_text(code)
    
    extractor = CovergroupExtractor(parser)
    
    cg = extractor.find_covergroup("mem_cg")
    assert cg is not None, "未找到 covergroup"
    assert len(cg.coverpoints) >= 1, "未找到 coverpoint"
    
    print(f"✓ Covergroup: {cg.name}, coverpoints={len(cg.coverpoints)}")
    for cp in cg.coverpoints:
        print(f"  - {cp.name}: {cp.bins}")
    return True


def test_assertion():
    """AssertionExtractor 测试"""
    print("\n" + "=" * 50)
    print("Test: AssertionExtractor")
    print("=" * 50)
    
    code = '''
module tb;
    assert property (@posedge clk) req |-> ##1 ack);
    sequence req_ack;
        req ##[1:3] ack;
    endsequence
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    extractor = AssertionExtractor(parser)
    
    assertions = extractor.get_all_assertions()
    sequences = extractor.get_all_sequences()
    
    print(f"✓ Assertions: {len(assertions)}")
    print(f"✓ Sequences: {len(sequences)}")
    return True


def test_connection():
    """ConnectionTracer 测试"""
    print("\n" + "=" * 50)
    print("Test: ConnectionTracer")
    print("=" * 50)
    
    code = '''
module top;
    mem u_mem (.clk(clk), .addr(addr));
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    tracer = ConnectionTracer(parser)
    
    inst = tracer.find_instance("u_mem")
    assert inst is not None, "未找到实例"
    assert len(inst.connections) >= 1, "未找到连接"
    
    print(f"✓ Instance: {inst.name} ({inst.module_type})")
    for conn in inst.connections:
        print(f"  - .{conn.dest} -> {conn.signal}")
    return True


def main():
    print("\n" + "=" * 50)
    print("SV Trace 全面测试")
    print("=" * 50)
    
    tests = [
        test_parse,
        test_parameter,
        test_signal_query,
        test_driver,
        test_load,
        test_class,
        test_constraint,
        test_covergroup,
        test_assertion,
        test_connection,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"结果: {passed} passed, {failed} failed")
    print("=" * 50)


if __name__ == "__main__":
    main()
