"""DependencyAnalyzer 边界测试用例"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse import SVParser
from trace.dependency import DependencyAnalyzer

def test_dependency_edge_cases():
    """边界测试: DependencyAnalyzer"""
    results = {}
    
    # 1. 简单依赖链
    code1 = '''module dep_simple;
        logic [7:0] a, b, c;
        assign b = a + 1;
        assign c = b + 1;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code1)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        da = DependencyAnalyzer(parser)
        deps = da.analyze('a')
        # 检查是否有依赖关系
        results['simple_chain'] = 1 if deps else 0
    except Exception as e:
        results['simple_chain'] = 0
    finally:
        os.unlink(tmp)
    
    # 2. 多层依赖
    code2 = '''module dep_multi;
        logic [7:0] a, b, c, d;
        assign b = a + 1;
        assign c = b * 2;
        assign d = c - 1;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code2)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        da = DependencyAnalyzer(parser)
        deps = da.analyze('a')
        results['multi_layer'] = 1 if deps else 0
    except Exception as e:
        results['multi_layer'] = 0
    finally:
        os.unlink(tmp)
    
    # 3. 条件依赖
    code3 = '''module dep_cond;
        logic [7:0] a, b, c, sel;
        always_comb begin
            if (sel)
                c = a;
            else
                c = b;
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code3)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        da = DependencyAnalyzer(parser)
        deps = da.analyze('a')
        results['conditional'] = 1 if deps else 0
    except Exception as e:
        results['conditional'] = 0
    finally:
        os.unlink(tmp)
    
    # 4. 数组依赖
    code4 = '''module dep_array;
        logic [7:0] mem [0:15];
        logic [3:0] addr;
        logic [7:0] data;
        always_comb begin
            data = mem[addr];
            mem[addr] = data + 1;
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code4)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        da = DependencyAnalyzer(parser)
        deps = da.analyze('data')
        results['array_dep'] = 1 if deps else 0
    except Exception as e:
        results['array_dep'] = 0
    finally:
        os.unlink(tmp)
    
    # 5. 三元表达式依赖
    code5 = '''module dep_ternary;
        logic [7:0] a, b, sel, r;
        assign r = sel ? a : b;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code5)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        da = DependencyAnalyzer(parser)
        deps = da.analyze('a')
        results['ternary'] = 1 if deps else 0
    except Exception as e:
        results['ternary'] = 0
    finally:
        os.unlink(tmp)
    
    # 6. for 循环依赖
    code6 = '''module dep_for;
        logic [7:0] cnt;
        logic clk;
        logic [3:0] i;
        always_ff @(posedge clk) begin
            for (i = 0; i < 10; i = i + 1) begin
                cnt <= cnt + 1;
            end
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code6)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        da = DependencyAnalyzer(parser)
        deps = da.analyze('cnt')
        results['for_loop'] = 1 if deps else 0
    except Exception as e:
        results['for_loop'] = 0
    finally:
        os.unlink(tmp)
    
    # 7. 函数依赖
    code7 = '''module dep_func;
        logic [7:0] a, b, r;
        function logic [7:0] add;
            input [7:0] x, y;
            add = x + y;
        endfunction
        assign r = add(a, b);
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code7)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        da = DependencyAnalyzer(parser)
        deps = da.analyze('a')
        results['function'] = 1 if deps else 0
    except Exception as e:
        results['function'] = 0
    finally:
        os.unlink(tmp)
    
    # 8. 跨模块依赖
    code8 = '''module dep_sub;
        input [7:0] x;
        output [7:0] y;
        assign y = x + 1;
    endmodule
    
    module dep_top;
        logic [7:0] a, b;
        dep_sub u1 (.x(a), .y(b));
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code8)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        da = DependencyAnalyzer(parser)
        deps = da.analyze('a')
        results['cross_module'] = 1 if deps else 0
    except Exception as e:
        results['cross_module'] = 0
    finally:
        os.unlink(tmp)
    
    return results


if __name__ == '__main__':
    print("=== DependencyAnalyzer Edge Cases ===")
    results = test_dependency_edge_cases()
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {name}: {count}")
    
    passed = sum(1 for c in results.values() if c > 0)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({100*passed//total}%)")
