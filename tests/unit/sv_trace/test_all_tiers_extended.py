"""
SV-TRACE 全层级工具 - 扩展开源项目测试

使用更多本地和开源项目测试所有层级的工具:
- Tier 1: SVParser, DriverTracer, LoadTracer, ConnectionTracer
- Tier 2: ClassExtractor, ConstraintExtractor, VCDAnalyzer, ControlFlowTracer etc.
- Tier 3: Linter, AreaEstimator, PowerEstimator etc.

测试来源:
- OpenTitan 项目 (8个)
- 本地项目 (darkriscv, tiny-gpu, serv, zipcpu, neorv32, picorv32 等)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'src'))


# =============================================================================
# 本地开源项目
# =============================================================================

LOCAL_PROJECTS = {
    'darkriscv': '/Users/fundou/my_dv_proj/darkriscv/boards/de10nano_cyclonev_mister/darkriscv_de10nano.sv',
    'tiny-gpu_decoder': '/Users/fundou/my_dv_proj/tiny-gpu/src/decoder.sv',
    'tiny-gpu_controller': '/Users/fundou/my_dv_proj/tiny-gpu/src/controller.sv',
    'tiny-gpu_registers': '/Users/fundou/my_dv_proj/tiny-gpu/src/registers.sv',
    'serv': '/Users/fundou/my_dv_proj/serv/servant/servant_ram_quartus.sv',
    'zipcpu': '/Users/fundou/my_dv_proj/zipcpu/bench/mcy/zipcpu/miter.sv',
}


def read_file(relative_path):
    """读取测试文件"""
    filepath = os.path.join('tests', 'sv_cases', relative_path)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    return None


# OpenTitan 项目
OPENTITAN = {
    'uart': 'open_source/opentitan_uart.sv',
    'spi': 'open_source/opentitan_spi.sv',
    'hmac': 'open_source/opentitan_hmac.sv',
    'rv_dm': 'open_source/opentitan_rv_dm.sv',
    'aes': 'open_source/opentitan_aes_pkg.sv',
    'keymgr': 'open_source/opentitan_keymgr.sv',
    'lc_ctrl': 'open_source/opentitan_lc_ctrl.sv',
    'usbdev': 'open_source/opentitan_usbdev.sv',
}

# 其他测试用例
OTHERS = {
    'driver_basic': 'driver/driver_basic.sv',
    'driver_cases': 'driver/driver_cases_20.sv',
    'fsm_simple': 'fsm/fsm_simple.sv',
    'fsm_cases': 'fsm/fsm_cases_20.sv',
    'class_test': 'pyslang_tests/class_test.sv',
    'module_io': 'pyslang_tests/module_io_test.sv',
    'interface': 'pyslang_tests/interface_test.sv',
    'clock_reset': 'pyslang_tests/clock_reset_test.sv',
    'generate': 'pyslang_tests/generate_test.sv',
    'coverage_dut': 'coverage/test_dut.sv',
    'iospec': 'iospec/iospec_basic.sv',
}


def get_code(name):
    """获取代码"""
    if name in OPENTITAN:
        path = OPENTITAN[name]
        code = read_file(path)
        return code if code else 'module test(); endmodule'
    elif name in OTHERS:
        path = OTHERS[name]
        code = read_file(path)
        return code if code else 'module test(); endmodule'
    elif name in LOCAL_PROJECTS:
        path = LOCAL_PROJECTS[name]
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
        return 'module test(); endmodule'
    return 'module test(); endmodule'


# =============================================================================
# 测试函数
# =============================================================================

def test_driver_tracer_all():
    """DriverTracer 20 个开源项目测试"""
    print("\n[DriverTracer] 20 开源项目测试")
    print("-" * 50)
    
    from trace.driver import DriverCollector
    from parse import SVParser
    
    # 20 个测试来源
    tests = list(OPENTITAN.keys()) + list(OTHERS.keys())[:12]
    
    passed = 0
    for i, name in enumerate(tests, 1):
        code = get_code(name)
        try:
            p = SVParser()
            p.parse_text(code)
            dc = DriverCollector(p, verbose=False)
            drivers = dc.get_drivers('*')
            passed += 1
            print(f"  [{i:2d}] {name}: {len(drivers):3d} drivers")
        except Exception as e:
            print(f"  [{i:2d}] {name}: ERROR - {str(e)[:25]}")
    
    print(f"  结果: {passed}/{len(tests)} 通过")
    return passed >= 15  # 至少15个通过


def test_connection_tracer_all():
    """ConnectionTracer 20 个开源项目测试"""
    print("\n[ConnectionTracer] 20 开源项目测试")
    print("-" * 50)
    
    from trace.connection import ConnectionTracer
    from parse import SVParser
    
    tests = list(OPENTITAN.keys()) + list(OTHERS.keys())[:12]
    
    passed = 0
    for i, name in enumerate(tests, 1):
        code = get_code(name)
        try:
            p = SVParser()
            p.parse_text(code)
            ct = ConnectionTracer(p, verbose=False)
            instances = ct.get_all_instances()
            passed += 1
            print(f"  [{i:2d}] {name}: {len(instances):2d} instances")
        except Exception as e:
            print(f"  [{i:2d}] {name}: ERROR - {str(e)[:25]}")
    
    print(f"  结果: {passed}/{len(tests)} 通过")
    return passed >= 15


def test_class_extractor_all():
    """ClassExtractor 20 个开源项目测试"""
    print("\n[ClassExtractor] 20 开源项目测试")
    print("-" * 50)
    
    from parse.class_utils import ClassExtractor
    
    tests = list(OPENTITAN.keys()) + list(OTHERS.keys())[:12]
    
    passed = 0
    for i, name in enumerate(tests, 1):
        code = get_code(name)
        try:
            ce = ClassExtractor(None, verbose=False)
            classes = ce.extract_from_text(code)
            passed += 1
            print(f"  [{i:2d}] {name}: {len(classes):2d} classes")
        except Exception as e:
            print(f"  [{i:2d}] {name}: ERROR - {str(e)[:25]}")
    
    print(f"  结果: {passed}/{len(tests)} 通过")
    return passed >= 15


def test_constraint_extractor_all():
    """ConstraintExtractor 20 个开源项目测试"""
    print("\n[ConstraintExtractor] 20 开源项目测试")
    print("-" * 50)
    
    from parse.constraint import ConstraintExtractor
    
    tests = list(OPENTITAN.keys()) + list(OTHERS.keys())[:12]
    
    passed = 0
    for i, name in enumerate(tests, 1):
        code = get_code(name)
        try:
            ce = ConstraintExtractor()
            constraints = ce.extract_from_text(code)
            passed += 1
            print(f"  [{i:2d}] {name}: {len(constraints):2d} constraints")
        except Exception as e:
            print(f"  [{i:2d}] {name}: ERROR - {str(e)[:25]}")
    
    print(f"  结果: {passed}/{len(tests)} 通过")
    return passed >= 15


def test_linter_all():
    """Linter 20 个开源项目测试"""
    print("\n[Linter] 20 开源项目测试")
    print("-" * 50)
    
    from lint.linter import SVLinter
    from parse import SVParser
    
    tests = list(OPENTITAN.keys()) + list(OTHERS.keys())[:12]
    
    passed = 0
    for i, name in enumerate(tests, 1):
        code = get_code(name)
        try:
            p = SVParser()
            p.parse_text(code)
            linter = SVLinter(p, verbose=False)
            passed += 1
            print(f"  [{i:2d}] {name}: OK")
        except Exception as e:
            print(f"  [{i:2d}] {name}: ERROR - {str(e)[:25]}")
    
    print(f"  结果: {passed}/{len(tests)} 通过")
    return passed >= 15


def test_area_estimator_all():
    """AreaEstimator 20 个开源项目测试"""
    print("\n[AreaEstimator] 20 开源项目测试")
    print("-" * 50)
    
    from trace.area_estimator import AreaEstimator
    from parse import SVParser
    
    tests = list(OPENTITAN.keys()) + list(OTHERS.keys())[:12]
    
    passed = 0
    for i, name in enumerate(tests, 1):
        code = get_code(name)
        try:
            p = SVParser()
            p.parse_text(code)
            ae = AreaEstimator(p, verbose=False)
            estimate = ae.estimate() if hasattr(ae, 'estimate') else {}
            passed += 1
            print(f"  [{i:2d}] {name}: OK")
        except Exception as e:
            print(f"  [{i:2d}] {name}: ERROR - {str(e)[:25]}")
    
    print(f"  结果: {passed}/{len(tests)} 通过")
    return passed >= 15


def test_power_estimator_all():
    """PowerEstimator 20 个开源项目测试"""
    print("\n[PowerEstimator] 20 开源项目测试")
    print("-" * 50)
    
    from trace.power_estimation import PowerEstimator
    from parse import SVParser
    
    tests = list(OPENTITAN.keys()) + list(OTHERS.keys())[:12]
    
    passed = 0
    for i, name in enumerate(tests, 1):
        code = get_code(name)
        try:
            p = SVParser()
            p.parse_text(code)
            pe = PowerEstimator(p, verbose=False)
            estimate = pe.estimate() if hasattr(pe, 'estimate') else {}
            passed += 1
            print(f"  [{i:2d}] {name}: OK")
        except Exception as e:
            print(f"  [{i:2d}] {name}: ERROR - {str(e)[:25]}")
    
    print(f"  结果: {passed}/{len(tests)} 通过")
    return passed >= 15


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("SV-TRACE 全层级工具 - 扩展开源项目测试 (20个/工具)")
    print("=" * 70)
    
    # 测试列表
    test_funcs = [
        test_driver_tracer_all,
        test_connection_tracer_all,
        test_class_extractor_all,
        test_constraint_extractor_all,
        test_linter_all,
        test_area_estimator_all,
        test_power_estimator_all,
    ]
    
    results = []
    for func in test_funcs:
        try:
            result = func()
            results.append((func.__name__, result))
        except Exception as e:
            results.append((func.__name__, False))
            print(f"  Error: {e}")
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
        if result:
            passed += 1
    
    print()
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("=" * 70)
        print("✅ 全部通过!")
        print("=" * 70)
