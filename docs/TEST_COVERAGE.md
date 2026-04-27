# 测试覆盖率文档

## 测试子项目概览

| 子项目 | 测试文件数 | 测试用例数 |
|--------|-----------|-----------|
| sv_ast | 4 | 746+ |
| sv_trace | 6 | 31 |
| sv_verify | 8 | 23 |
| sv_codecheck | 3 | 10 |
| **总计** | **21** | **810+** |

---

## 1. sv_ast (746+ 个测试用例)

**定位**: 基于 pyslang 的 SystemVerilog AST 解析工具库

| 测试文件 | 测试用例数 |
|----------|-----------|
| test_svtests.py | 716 (sv-tests 完整测试集) |
| test_all.py | 10 |
| test_class.py | 18 |
| test_parse.py | 2 |

**数据来源**: ~/my_dv_proj/sv-tests/tests/ (830 个 .sv 文件)

---

## 2. sv_trace (31 个测试用例)

**定位**: RTL 信号追踪、数据流分析

| 测试文件 | 测试用例数 |
|----------|-----------|
| test_driver.py | 15 |
| test_dependency.py | 4 |
| test_foundation.py | 5 |
| test_foundation_modules.py | 3 |
| test_control_dependency.py | 3 |
| test_comprehensive.py | 1 |

---

## 3. sv_verify (23 个测试用例)

**定位**: 验证工具、调试分析

| 测试文件 | 测试用例数 |
|----------|-----------|
| test_new_features.py | 8 |
| test_targeted.py | 6 |
| test_corners.py | 5 |
| test_app_tools.py | 2 |
| test_fsm.py | 2 |

---

## 4. sv_codecheck (10 个测试用例)

**定位**: 代码质量检查、Linting

| 测试文件 | 测试用例数 |
|----------|-----------|
| test_real_projects.py | 4 |
| test_quality_performance.py | 3 |
| test_limitation.py | 3 |

---

## 运行测试

```bash
# sv_ast (包含 sv-tests)
cd tests/unit/sv_ast && python3 test_svtests.py

# sv_trace
cd tests/unit/sv_trace && python3 test_*.py

# 全部测试
python3 tests/unit/run_subproject_tests.py
```

*更新于 2026-04-28*
