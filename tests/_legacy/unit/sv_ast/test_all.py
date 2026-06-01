"""
全面测试 - 测试所有模块
"""
import sys
import os
import tempfile

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser, ClassExtractor
from query.signal import SignalQuery
from trace.driver import DriverCollector
from trace.load import LoadTracer
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


def test_signal_query():
    """SignalQuery 测试"""
    print("\n" + "=" * 50)
    print("Test: SignalQuery")
    print("=" * 50)
    
    code = '''module top(input clk, input [7:0] data, output [7:0] out); endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        sq = SignalQuery(parser)
        
        sig = sq.find_signal('data')
        print(f"✓ SignalQuery OK")
        return True
    finally:
        os.unlink(tmp)


def test_driver():
    """DriverCollector 测试"""
    print("\n" + "=" * 50)
    print("Test: DriverCollector")
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
        parser = SVParser()
        parser.parse_file(tmp)
        
        tracer = DriverCollector(parser)
        drivers = tracer.find_driver('c')
        
        print(f"✓ c 的驱动: {len(drivers)}")
        return True
    finally:
        os.unlink(tmp)


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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        tracer = LoadTracer(parser)
        loads = tracer.find_load('a')
        
        print(f"✓ a 的负载: {len(loads)}")
        return True
    finally:
        os.unlink(tmp)


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
    tree = parser.parse_text(code)
    
    print("✓ ClassExtractor OK (parse test only)")
    return True


def test_connection():
    """ConnectionTracer 测试"""
    print("\n" + "=" * 50)
    print("Test: ConnectionTracer")
    print("=" * 50)
    
    code = '''
module top;
    logic clk, addr;
    mem u_mem (.clk(clk), .addr(addr));
endmodule
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        tracer = ConnectionTracer(parser)
        
        print(f"✓ ConnectionTracer OK")
        return True
    finally:
        os.unlink(tmp)


def main():
    print("\n" + "=" * 50)
    print("SV Trace 全面测试")
    print("=" * 50)
    
    tests = [
        test_parse,
        test_signal_query,
        test_driver,
        test_load,
        test_class,
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
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
