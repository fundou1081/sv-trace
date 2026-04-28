# 测试覆盖率文档

## 测试子项目概览

| 子项目 | 测试文件数 | 测试用例数 |
|--------|-----------|-----------|
| sv_ast | 8 | 740+ |
| sv_trace | 48 | 100+ |
| sv_verify | 11 | 30+ |
| sv_codecheck | 5 | 10+ |
| **总计** | **72** | **880+** |

---

## 1. sv_ast (740+ 测试用例)

**定位**: 基于 pyslang 的 SystemVerilog AST 解析工具库

### 测试数据来源
| 来源 | 文件数 |
|------|--------|
| sv-tests | 830 |
| OpenTitan | 5 |
| XiangShan | 3 |

### 测试文件
- test_svtests.py, test_all.py, test_class.py, test_parse.py, test_iospec.py, test_opentitan.py, test_xiangshan.py

---

## 2. sv_trace (100+ 测试用例)

**定位**: RTL 信号追踪、数据流分析

### 测试数据来源
| 来源 | 文件数 |
|------|--------|
| targeted | 40 |
| picorv32/serv/basic_verilog | 3 |
| OpenTitan | 2 |
| darkriscv | 1 |
| 边界场景 | 10 |
| 常用场景 | 5 |

### 测试文件
- test_driver.py, test_comprehensive.py, test_foundation.py, test_foundation_modules.py, test_dependency.py, test_control_dependency.py, test_opentitan.py, test_darkriscv.py, test_edge_cases.py, test_common_scenarios.py, 等 48 个

---

## 3. sv_verify (30+ 测试用例)

**定位**: 验证工具、调试分析

### 测试文件
- test_app_tools.py, test_fsm.py, test_hierarchy.py, test_targeted.py, test_corners.py, test_new_features.py, test_opentitan.py, test_neorv32.py, test_real_projects.py

---

## 4. sv_codecheck (10+ 测试用例)

**定位**: 代码质量检查、Linting

### 测试文件
- test_limitation.py, test_quality_performance.py, test_real_projects.py, test_tinygpu.py

---

## 运行测试

```bash
# 运行单个子项目测试
cd tests/unit/sv_ast && python3 test_svtests.py

# 运行全部子项目测试
python3 tests/unit/run_subproject_tests.py
```

### 测试数据目录
- sv-tests: ~/my_dv_proj/sv-tests/tests/
- OpenTitan: ~/my_dv_proj/opentitan/hw/ip/
- 项目特定: tests/targeted/, tests/sv_cases/

*更新于 2026-04-28*
