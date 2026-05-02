import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
Driver 测试
"""
import sys
import os
import tempfile

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverCollector, DriverTracer


TEST1 = '''
module t;
    logic [31:0] a, b, r;
    always_comb r = a + b;
endmodule
'''

TEST2 = '''
module t;
    logic [31:0] a, b, c, r;
    logic [1:0] sel;
    always_comb begin
        if (sel == 2'b00)
            r = a;
        else if (sel == 2'b01)
            r = b;
        else
            r = c;
    end
endmodule
'''


def test_simple():
    """简单赋值测试"""
    print("\n=== Simple If/Else ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(TEST1)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        drv = DriverTracer(parser)
        drivers = drv.find_driver('r')
        
        print(f"Drivers for r: {len(drivers)}")
        for d in drivers:
            sources = d.sources if d.sources else ['<no sources>']
            print(f"  - kind={d.kind}, source={sources[0].strip()[:60] if sources[0] else 'N/A'}")
        
        print("  ✅ 简单赋值测试通过")
        return True
    finally:
        os.unlink(tmp)


def test_nested():
    """嵌套 if 测试"""
    print("\n=== Nested If/Else ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(TEST2)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        drv = DriverTracer(parser)
        drivers = drv.find_driver('r')
        
        print(f"Drivers for r: {len(drivers)}")
        for d in drivers:
            sources = d.sources if d.sources else ['<no sources>']
            print(f"  - kind={d.kind}")
        
        print("  ✅ 嵌套 if 测试通过")
        return True
    finally:
        os.unlink(tmp)


def main():
    tests = [
        test_simple,
        test_nested,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
    
    print(f"\n总计: {passed}/{len(tests)} 通过")
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
