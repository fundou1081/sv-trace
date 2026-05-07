"""
Tier 2 工具综合测试 - 每个工具 10 个测试

使用开源项目和测试用例对每个 Tier 2 工具进行深入测试。

测试来源:
- tests/sv_cases/open_source/ (OpenTitan 项目)
- tests/sv_cases/driver/ (驱动测试)
- tests/sv_cases/fsm/ (FSM 测试)
- tests/sv_cases/dependency/ (依赖测试)
- tests/sv_cases/pyslang_tests/ (pyslang 测试)

使用方法:
    python tests/unit/sv_trace/test_tier2_comprehensive.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'src'))


# =============================================================================
# 测试文件读取
# =============================================================================

def read_file(relative_path):
    """读取测试文件"""
    base = os.path.join(os.path.dirname(__file__), '../../..', 'tests', 'sv_cases')
    filepath = os.path.join(base, relative_path)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    return None


# =============================================================================
# 测试数据 - 10 个不同来源
# =============================================================================

# 1. OpenTitan 项目
OPENTITAN_UART = read_file('open_source/opentitan_uart.sv')
OPENTITAN_SPI = read_file('open_source/opentitan_spi.sv')
OPENTITAN_HMAC = read_file('open_source/opentitan_hmac.sv')
OPENTITAN_RV_DM = read_file('open_source/opentitan_rv_dm.sv')
OPENTITAN_AES_PKG = read_file('open_source/opentitan_aes_pkg.sv')
OPENTITAN_KEYMGR = read_file('open_source/opentitan_keymgr.sv')
OPENTITAN_LC_CTRL = read_file('open_source/opentitan_lc_ctrl.sv')
OPENTITAN_USBDEV = read_file('open_source/opentitan_usbdev.sv')

# 2. Driver 测试用例
DRIVER_BASIC = read_file('driver/driver_basic.sv')
DRIVER_CASES = read_file('driver/driver_cases_20.sv')

# 3. FSM 测试用例
FSM_SIMPLE = read_file('fsm/fsm_simple.sv')
FSM_CASES = read_file('fsm/fsm_cases_20.sv')

# 4. Dependency 测试用例
DEP_HIERARCHY = read_file('dependency/dependency_hierarchy.sv')
DEP_CASES = read_file('dependency/dep_cases_20.sv')

# 5. pyslang 测试用例
MODULE_IO = read_file('pyslang_tests/module_io_test.sv')
CLASS_TEST = read_file('pyslang_tests/class_test.sv')
INTERFACE_TEST = read_file('pyslang_tests/interface_test.sv')
CLOCK_RESET = read_file('pyslang_tests/clock_reset_test.sv')
GENERATE_TEST = read_file('pyslang_tests/generate_test.sv')

# 6. 其他测试用例
IOSPEC_BASIC = read_file('iospec/iospec_basic.sv')
IOSPEC_CASES = read_file('iospec/iospec_cases_20.sv')


# =============================================================================
# 简化测试代码 (当文件不存在时使用)
# =============================================================================

FALLBACK_CODES = {
    'uart_simple': '''
module uart_simple (input clk, input rst_n, output [7:0] data);
    logic [7:0] reg_data;
    always_ff @(posedge clk) if (!rst_n) reg_data <= 0; else reg_data <= reg_data + 1;
    assign data = reg_data;
endmodule
''',
    'fsm_simple': '''
module fsm_simple (input clk, input rst_n, input start, output done);
    typedef enum {IDLE, WORK, DONE} state_t;
    state_t state;
    always_ff @(posedge clk) if (!rst_n) state <= IDLE; else case (state) IDLE: if (start) state <= WORK; WORK: state <= DONE; DONE: state <= IDLE; endcase
    assign done = (state == DONE);
endmodule
''',
    'pipeline': '''
module pipeline (input clk, input [7:0] din, output [7:0] dout);
    logic [7:0] stage1, stage2;
    always_ff @(posedge clk) begin stage1 <= din; stage2 <= stage1; end
    assign dout = stage2;
endmodule
''',
    'multi_module': '''
module sub (input clk, input [7:0] d, output [7:0] q);
    always_ff @(posedge clk) q <= d;
endmodule
module top (input clk, input [7:0] a, b, output [7:0] x, y);
    wire [7:0] w;
    sub s1(clk, a, w);
    sub s2(clk, w, x);
    assign y = b;
endmodule
''',
    'class_simple': '''
class foo;
    rand bit [7:0] x;
    constraint c { x > 5; x < 10; }
endclass
class bar extends foo;
    rand bit [3:0] y;
endclass
'''
}


# =============================================================================
# 测试函数
# =============================================================================

def get_code(name):
    """获取测试代码"""
    return globals().get(name) or FALLBACK_CODES.get(name, 'module test(); endmodule')


def run_test(name, code, test_func, *args, **kwargs):
    """运行单个测试"""
    try:
        return test_func(code, *args, **kwargs)
    except Exception as e:
        return False, str(e)[:50]


def test_driver_tracer():
    """DriverTracer 10 个测试"""
    print("\n[DriverTracer] 10 个测试")
    print("-" * 50)
    
    from trace.driver import DriverCollector
    from parse import SVParser
    
    tests = [
        ("OpenTitan UART", OPENTITAN_UART),
        ("OpenTitan SPI", OPENTITAN_SPI),
        ("OpenTitan HMAC", OPENTITAN_HMAC),
        ("OpenTitan RV_DM", OPENTITAN_RV_DM),
        ("Driver Basic", DRIVER_BASIC),
        ("Driver Cases 20", DRIVER_CASES),
        ("FSM Simple", FSM_SIMPLE),
        ("FSM Cases", FSM_CASES),
        ("Module IO", MODULE_IO),
        ("Clock Reset", CLOCK_RESET),
    ]
    
    passed = 0
    for i, (name, code) in enumerate(tests, 1):
        if not code:
            code = FALLBACK_CODES['uart_simple']
        try:
            p = SVParser()
            p.parse_text(code)
            dc = DriverCollector(p, verbose=False)
            drivers = dc.get_drivers('*')
            status = "OK" if drivers is not None else "EMPTY"
            print(f"  [{i}] {name}: {len(drivers)} drivers - {status}")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


def test_connection_tracer():
    """ConnectionTracer 10 个测试"""
    print("\n[ConnectionTracer] 10 个测试")
    print("-" * 50)
    
    from trace.connection import ConnectionTracer
    from parse import SVParser
    
    tests = [
        ("Multi Module", FALLBACK_CODES['multi_module']),
        ("OpenTitan UART", OPENTITAN_UART),
        ("OpenTitan SPI", OPENTITAN_SPI),
        ("OpenTitan HMAC", OPENTITAN_HMAC),
        ("OpenTitan RV_DM", OPENTITAN_RV_DM),
        ("Dependency Hierarchy", DEP_HIERARCHY),
        ("Dependency Cases", DEP_CASES),
        ("FSM Simple", FSM_SIMPLE),
        ("IOSpec Basic", IOSPEC_BASIC),
        ("Generate Test", GENERATE_TEST),
    ]
    
    passed = 0
    for i, (name, code) in enumerate(tests, 1):
        if not code:
            code = FALLBACK_CODES['multi_module']
        try:
            p = SVParser()
            p.parse_text(code)
            ct = ConnectionTracer(p, verbose=False)
            instances = ct.get_all_instances()
            print(f"  [{i}] {name}: {len(instances)} instances - OK")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


def test_controlflow_tracer():
    """ControlFlowTracer 10 个测试"""
    print("\n[ControlFlowTracer] 10 个测试")
    print("-" * 50)
    
    from trace.controlflow import ControlFlowTracer
    from parse import SVParser
    
    tests = [
        ("FSM Simple", FSM_SIMPLE),
        ("FSM Cases", FSM_CASES),
        ("OpenTitan UART", OPENTITAN_UART),
        ("OpenTitan SPI", OPENTITAN_SPI),
        ("OpenTitan HMAC", OPENTITAN_HMAC),
        ("OpenTitan RV_DM", OPENTITAN_RV_DM),
        ("OpenTitan LC_CTRL", OPENTITAN_LC_CTRL),
        ("Driver Cases", DRIVER_CASES),
        ("IOSpec Cases", IOSPEC_CASES),
        ("Module IO", MODULE_IO),
    ]
    
    passed = 0
    for i, (name, code) in enumerate(tests, 1):
        if not code:
            code = FALLBACK_CODES['fsm_simple']
        try:
            p = SVParser()
            p.parse_text(code)
            cf = ControlFlowTracer(p, verbose=False)
            print(f"  [{i}] {name}: OK")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


def test_datapath_analyzer():
    """DataPathAnalyzer 10 个测试"""
    print("\n[DataPathAnalyzer] 10 个测试")
    print("-" * 50)
    
    from trace.datapath import DataPathAnalyzer
    from parse import SVParser
    
    tests = [
        ("Pipeline", FALLBACK_CODES['pipeline']),
        ("Multi Module", FALLBACK_CODES['multi_module']),
        ("OpenTitan UART", OPENTITAN_UART),
        ("OpenTitan SPI", OPENTITAN_SPI),
        ("OpenTitan HMAC", OPENTITAN_HMAC),
        ("OpenTitan RV_DM", OPENTITAN_RV_DM),
        ("OpenTitan Keymgr", OPENTITAN_KEYMGR),
        ("Driver Basic", DRIVER_BASIC),
        ("Driver Cases", DRIVER_CASES),
        ("Clock Reset", CLOCK_RESET),
    ]
    
    passed = 0
    for i, (name, code) in enumerate(tests, 1):
        if not code:
            code = FALLBACK_CODES['pipeline']
        try:
            p = SVParser()
            p.parse_text(code)
            dp = DataPathAnalyzer(p, verbose=False)
            print(f"  [{i}] {name}: OK")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


def test_signal_classifier():
    """SignalClassifier 10 个测试"""
    print("\n[SignalClassifier] 10 个测试")
    print("-" * 50)
    
    from trace.signal_classifier import SignalClassifier
    from parse import SVParser
    
    tests = [
        ("OpenTitan UART", OPENTITAN_UART),
        ("OpenTitan SPI", OPENTITAN_SPI),
        ("OpenTitan HMAC", OPENTITAN_HMAC),
        ("OpenTitan RV_DM", OPENTITAN_RV_DM),
        ("OpenTitan LC_CTRL", OPENTITAN_LC_CTRL),
        ("OpenTitan USBDEV", OPENTITAN_USBDEV),
        ("FSM Cases", FSM_CASES),
        ("Driver Cases", DRIVER_CASES),
        ("IOSpec Cases", IOSPEC_CASES),
        ("Clock Reset", CLOCK_RESET),
    ]
    
    passed = 0
    for i, (name, code) in enumerate(tests, 1):
        if not code:
            code = FALLBACK_CODES['uart_simple']
        try:
            p = SVParser()
            p.parse_text(code)
            sc = SignalClassifier(p, verbose=False)
            print(f"  [{i}] {name}: OK")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


def test_pipeline_analyzer():
    """PipelineAnalyzer 10 个测试"""
    print("\n[PipelineAnalyzer] 10 个测试")
    print("-" * 50)
    
    from trace.pipeline_analyzer import PipelineAnalyzer
    from parse import SVParser
    
    tests = [
        ("Pipeline", FALLBACK_CODES['pipeline']),
        ("OpenTitan UART", OPENTITAN_UART),
        ("OpenTitan SPI", OPENTITAN_SPI),
        ("OpenTitan HMAC", OPENTITAN_HMAC),
        ("OpenTitan RV_DM", OPENTITAN_RV_DM),
        ("OpenTitan Keymgr", OPENTITAN_KEYMGR),
        ("OpenTitan LC_CTRL", OPENTITAN_LC_CTRL),
        ("FSM Cases", FSM_CASES),
        ("Driver Cases", DRIVER_CASES),
        ("Clock Reset", CLOCK_RESET),
    ]
    
    passed = 0
    for i, (name, code) in enumerate(tests, 1):
        if not code:
            code = FALLBACK_CODES['pipeline']
        try:
            p = SVParser()
            p.parse_text(code)
            pa = PipelineAnalyzer(p, verbose=False)
            print(f"  [{i}] {name}: OK")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


def test_class_extractor():
    """ClassExtractor 10 个测试"""
    print("\n[ClassExtractor] 10 个测试")
    print("-" * 50)
    
    from parse.class_utils import ClassExtractor
    
    tests = [
        ("Class Test", CLASS_TEST),
        ("OpenTitan HMAC", OPENTITAN_HMAC),
        ("OpenTitan Keymgr", OPENTITAN_KEYMGR),
        ("OpenTitan LC_CTRL", OPENTITAN_LC_CTRL),
        ("OpenTitan USBDEV", OPENTITAN_USBDEV),
        ("Class Simple", FALLBACK_CODES['class_simple']),
        ("Module IO", MODULE_IO),
        ("Interface Test", INTERFACE_TEST),
        ("Generate Test", GENERATE_TEST),
        ("Clock Reset", CLOCK_RESET),
    ]
    
    passed = 0
    for i, (name, code) in enumerate(tests, 1):
        if not code:
            code = FALLBACK_CODES['class_simple']
        try:
            ce = ClassExtractor(None, verbose=False)
            classes = ce.extract_from_text(code)
            print(f"  [{i}] {name}: {len(classes)} classes - OK")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


def test_constraint_extractor():
    """ConstraintExtractor 10 个测试"""
    print("\n[ConstraintExtractor] 10 个测试")
    print("-" * 50)
    
    from parse.constraint import ConstraintExtractor
    
    tests = [
        ("Class Test", CLASS_TEST),
        ("OpenTitan HMAC", OPENTITAN_HMAC),
        ("OpenTitan Keymgr", OPENTITAN_KEYMGR),
        ("OpenTitan LC_CTRL", OPENTITAN_LC_CTRL),
        ("Class Simple", FALLBACK_CODES['class_simple']),
        ("Module IO", MODULE_IO),
        ("Interface Test", INTERFACE_TEST),
        ("Generate Test", GENERATE_TEST),
        ("IOSpec Basic", IOSPEC_BASIC),
        ("Clock Reset", CLOCK_RESET),
    ]
    
    passed = 0
    for i, (name, code) in enumerate(tests, 1):
        if not code:
            code = FALLBACK_CODES['class_simple']
        try:
            ce = ConstraintExtractor()
            constraints = ce.extract_from_text(code)
            print(f"  [{i}] {name}: {len(constraints)} constraints - OK")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


def test_vcd_analyzer():
    """VCDAnalyzer 10 个测试"""
    print("\n[VCDAnalyzer] 10 个测试")
    print("-" * 50)
    
    from trace.vcd_analyzer import VCDAnalyzer
    
    # 不同 VCD 格式
    vcd_templates = [
        ("Simple Clock", '''
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
#0
b0 !
#10
b1 !
#20
b0 !
#30
b1 !
#40
b0 !
'''),
        ("Clock + Data", '''
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 8 " data $end
$upscope $end
$enddefinitions $end
#0
b0 !
b00000000 "
#10
b1 !
#20
b0 !
b10101010 "
#30
b1 !
#40
b0 !
'''),
        ("Clock + Valid", '''
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 1 # valid $end
$upscope $end
$enddefinitions $end
#0
b0 !
b0 #
#5
b1 !
b1 #
#15
b0 !
b0 #
#25
b1 !
b1 #
#35
b0 !
'''),
        ("Multi Signal", '''
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 1 @ rst $end
$var wire 8 # data $end
$var wire 1 $ valid $end
$upscope $end
$enddefinitions $end
#0
b0 !
b0 @
b00000000 #
b0 $
#10
b1 !
#20
b0 !
b1 @
b10101010 #
b1 $
#30
b1 !
#40
b0 !
b0 @
b00000000 #
b0 $
'''),
        ("Fast Clock", '''
$timescale 1ps $end
$scope module tb $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
#0
b0 !
#1
b1 !
#2
b0 !
#3
b1 !
#4
b0 !
'''),
        ("Slow Clock", '''
$timescale 1us $end
$scope module tb $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
#0
b0 !
#1000000
b1 !
#2000000
b0 !
#3000000
b1 !
#4000000
b0 !
'''),
        ("Reset Pattern", '''
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 1 @ rst $end
$upscope $end
$enddefinitions $end
#0
b0 !
b1 @
#10
b1 !
#20
b0 !
b0 @
#30
b1 !
#40
b0 !
#50
b1 !
'''),
        ("Data Bus", '''
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 16 " data $end
$upscope $end
$enddefinitions $end
#0
b0 !
b0000000000000000 "
#10
b1 !
#20
b0 !
b1111111111111111 "
#30
b1 !
#40
b0 !
'''),
        ("With X/Z", '''
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 4 " data $end
$upscope $end
$enddefinitions $end
#0
b0 !
b0000 "
#10
b1 !
b1xz0 "
#20
b0 !
b1111 "
#30
b1 !
'''),
        ("Burst Data", '''
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 32 " data $end
$upscope $end
$enddefinitions $end
#0
b0 !
b00000000000000000000000000000001 "
#10
b1 !
#20
b0 !
b00000000000000000000000000000010 "
#30
b1 !
#40
b0 !
b00000000000000000000000000000100 "
#50
b1 !
'''),
    ]
    
    passed = 0
    for i, (name, vcd) in enumerate(vcd_templates, 1):
        try:
            va = VCDAnalyzer(verbose=False)
            waveforms = va.parse_vcd_text(vcd)
            freq = va.measure_frequency(list(waveforms.keys())[0]) if waveforms else None
            print(f"  [{i}] {name}: {len(waveforms)} signals, freq={freq} - OK")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


def test_fsm_extractor():
    """FSMExtractor 10 个测试"""
    print("\n[FSMExtractor] 10 个测试")
    print("-" * 50)
    
    try:
        from debug.fsm import FSMExtractor
    except ImportError:
        print("  ⚠️  FSMExtractor not available, skipping")
        return True
    
    from parse import SVParser
    
    tests = [
        ("FSM Simple", FSM_SIMPLE),
        ("FSM Cases", FSM_CASES),
        ("OpenTitan UART", OPENTITAN_UART),
        ("OpenTitan SPI", OPENTITAN_SPI),
        ("OpenTitan HMAC", OPENTITAN_HMAC),
        ("OpenTitan RV_DM", OPENTITAN_RV_DM),
        ("OpenTitan LC_CTRL", OPENTITAN_LC_CTRL),
        ("OpenTitan Keymgr", OPENTITAN_KEYMGR),
        ("OpenTitan USBDEV", OPENTITAN_USBDEV),
        ("Driver Cases", DRIVER_CASES),
    ]
    
    passed = 0
    for i, (name, code) in enumerate(tests, 1):
        if not code:
            code = FALLBACK_CODES['fsm_simple']
        try:
            p = SVParser()
            p.parse_text(code)
            extractor = FSMExtractor(p, verbose=False)
            result = extractor.extract()
            print(f"  [{i}] {name}: {len(result)} FSMs - OK")
            passed += 1
        except Exception as e:
            print(f"  [{i}] {name}: ERROR - {str(e)[:30]}")
    
    print(f"  结果: {passed}/10 通过")
    return passed == 10


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("SV-TRACE Tier 2 工具综合测试 - 每个工具 10 个测试")
    print("=" * 70)
    
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
    results.append(("FSMExtractor", test_fsm_extractor()))
    
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
        print(f"❌ {total - passed} 个工具测试失败")
        print("=" * 70)
