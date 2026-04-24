# sv-trace 测试套件

## 测试用例库

tests/sv_cases/:
- driver/driver_basic.sv - DriverTracer测试
- fsm/fsm_simple.sv - FSMExtractor测试
- cdc/cdc_basic.sv - CDC分析测试
- iospec/iospec_basic.sv - IOSpecExtractor测试
- dependency/dependency_hierarchy.sv - 模块依赖测试
- lint/lint_issues.sv - Lint问题测试

运行: python3 tests/run_all_tests.py

sv-tests兼容性: 1030 passed, 0 failed

