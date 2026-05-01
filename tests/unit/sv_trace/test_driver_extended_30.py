"""
DriverTracer 扩展开源项目测试 - 30个测试

包含:
- OpenTitan 8个
- 本地项目 (darkriscv, tiny-gpu, serv, zipcpu) 4个
- basic_verilog 10个
- 测试用例 8个
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'src'))

from parse import SVParser
from trace.driver import DriverCollector


# 30个测试来源
TEST_SOURCES = [
    # OpenTitan (8)
    ('OPENTITAN_uart', 'tests/sv_cases/open_source/opentitan_uart.sv'),
    ('OPENTITAN_spi', 'tests/sv_cases/open_source/opentitan_spi.sv'),
    ('OPENTITAN_hmac', 'tests/sv_cases/open_source/opentitan_hmac.sv'),
    ('OPENTITAN_rv_dm', 'tests/sv_cases/open_source/opentitan_rv_dm.sv'),
    ('OPENTITAN_aes', 'tests/sv_cases/open_source/opentitan_aes_pkg.sv'),
    ('OPENTITAN_keymgr', 'tests/sv_cases/open_source/opentitan_keymgr.sv'),
    ('OPENTITAN_lc_ctrl', 'tests/sv_cases/open_source/opentitan_lc_ctrl.sv'),
    ('OPENTITAN_usbdev', 'tests/sv_cases/open_source/opentitan_usbdev.sv'),
    
    # 本地项目 (4)
    ('LOCAL_darkriscv', '/Users/fundou/my_dv_proj/darkriscv/boards/de10nano_cyclonev_mister/darkriscv_de10nano.sv'),
    ('LOCAL_tiny_gpu', '/Users/fundou/my_dv_proj/tiny-gpu/src/decoder.sv'),
    ('LOCAL_serv', '/Users/fundou/my_dv_proj/serv/servant/servant_ram_quartus.sv'),
    ('LOCAL_zipcpu', '/Users/fundou/my_dv_proj/zipcpu/bench/mcy/zipcpu/miter.sv'),
    
    # basic_verilog (10)
    ('BV_adder_tree', '/Users/fundou/my_dv_proj/basic_verilog/adder_tree.sv'),
    ('BV_barrel_shifter', '/Users/fundou/my_dv_proj/basic_verilog/barrel_shifter.sv'),
    ('BV_clk_divider', '/Users/fundou/my_dv_proj/basic_verilog/clk_divider.sv'),
    ('BV_comb_repeater', '/Users/fundou/my_dv_proj/basic_verilog/comb_repeater.sv'),
    ('BV_debounce', '/Users/fundou/my_dv_proj/basic_verilog/debounce_v2.sv'),
    ('BV_fifo_sync', '/Users/fundou/my_dv_proj/basic_verilog/fifo_sync.sv'),
    ('BV_lfsr', '/Users/fundou/my_dv_proj/basic_verilog/lfsr.sv'),
    ('BV_mac', '/Users/fundou/my_dv_proj/basic_verilog/mac.sv'),
    ('BV_ping_pong', '/Users/fundou/my_dv_proj/basic_verilog/ping_pong_buf.sv'),
    ('BV_uart_rs232', '/Users/fundou/my_dv_proj/basic_verilog/uart_rs232.sv'),
    
    # 测试用例 (8)
    ('TEST_driver_basic', 'tests/sv_cases/driver/driver_basic.sv'),
    ('TEST_driver_cases', 'tests/sv_cases/driver/driver_cases_20.sv'),
    ('TEST_fsm_simple', 'tests/sv_cases/fsm/fsm_simple.sv'),
    ('TEST_fsm_cases', 'tests/sv_cases/fsm/fsm_cases_20.sv'),
    ('TEST_class', 'tests/sv_cases/pyslang_tests/class_test.sv'),
    ('TEST_module_io', 'tests/sv_cases/pyslang_tests/module_io_test.sv'),
    ('TEST_interface', 'tests/sv_cases/pyslang_tests/interface_test.sv'),
    ('TEST_clock', 'tests/sv_cases/pyslang_tests/clock_reset_test.sv'),
]


def test_driver_extended():
    """测试 DriverTracer"""
    print("=" * 60)
    print("DriverTracer 30 扩展开源项目测试")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    results = []
    for i, (name, path) in enumerate(TEST_SOURCES, 1):
        if not os.path.exists(path):
            print(f"[{i:2d}] {name:20s}: FILE NOT FOUND")
            failed += 1
            continue
        
        try:
            with open(path) as f:
                code = f.read()
            
            # 解析
            p = SVParser()
            p.parse_text(code)
            
            # 提取驱动
            dc = DriverCollector(p, verbose=False)
            drivers = dc.get_drivers('*')
            
            results.append((name, len(drivers)))
            passed += 1
            print(f"[{i:2d}] {name:20s}: {len(drivers):3d} drivers ✅")
            
        except Exception as e:
            failed += 1
            print(f"[{i:2d}] {name:20s}: ERROR - {str(e)[:25]} ❌")
    
    print("=" * 60)
    print(f"通过: {passed}/30")
    print(f"失败: {failed}/30")
    
    # 按驱动数排序
    print()
    print("按驱动数排序:")
    for name, count in sorted(results, key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {name:20s}: {count:3d}")
    
    return passed >= 25


if __name__ == '__main__':
    test_driver_extended()


def is_instantiation_template(code):
    """检测文件是否为实例化模板 (非实际硬件)"""
    # 检查是否包含 instantiation template 标记
    if 'INSTANTIATION TEMPLATE' in code:
        return True
    
    # 检查是否有实际的 always_ff/always_comb/assign 语句
    has_hw = any([
        'always_ff' in code,
        'always_comb' in code,
        'always_latch' in code,
        'assign ' in code,
    ])
    
    return not has_hw


# 添加文件类型检测测试
def test_detect_file_types():
    """测试文件类型检测"""
    print("\n文件类型检测:")
    print("-" * 40)
    
    import os
    base = '/Users/fundou/my_dv_proj/basic_verilog'
    
    files_to_check = [
        'cdc_data.sv',
        'pdm_modulator.sv', 
        'adder_tree.sv',
        'fifo_combiner.sv',
    ]
    
    for f in files_to_check:
        path = os.path.join(base, f)
        if not os.path.exists(path):
            continue
            
        with open(path) as fp:
            code = fp.read()
        
        is_template = is_instantiation_template(code)
        is_empty = True if 'always_ff' in code or 'always_comb' in code else False
        
        print(f"{f}: template={is_template}, has_hw={is_empty}")

    return True


if __name__ == '__main__':
    test_detect_file_types()
