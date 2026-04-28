#!/usr/bin/env python3
"""
pyslang 限制测试
"""
import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser


def test_parse():
    """基本解析测试"""
    code = 'module t; logic a; endmodule'
    parser = SVParser()
    parser.parse_text(code)
    return True


def test_module():
    """模块解析测试"""
    code = '''
module test (input clk, output [7:0] data);
    always @(posedge clk) begin
        data <= data + 1;
    end
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    return True


def test_class():
    """Class 解析测试"""
    code = '''
class packet;
    rand logic [7:0] data;
    function void send();
    endfunction
endclass
'''
    parser = SVParser()
    parser.parse_text(code)
    return True


def main():
    tests = [test_parse, test_module, test_class]
    passed = 0
    
    for t in tests:
        try:
            if t():
                print(f"  ✅ {t.__name__}")
                passed += 1
            else:
                print(f"  ❌ {t.__name__}")
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
    
    print(f"\n{passed}/{len(tests)} passed")
    return passed == len(tests)


if __name__ == '__main__':
    main()
