"""Query 模块边界测试用例"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse import SVParser
from query.overflow_risk_detector import OverflowRiskDetector
from query.condition_relation_extractor import ConditionRelationExtractor
from query.signal import SignalQuery

def test_query_edge_cases():
    """边界测试: Query 模块"""
    results = {}
    
    # 1. OverflowRiskDetector: 饱和计数器
    code1 = '''module overflow_edge1;
        logic [7:0] counter;
        logic clk, rst;
        always_ff @(posedge clk or posedge rst) begin
            if (rst)
                counter <= 0;
            else
                counter <= counter + 1;
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code1)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = OverflowRiskDetector(parser)
        result = detector.detect()
        results['overflow_counter'] = len(result.risks)
    except Exception as e:
        results['overflow_counter'] = 0
    finally:
        os.unlink(tmp)
    
    # 2. OverflowRiskDetector: 有边界的加法
    code2 = '''module overflow_edge2;
        logic [7:0] a, b, sum;
        logic overflow;
        assign {overflow, sum} = a + b;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code2)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = OverflowRiskDetector(parser)
        result = detector.detect()
        results['overflow_checked'] = len(result.risks)
    except Exception as e:
        results['overflow_checked'] = 0
    finally:
        os.unlink(tmp)
    
    # 3. ConditionRelationExtractor: 互斥条件
    code3 = '''module cond_edge1;
        logic [1:0] mode;
        logic [7:0] a, b, r;
        always_comb begin
            case (mode)
                2'b00: r = a;
                2'b01: r = b;
                2'b10: r = a + b;
            endcase
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code3)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        extractor = ConditionRelationExtractor(parser)
        result = extractor.extract('r')
        results['cond_mutual_exclusive'] = len(result.conditions) if result else 0
    except Exception as e:
        results['cond_mutual_exclusive'] = 0
    finally:
        os.unlink(tmp)
    
    # 4. ConditionRelationExtractor: 嵌套条件
    code4 = '''module cond_edge2;
        logic a, b, c;
        logic [7:0] r;
        always_comb begin
            if (a) begin
                if (b)
                    r = 1;
                else
                    r = 2;
            end else begin
                if (c)
                    r = 3;
                else
                    r = 4;
            end
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code4)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        extractor = ConditionRelationExtractor(parser)
        result = extractor.extract('r')
        results['cond_nested'] = len(result.conditions) if result else 0
    except Exception as e:
        results['cond_nested'] = 0
    finally:
        os.unlink(tmp)
    
    # 5. SignalQuery: 查找信号
    code5 = '''module signal_edge1;
        logic clk, rst, vld;
        logic [7:0] data;
        logic [7:0] result;
        
        always_ff @(posedge clk) begin
            if (rst)
                result <= 0;
            else if (vld)
                result <= data;
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code5)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        query = SignalQuery(parser)
        signal = query.find_signal('result')
        results['signal_query'] = 1 if signal else 0
    except Exception as e:
        results['signal_query'] = 0
    finally:
        os.unlink(tmp)
    
    # 6. OverflowRiskDetector: 乘法溢出
    code6 = '''module overflow_edge3;
        logic [7:0] a, b;
        logic [15:0] result;
        assign result = a * b;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code6)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = OverflowRiskDetector(parser)
        result = detector.detect()
        results['overflow_mult'] = len(result.risks)
    except Exception as e:
        results['overflow_mult'] = 0
    finally:
        os.unlink(tmp)
    
    # 7. ConditionRelationExtractor: 优先级条件
    code7 = '''module cond_edge3;
        logic high_pri, low_pri;
        logic [7:0] a, b, r;
        always_comb begin
            r = 0;
            if (high_pri)
                r = a;
            else if (low_pri)
                r = b;
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code7)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        extractor = ConditionRelationExtractor(parser)
        result = extractor.extract('r')
        results['cond_priority'] = len(result.conditions) if result else 0
    except Exception as e:
        results['cond_priority'] = 0
    finally:
        os.unlink(tmp)
    
    # 8. OverflowRiskDetector: 移位溢出
    code8 = '''module overflow_edge4;
        logic [7:0] data;
        logic [2:0] shift;
        logic [7:0] result;
        assign result = data << shift;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code8)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = OverflowRiskDetector(parser)
        result = detector.detect()
        results['overflow_shift'] = len(result.risks)
    except Exception as e:
        results['overflow_shift'] = 0
    finally:
        os.unlink(tmp)
    
    return results


if __name__ == '__main__':
    print("=== Query Module Edge Cases ===")
    results = test_query_edge_cases()
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {name}: {count}")
    
    passed = sum(1 for c in results.values() if c > 0)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({100*passed//total}%)")
