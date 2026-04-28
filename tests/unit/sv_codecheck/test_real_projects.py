#!/usr/bin/env python3
"""
真实项目解析测试
"""
import sys
import os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser


PROJECTS = [
    '/Users/fundou/my_dv_proj/sv-tests/tests/chapter-12',
]


def test_sv_tests_parse():
    """测试 sv-tests 项目"""
    passed = 0
    total = 0
    
    for proj in PROJECTS:
        if not os.path.exists(proj):
            continue
            
        for root, dirs, files in os.walk(proj):
            for f in files:
                if f.endswith('.sv'):
                    total += 1
                    try:
                        parser = SVParser()
                        parser.parse_file(os.path.join(root, f))
                        passed += 1
                    except:
                        pass
    
    print(f"  sv-tests: {passed}/{total}")
    return passed > 0


def test_parse_real_design():
    """测试真实设计"""
    code = '''
module cpu (
    input clk,
    input rst_n,
    input [31:0] inst,
    output [31:0] rd
);
    reg [31:0] pc;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pc <= 0;
        else
            pc <= pc + 4;
    end
    assign rd = pc;
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    print("  real design: OK")
    return True


def test_parse_interface():
    """测试 interface"""
    code = '''
interface axi4;
    logic [31:0] awaddr;
    logic awvalid;
    logic awready;
endinterface
'''
    parser = SVParser()
    parser.parse_text(code)
    print("  interface: OK")
    return True


def test_parse_package():
    """测试 package"""
    code = '''
package defines;
    parameter WIDTH = 8;
    typedef enum logic [1:0] {IDLE, RUN, DONE} state_t;
endpackage
'''
    parser = SVParser()
    parser.parse_text(code)
    print("  package: OK")
    return True


def main():
    print("============================================================")
    print("Real Projects Tests")
    print("============================================================")
    
    tests = [
        test_sv_tests_parse,
        test_parse_real_design,
        test_parse_interface,
        test_parse_package,
    ]
    
    passed = 0
    for t in tests:
        try:
            if t():
                passed += 1
        except Exception as e:
            print(f"  {t.__name__}: ERROR - {e}")
    
    print(f"\n{passed}/{len(tests)} passed")
    print("============================================================")


if __name__ == '__main__':
    main()
