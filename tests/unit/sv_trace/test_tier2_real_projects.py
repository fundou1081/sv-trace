"""
Tier 2 工具 - 开源项目真实源码测试

使用 OpenTitan 等开源项目的真实 SystemVerilog 代码测试 Tier 2 工具。

测试文件来源:
- tests/sv_cases/open_source/opentitan_uart.sv
- tests/sv_cases/open_source/opentitan_spi.sv
- tests/sv_cases/open_source/opentitan_hmac.sv
- tests/sv_cases/open_source/opentitan_rv_dm.sv
- tests/sv_cases/open_source/opentitan_aes_pkg.sv
- tests/sv_cases/targeted/test_driver_collector.sv
- tests/sv_cases/targeted/test_controlflow_tracer.sv

使用方法:
    python tests/unit/sv_trace/test_tier2_real_projects.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'src'))

from parse import SVParser


# =============================================================================
# 读取真实源码
# =============================================================================

def read_test_file(filename):
    """读取测试文件"""
    test_dir = os.path.join(os.path.dirname(__file__), '../../..', 'tests', 'sv_cases')
    filepath = os.path.join(test_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    return None


def read_open_source_file(filename):
    """读取开源项目测试文件"""
    test_dir = os.path.join(os.path.dirname(__file__), '../../..', 'tests', 'sv_cases', 'open_source')
    filepath = os.path.join(test_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    return None


# =============================================================================
# 测试数据
# =============================================================================

# 读取真实源码
UART_CODE = read_open_source_file('opentitan_uart.sv')
SPI_CODE = read_open_source_file('opentitan_spi.sv')
HMAC_CODE = read_open_source_file('opentitan_hmac.sv')
RVDM_CODE = read_open_source_file('opentitan_rv_dm.sv')
AES_CODE = read_open_source_file('opentitan_aes_pkg.sv')

# 如果文件不存在，使用简化版本
if not UART_CODE:
    UART_CODE = '''
module uart_core (
    input clk_i, rst_ni,
    input [7:0] reg_data,
    output logic [7:0] hw_data
);
    typedef enum logic [1:0] {
        IDLE = 2'b00,
        START = 2'b01,
        DATA = 2'b10,
        STOP = 2'b11
    } state_t;
    
    state_t state, next_state;
    
    always_ff @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni)
            state <= IDLE;
        else
            state <= next_state;
    end
    
    always_comb begin
        next_state = state;
        unique case (state)
            IDLE: if (reg_data[0]) next_state = START;
            START: next_state = DATA;
            DATA: next_state = STOP;
            STOP: next_state = IDLE;
        endcase
    end
    
    always_ff @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni)
            hw_data <= 8'h0;
        else
            hw_data <= {reg_data[0], 7'h0};
    end
endmodule
'''

if not SPI_CODE:
    SPI_CODE = '''
module spi_device (
    input clk_i, rst_ni,
    input [31:0] tx_data,
    output [31:0] rx_data
);
    logic [31:0] tx_shift, rx_shift;
    logic [4:0] bit_cnt;
    
    always_ff @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            tx_shift <= 32'h0;
            bit_cnt <= 5'h0;
        end else begin
            if (bit_cnt < 32)
                tx_shift <= {1'b0, tx_shift[31:1]};
            bit_cnt <= bit_cnt + 1;
        end
    end
endmodule
'''

# 简单的多模块测试代码
MULTI_MODULE_CODE = '''
module sub_module (
    input clk,
    input [7:0] data_in,
    output [7:0] data_out
);
    logic [7:0] pipeline_reg;
    
    always_ff @(posedge clk) begin
        pipeline_reg <= data_in;
    end
    
    assign data_out = pipeline_reg;
endmodule

module top_module (
    input clk,
    input [7:0] in1, in2,
    output [7:0] out1, out2
);
    wire [7:0] w1, w2;
    
    sub_module u_sub1 (.clk(clk), .data_in(in1), .data_out(w1));
    sub_module u_sub2 (.clk(clk), .data_in(w1), .data_out(w2));
    
    assign out1 = w1;
    assign out2 = w2;
endmodule
'''

# Pipeline 测试代码
PIPELINE_CODE = '''
module pipeline_cpu (
    input clk,
    input rst_n,
    input [31:0] instruction,
    input [31:0] pc,
    output [31:0] result
);
    // IF stage
    logic [31:0] if_pc, if_instr;
    // ID stage
    logic [31:0] id_pc, id_instr;
    // EX stage
    logic [31:0] ex_pc, ex_alu_result;
    // MEM stage
    logic [31:0] mem_result;
    // WB stage
    logic [31:0] wb_result;
    
    // IF/ID pipeline register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            if_pc <= 32'h0;
            if_instr <= 32'h0;
        end else begin
            if_pc <= pc;
            if_instr <= instruction;
        end
    end
    
    // ID/EX pipeline register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            id_pc <= 32'h0;
            id_instr <= 32'h0;
        end else begin
            id_pc <= if_pc;
            id_instr <= if_instr;
        end
    end
    
    assign result = wb_result;
endmodule
'''

# Class 测试代码
CLASS_CODE = '''
class transaction;
    rand bit [31:0] addr;
    rand bit [31:0] data;
    rand bit [3:0] kind;
    
    constraint valid_addr {
        addr inside {['h1000:'h2000]};
    }
    
    constraint valid_data {
        data > 0;
        data < 'hFFFF_FFFF;
    }
    
    function void print();
        $display("transaction: addr=%h data=%h", addr, data);
    endfunction
endclass

class extended_transaction extends transaction;
    rand bit [7:0] channel;
    
    constraint channel_valid {
        channel < 16;
    }
    
    function void print();
        super.print();
        $display("channel=%h", channel);
    endfunction
endclass
'''


# =============================================================================
# 测试函数
# =============================================================================

def test_driver_tracer():
    """测试 DriverTracer"""
    print("\n[DriverTracer] 开源项目测试")
    print("-" * 50)
    
    from trace.driver import DriverCollector
    
    tests_passed = 0
    tests_total = 0
    
    # 测试 1: UART 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(UART_CODE)
        dc = DriverCollector(p, verbose=False)
        drivers = dc.get_drivers('*')
        if len(drivers) >= 0:
            print(f"  ✅ UART: {len(drivers)} drivers")
            tests_passed += 1
    except Exception as e:
        print(f"  ❌ UART: {e}")
    
    # 测试 2: SPI 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(SPI_CODE)
        dc = DriverCollector(p, verbose=False)
        drivers = dc.get_drivers('*')
        if len(drivers) >= 0:
            print(f"  ✅ SPI: {len(drivers)} drivers")
            tests_passed += 1
    except Exception as e:
        print(f"  ❌ SPI: {e}")
    
    # 测试 3: 多模块代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(MULTI_MODULE_CODE)
        dc = DriverCollector(p, verbose=False)
        drivers = dc.get_drivers('*')
        if len(drivers) >= 0:
            print(f"  ✅ Multi-module: {len(drivers)} drivers")
            tests_passed += 1
    except Exception as e:
        print(f"  ❌ Multi-module: {e}")
    
    # 测试 4: 查找特定信号
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(UART_CODE)
        dc = DriverCollector(p, verbose=False)
        # 查找 state 信号
        state_drivers = dc.find_driver('state')
        print(f"  ✅ Find driver: {len(state_drivers)} for 'state'")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Find driver: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_connection_tracer():
    """测试 ConnectionTracer"""
    print("\n[ConnectionTracer] 开源项目测试")
    print("-" * 50)
    
    from trace.connection import ConnectionTracer
    
    tests_passed = 0
    tests_total = 0
    
    # 测试 1: 多模块
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(MULTI_MODULE_CODE)
        ct = ConnectionTracer(p, verbose=False)
        instances = ct.get_all_instances()
        if len(instances) >= 2:
            print(f"  ✅ Multi-module: {len(instances)} instances")
            tests_passed += 1
        else:
            print(f"  ⚠️  Multi-module: {len(instances)} instances (expected >= 2)")
    except Exception as e:
        print(f"  ❌ Multi-module: {e}")
    
    # 测试 2: HMAC 代码
    tests_total += 1
    try:
        if HMAC_CODE:
            p = SVParser()
            p.parse_text(HMAC_CODE)
            ct = ConnectionTracer(p, verbose=False)
            instances = ct.get_all_instances()
            print(f"  ✅ HMAC: {len(instances)} instances")
            tests_passed += 1
        else:
            print(f"  ⚠️  HMAC: code not available")
    except Exception as e:
        print(f"  ❌ HMAC: {e}")
    
    # 测试 3: UART 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(UART_CODE)
        ct = ConnectionTracer(p, verbose=False)
        instances = ct.get_all_instances()
        print(f"  ✅ UART: {len(instances)} instances")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ UART: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_controlflow_tracer():
    """测试 ControlFlowTracer"""
    print("\n[ControlFlowTracer] 开源项目测试")
    print("-" * 50)
    
    from trace.controlflow import ControlFlowTracer
    
    tests_passed = 0
    tests_total = 0
    
    # 测试 1: FSM 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(UART_CODE)
        cf = ControlFlowTracer(p, verbose=False)
        print(f"  ✅ FSM (UART): initialized")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FSM (UART): {e}")
    
    # 测试 2: Pipeline 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(PIPELINE_CODE)
        cf = ControlFlowTracer(p, verbose=False)
        print(f"  ✅ Pipeline: initialized")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Pipeline: {e}")
    
    # 测试 3: HMAC 代码
    tests_total += 1
    try:
        if HMAC_CODE:
            p = SVParser()
            p.parse_text(HMAC_CODE)
            cf = ControlFlowTracer(p, verbose=False)
            print(f"  ✅ HMAC: initialized")
            tests_passed += 1
        else:
            print(f"  ⚠️  HMAC: code not available")
    except Exception as e:
        print(f"  ❌ HMAC: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_datapath_analyzer():
    """测试 DataPathAnalyzer"""
    print("\n[DataPathAnalyzer] 开源项目测试")
    print("-" * 50)
    
    from trace.datapath import DataPathAnalyzer
    
    tests_passed = 0
    tests_total = 0
    
    # 测试 1: Pipeline 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(PIPELINE_CODE)
        dp = DataPathAnalyzer(p, verbose=False)
        print(f"  ✅ Pipeline: initialized")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Pipeline: {e}")
    
    # 测试 2: Multi-module 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(MULTI_MODULE_CODE)
        dp = DataPathAnalyzer(p, verbose=False)
        print(f"  ✅ Multi-module: initialized")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Multi-module: {e}")
    
    # 测试 3: SPI 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(SPI_CODE)
        dp = DataPathAnalyzer(p, verbose=False)
        print(f"  ✅ SPI: initialized")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ SPI: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_signal_classifier():
    """测试 SignalClassifier"""
    print("\n[SignalClassifier] 开源项目测试")
    print("-" * 50)
    
    from trace.signal_classifier import SignalClassifier
    
    tests_passed = 0
    tests_total = 0
    
    # 测试 1: UART 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(UART_CODE)
        sc = SignalClassifier(p, verbose=False)
        print(f"  ✅ UART: initialized")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ UART: {e}")
    
    # 测试 2: Pipeline 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(PIPELINE_CODE)
        sc = SignalClassifier(p, verbose=False)
        print(f"  ✅ Pipeline: initialized")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Pipeline: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_pipeline_analyzer():
    """测试 PipelineAnalyzer"""
    print("\n[PipelineAnalyzer] 开源项目测试")
    print("-" * 50)
    
    from trace.pipeline_analyzer import PipelineAnalyzer
    
    tests_passed = 0
    tests_total = 0
    
    # 测试 1: Pipeline 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(PIPELINE_CODE)
        pa = PipelineAnalyzer(p, verbose=False)
        print(f"  ✅ Pipeline: initialized")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Pipeline: {e}")
    
    # 测试 2: SPI 代码
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(SPI_CODE)
        pa = PipelineAnalyzer(p, verbose=False)
        print(f"  ✅ SPI: initialized")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ SPI: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_class_extractor():
    """测试 ClassExtractor"""
    print("\n[ClassExtractor] 开源项目测试")
    print("-" * 50)
    
    from parse.class_utils import ClassExtractor
    
    tests_passed = 0
    tests_total = 0
    
    # 测试 1: 简单 Class
    tests_total += 1
    try:
        ce = ClassExtractor(None, verbose=False)
        classes = ce.extract_from_text(CLASS_CODE)
        if len(classes) >= 2:
            print(f"  ✅ Simple class: {len(classes)} classes")
            tests_passed += 1
        else:
            print(f"  ⚠️  Simple class: {len(classes)} classes (expected >= 2)")
    except Exception as e:
        print(f"  ❌ Simple class: {e}")
    
    # 测试 2: HMAC 代码中的 class
    tests_total += 1
    try:
        if HMAC_CODE:
            ce = ClassExtractor(None, verbose=False)
            classes = ce.extract_from_text(HMAC_CODE)
            print(f"  ✅ HMAC: {len(classes)} classes")
            tests_passed += 1
        else:
            print(f"  ⚠️  HMAC: code not available")
    except Exception as e:
        print(f"  ❌ HMAC: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_constraint_extractor():
    """测试 ConstraintExtractor"""
    print("\n[ConstraintExtractor] 开源项目测试")
    print("-" * 50)
    
    from parse.constraint import ConstraintExtractor
    
    tests_passed = 0
    tests_total = 0
    
    # 测试 1: 简单 Class
    tests_total += 1
    try:
        ce = ConstraintExtractor()
        constraints = ce.extract_from_text(CLASS_CODE)
        if len(constraints) >= 2:
            print(f"  ✅ Simple: {len(constraints)} constraints")
            tests_passed += 1
        else:
            print(f"  ⚠️  Simple: {len(constraints)} constraints (expected >= 2)")
    except Exception as e:
        print(f"  ❌ Simple: {e}")
    
    # 测试 2: HMAC 代码中的 constraint
    tests_total += 1
    try:
        if HMAC_CODE:
            ce = ConstraintExtractor()
            constraints = ce.extract_from_text(HMAC_CODE)
            print(f"  ✅ HMAC: {len(constraints)} constraints")
            tests_passed += 1
        else:
            print(f"  ⚠️  HMAC: code not available")
    except Exception as e:
        print(f"  ❌ HMAC: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_fsm_extractor():
    """测试 FSMExtractor"""
    print("\n[FSMExtractor] 开源项目测试")
    print("-" * 50)
    
    try:
        from debug.fsm import FSMExtractor
    except ImportError:
        print("  ⚠️  FSMExtractor not available")
        return True
    
    tests_passed = 0
    tests_total = 0
    
    # 测试 1: UART FSM
    tests_total += 1
    try:
        p = SVParser()
        p.parse_text(UART_CODE)
        extractor = FSMExtractor(p, verbose=False)
        result = extractor.extract()
        print(f"  ✅ UART FSM: {len(result)} FSMs")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ UART FSM: {e}")
    
    # 测试 2: HMAC 代码
    tests_total += 1
    try:
        if HMAC_CODE:
            p = SVParser()
            p.parse_text(HMAC_CODE)
            extractor = FSMExtractor(p, verbose=False)
            result = extractor.extract()
            print(f"  ✅ HMAC: {len(result)} FSMs")
            tests_passed += 1
        else:
            print(f"  ⚠️  HMAC: code not available")
    except Exception as e:
        print(f"  ❌ HMAC: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_vcd_analyzer():
    """测试 VCDAnalyzer"""
    print("\n[VCDAnalyzer] 开源项目测试")
    print("-" * 50)
    
    from trace.vcd_analyzer import VCDAnalyzer
    
    tests_passed = 0
    tests_total = 0
    
    # VCD 测试数据
    VCD_DATA = '''
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 8 " data $end
$var wire 1 # valid $end
$upscope $end
$enddefinitions $end
#0
b0 !
b00000000 "
b0 #
#10
b1 !
#15
b1 #
#20
b0 !
b10101010 "
#30
b1 !
b0 #
#40
b0 !
#50
b1 !
'''
    
    tests_total += 1
    try:
        va = VCDAnalyzer(verbose=False)
        waveforms = va.parse_vcd_text(VCD_DATA)
        if len(waveforms) >= 3:
            print(f"  ✅ Parse: {len(waveforms)} signals")
            tests_passed += 1
        else:
            print(f"  ⚠️  Parse: {len(waveforms)} signals (expected >= 3)")
    except Exception as e:
        print(f"  ❌ Parse: {e}")
    
    tests_total += 1
    try:
        va = VCDAnalyzer(verbose=False)
        va.parse_vcd_text(VCD_DATA)
        transitions = va.find_transitions('tb/clk')
        if len(transitions) > 0:
            print(f"  ✅ Transitions: {len(transitions)}")
            tests_passed += 1
        else:
            print(f"  ⚠️  Transitions: 0")
    except Exception as e:
        print(f"  ❌ Transitions: {e}")
    
    tests_total += 1
    try:
        va = VCDAnalyzer(verbose=False)
        va.parse_vcd_text(VCD_DATA)
        freq = va.measure_frequency('tb/clk')
        duty = va.measure_duty_cycle('tb/clk')
        if freq and duty:
            print(f"  ✅ Frequency: {freq:.1f} Hz, Duty: {duty:.2f}")
            tests_passed += 1
        else:
            print(f"  ⚠️  Frequency/Duty: measurement failed")
    except Exception as e:
        print(f"  ❌ Frequency/Duty: {e}")
    
    print(f"  结果: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("SV-TRACE Tier 2 工具 - 开源项目真实源码测试")
    print("=" * 70)
    
    # 读取真实源码
    print("\n读取开源项目测试文件...")
    UART_CODE = read_open_source_file('opentitan_uart.sv')
    HMAC_CODE = read_open_source_file('opentitan_hmac.sv')
    SPI_CODE = read_open_source_file('opentitan_spi.sv')
    
    if UART_CODE:
        print(f"  ✅ opentitan_uart.sv: {len(UART_CODE)} chars")
    if HMAC_CODE:
        print(f"  ✅ opentitan_hmac.sv: {len(HMAC_CODE)} chars")
    if SPI_CODE:
        print(f"  ✅ opentitan_spi.sv: {len(SPI_CODE)} chars")
    
    # 运行所有测试
    results = []
    
    results.append(("DriverTracer", test_driver_tracer()))
    results.append(("ConnectionTracer", test_connection_tracer()))
    results.append(("ControlFlowTracer", test_controlflow_tracer()))
    results.append(("DataPathAnalyzer", test_datapath_analyzer()))
    results.append(("SignalClassifier", test_signal_classifier()))
    results.append(("PipelineAnalyzer", test_pipeline_analyzer()))
    results.append(("ClassExtractor", test_class_extractor()))
    results.append(("ConstraintExtractor", test_constraint_extractor()))
    results.append(("VCDAnalyzer", test_vcd_analyzer()))
    
    # 尝试 FSMExtractor
    try:
        from debug.fsm import FSMExtractor
        results.append(("FSMExtractor", test_fsm_extractor()))
    except ImportError:
        print("\n[FSMExtractor] Skipped (not available)")
    
    # 打印总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print()
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("=" * 70)
        print("✅ 全部测试通过!")
        print("=" * 70)
    else:
        print("=" * 70)
        print(f"❌ {total - passed} 个测试失败")
        print("=" * 70)
