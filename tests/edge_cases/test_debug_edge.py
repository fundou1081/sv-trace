"""Debug Analyzers 边界测试用例"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse import SVParser
from debug.analyzers.multi_driver import MultiDriverDetector
from debug.analyzers.uninitialized import UninitializedDetector
from debug.analyzers.xvalue import XValueDetector
from debug.analyzers.dangling_port import DanglingPortDetector

def test_debug_edge_cases():
    """边界测试: Debug Analyzers"""
    results = {}
    
    # 1. MultiDriverDetector: wire 隐式声明的多驱动
    code1 = '''module md_edge1;
        input [7:0] a;
        // b 没有声明为 wire，直接 assign 隐式创建
        assign b = a;
        assign b = a + 1;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code1)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = MultiDriverDetector(parser)
        result = detector.detect_all()
        results['multi_driver_implicit'] = len(result)
    finally:
        os.unlink(tmp)
    
    # 2. MultiDriverDetector: generate 块中的多驱动
    code2 = '''module md_edge2;
        logic [7:0] a, b, r;
        genvar i;
        generate
            for (i = 0; i < 2; i = i + 1) begin : gen
                assign r = a + i;
            end
        endgenerate
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code2)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = MultiDriverDetector(parser)
        result = detector.detect_all()
        results['multi_driver_gen'] = len(result)
    finally:
        os.unlink(tmp)
    
    # 3. UninitializedDetector: 数组寄存器未初始化
    code3 = '''module uninit_edge1;
        logic [7:0] mem [0:15];
        logic [3:0] idx;
        logic clk;
        always_ff @(posedge clk) begin
            mem[idx] <= 8'hFF;
        end
        // mem[0] 读取时未初始化
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code3)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = UninitializedDetector(parser)
        result = detector.detect_all()
        results['uninit_array'] = len(result)
    finally:
        os.unlink(tmp)
    
    # 4. UninitializedDetector: 异步复位时未初始化
    code4 = '''module uninit_edge2;
        logic clk, rst;
        logic [7:0] r;
        always_ff @(posedge clk or posedge rst) begin
            if (rst)
                r <= 8'h00;
            // 异步复位后未覆盖的情况 - 如果没有 else 分支
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code4)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = UninitializedDetector(parser)
        result = detector.detect_all()
        results['uninit_async_rst'] = len(result)
    finally:
        os.unlink(tmp)
    
    # 5. XValueDetector: casez 通配符导致的 X
    code5 = '''module xval_edge1;
        logic [3:0] pattern;
        logic [7:0] result;
        always_comb begin
            casez (pattern)
                4'b1???: result = 8'h01;
                4'b01??: result = 8'h02;
                4'b001?: result = 8'h03;
                // 4'b0000 未覆盖 - 可能是 X
            endcase
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code5)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = XValueDetector(parser)
        result = detector.detect_all()
        results['xval_casez'] = len(result)
    finally:
        os.unlink(tmp)
    
    # 6. XValueDetector: full_case 未使用导致的 X
    code6 = '''module xval_edge2;
        logic [1:0] state, next_state;
        (* full_case *) case (state)
            2'b00: next_state = 2'b01;
            2'b01: next_state = 2'b10;
            // 2'b11 和 2'bxx 未覆盖
        endcase
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code6)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = XValueDetector(parser)
        result = detector.detect_all()
        results['xval_full_case'] = len(result)
    finally:
        os.unlink(tmp)
    
    # 7. DanglingPortDetector: 输出端口被连续赋值但未使用
    code7 = '''module dangling_edge1;
        input [7:0] a;
        output [7:0] b, c;  // c 未被连接
        assign b = a + 1;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code7)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = DanglingPortDetector(parser)
        result = detector.detect_all()
        results['dangling_output'] = len(result)
    finally:
        os.unlink(tmp)
    
    # 8. DanglingPortDetector: 模块实例化时未连接的输出
    code8 = '''module dangling_edge2;
        logic [7:0] a, b, c;
        submod u_sub (.in(a), .out(b));  // c 未连接
    endmodule

    module submod;
        input [7:0] in;
        output [7:0] out, extra;
        assign out = in + 1;
        assign extra = in - 1;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code8)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = DanglingPortDetector(parser)
        result = detector.detect_all()
        results['dangling_instance'] = len(result)
    finally:
        os.unlink(tmp)
    
    return results


if __name__ == '__main__':
    print("=== Debug Analyzers Edge Cases ===")
    results = test_debug_edge_cases()
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {name}: {count}")
    
    passed = sum(1 for c in results.values() if c > 0)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({100*passed//total}%)")
