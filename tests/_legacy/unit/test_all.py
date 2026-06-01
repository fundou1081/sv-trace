"""全面测试 - 测试所有模块

更新为新架构 (pyslang 重构后的 API)
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sv_manager import SVManager
from parse import SVParser
from parse import ParameterResolver, ClassExtractor, ConstraintExtractor, CovergroupExtractor, AssertionExtractor
from query import SignalQuery
from trace import DriverTracer, LoadTracer
from trace.connection import ConnectionTracer


def test_parse():
    """基础解析测试"""
    print("=" * 50)
    print("Test: 基础解析")
    print("=" * 50)
    
    code = '''module top(input clk, input [7:0] data); endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        assert parser.trees, "解析失败"
        print("✓ 基础解析 OK")
        return True
    finally:
        os.unlink(tmp)


def test_parameter():
    """Parameter 测试 - 使用 SVManager"""
    print("\n" + "=" * 50)
    print("Test: Parameter (SVManager)")
    print("=" * 50)
    
    code = '''module mem #(parameter ADDR_W = 8, parameter DATA_W = 16) (input clk); endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        sv = SVManager()
        sv.parse_file(tmp)
        
        # ParameterResolver 是 stub 实现，需要完整实现才能工作
        resolver = ParameterResolver(sv)
        
        # Stub 返回 None，测试仅验证不报错
        result = resolver.resolve("ADDR_W")
        print(f"✓ ParameterResolver.resolve() 调用成功 (stub 实现)")
        return True
    finally:
        os.unlink(tmp)


def test_signal_query():
    """SignalQuery 测试 - 使用 SVManager"""
    print("\n" + "=" * 50)
    print("Test: SignalQuery (SVManager)")
    print("=" * 50)
    
    code = '''module top(input clk, input [7:0] data, output [7:0] out); endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        sv = SVManager()
        sv.parse_file(tmp)
        
        sq = SignalQuery(sv)
        
        sig = sq.find_signal('data')
        assert sig is not None, "未找到 data"
        assert sig.width == 8, f"data width 应为 8，实际为 {sig.width}"
        
        print(f"✓ clk: width = {sq.find_signal('clk').width}")
        print(f"✓ data: width = {sq.find_signal('data').width}")
        print(f"✓ out: width = {sq.find_signal('out').width}")
        return True
    finally:
        os.unlink(tmp)


def test_driver():
    """DriverTracer 测试 - 使用 SVManager"""
    print("\n" + "=" * 50)
    print("Test: DriverTracer (SVManager)")
    print("=" * 50)
    
    code = '''
module top;
    logic a, b, c;
    assign c = a + b;
endmodule
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        sv = SVManager()
        sv.parse_file(tmp)
        
        # 获取第一个解析的 tree
        tree = list(sv.trees.values())[0] if sv.trees else None
        assert tree is not None, "解析失败"
        
        tracer = DriverTracer()
        tracer.collect(tree, tmp)
        
        # 验证 c 的驱动信息
        drivers_c = tracer.find_driver('c')
        print(f"✓ c 的驱动: {len(drivers_c)}")
        for d in drivers_c:
            print(f"  - {d}")
        
        return True
    finally:
        os.unlink(tmp)


def test_load():
    """LoadTracer 测试 - 使用 SVManager"""
    print("\n" + "=" * 50)
    print("Test: LoadTracer (SVManager)")
    print("=" * 50)
    
    code = '''
module top;
    logic a, b, c;
    assign c = a + b;
endmodule
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        sv = SVManager()
        sv.parse_file(tmp)
        
        # 获取第一个解析的 tree
        tree = list(sv.trees.values())[0] if sv.trees else None
        assert tree is not None, "解析失败"
        
        tracer = LoadTracer()
        tracer.collect(tree, tmp)
        
        # 验证 c 的负载
        loads_c = tracer.find_load('c')
        print(f"✓ c 的负载: {len(loads_c)}")
        for l in loads_c:
            print(f"  - {l}")
        
        return True
    finally:
        os.unlink(tmp)


def test_class():
    """ClassExtractor 测试 - stub"""
    print("\n" + "=" * 50)
    print("Test: ClassExtractor (stub)")
    print("=" * 50)
    
    code = '''
class packet;
    rand logic [7:0] data;
    function bit compare(packet other);
    endfunction
endclass
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        sv = SVManager()
        sv.parse_file(tmp)
        
        # ClassExtractor 是 stub，验证 API 可调用
        extractor = ClassExtractor(sv)
        
        print(f"✓ ClassExtractor 实例化成功 (stub)")
        return True
    finally:
        os.unlink(tmp)


def test_constraint():
    """ConstraintExtractor 测试 - stub"""
    print("\n" + "=" * 50)
    print("Test: ConstraintExtractor (stub)")
    print("=" * 50)
    
    code = '''
class packet;
    rand logic [7:0] data;
    constraint addr_range {
        data inside {[0:255]};
    }
endclass
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        sv = SVManager()
        sv.parse_file(tmp)
        
        # ConstraintExtractor 是 stub，验证 API 可调用
        extractor = ConstraintExtractor()
        
        print(f"✓ ConstraintExtractor 实例化成功 (stub)")
        return True
    finally:
        os.unlink(tmp)


def test_covergroup():
    """CovergroupExtractor 测试 - stub"""
    print("\n" + "=" * 50)
    print("Test: CovergroupExtractor (stub)")
    print("=" * 50)
    
    code = '''
covergroup mem_cg;
    coverpoint data { bins zero = {0}; }
endgroup
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        sv = SVManager()
        sv.parse_file(tmp)
        
        # CovergroupExtractor 是 stub，验证 API 可调用
        extractor = CovergroupExtractor()
        
        print(f"✓ CovergroupExtractor 实例化成功 (stub)")
        return True
    finally:
        os.unlink(tmp)


def test_assertion():
    """AssertionExtractor 测试 - stub"""
    print("\n" + "=" * 50)
    print("Test: AssertionExtractor (stub)")
    print("=" * 50)
    
    code = '''
module tb;
    sequence req_ack;
        req ##[1:3] ack;
    endsequence
endmodule
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        sv = SVManager()
        sv.parse_file(tmp)
        
        # AssertionExtractor 是 stub，验证 API 可调用
        extractor = AssertionExtractor()
        
        print(f"✓ AssertionExtractor 实例化成功 (stub)")
        return True
    finally:
        os.unlink(tmp)


def test_connection():
    """ConnectionTracer 测试 - stub"""
    print("\n" + "=" * 50)
    print("Test: ConnectionTracer (stub)")
    print("=" * 50)
    
    code = '''
module top;
    mem u_mem (.clk(clk), .addr(addr));
endmodule
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        sv = SVManager()
        sv.parse_file(tmp)
        
        # ConnectionTracer 是 stub，验证 API 可调用
        tracer = ConnectionTracer(sv)
        
        print(f"✓ ConnectionTracer 实例化成功 (stub)")
        return True
    finally:
        os.unlink(tmp)


def main():
    print("\n" + "=" * 50)
    print("SV Trace 全面测试 (新架构)")
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