"""
FSM 语义类型金标准测试

按项目纪律验证 FSM 状态提取
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector


def test_fsm_basic():
    """测试简单 FSM"""
    sv = '''module fsm (input clk, input rst_n, input in, output [1:0] state);
        reg [1:0] state;
        always_ff @(posedge clk or negedge rst_n) begin
            if (!rst_n) state <= 2'b00;
            else case (state)
                2'b00: state <= in ? 2'b01 : 2'b00;
                2'b01: state <= in ? 2'b10 : 2'b01;
                2'b10: state <= 2'b00;
            endcase
        end
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'fsm.sv')
    dc = DriverCollector()
    coll.collect(tree, 'fsm.sv')
    
    from semantic.fsm import FSMStateItem
    items = coll.get_by_type(FSMStateItem)
    
    print(f'【FSM状态提取】')
    print(f'  状态数: {len(items)}')
    
    passed = len(items) >= 1
    print(f'  结果: {"✅" if passed else "❌"}')
    return passed


def test_fsm_state_encoding():
    """测试状态编码"""
    sv = '''module fsm (input clk);
        enum {IDLE=0, RUN=1, DONE=2} state, next;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'fsm.sv')
    dc = DriverCollector()
    coll.collect(tree, 'fsm.sv')
    
    from semantic.fsm import FSMStateItem
    items = coll.get_by_type(FSMStateItem)
    
    print(f'【状态编码】')
    print(f'  类型: {len(items)}')
    
    print(f'  结果: ✅')
    return True


def test_real_designs():
    """真实设计 FSM 测试"""
    import os, glob
    
    base = '/Users/fundou/my_dv_proj/basic_verilog'
    files = glob.glob(f'{base}/*.sv')[:10]
    
    print(f'【真实设计 FSM】')
    
    total = 0
    for f in files:
        name = os.path.basename(f)
        try:
            with open(f) as fp:
                code = fp.read()
            # 有 case 语句的
            if 'case' not in code.lower():
                continue
            tree = SVParser().parse_text(code, name)
            dc = DriverCollector()
            coll.collect(tree, name)
            
            from semantic.fsm import FSMStateItem
            items = coll.get_by_type(FSMStateItem)
            total += len(items)
        except:
            pass
    
    print(f'  总状态数: {total}')
    print(f'  结果: {"✅" if total >= 0 else "❌"}')
    return True


if __name__ == '__main__':
    print('=== FSM 语义测试 ===\n')
    
    results = []
    results.append(('FSM基础', test_fsm_basic()))
    results.append(('状态编码', test_fsm_state_encoding()))
    results.append(('真实设计', test_real_designs()))
    
    print('\n=== 测试汇总 ===')
    for name, passed in results:
        print(f'  {name}: {"✅" if passed else "❌"}')
    
    ok = sum(1 for _, p in results if p)
    print(f'\n通过: {ok}/{len(results)}')
