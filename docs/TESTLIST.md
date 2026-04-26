# SV-Trace 测试清单

> v0.3 | 2026-04-26

## 测试统计

| 项目 | 数量 |
|------|------|
| 测试SV文件 | 30 |
| Python测试脚本 | 5 |
| 代码行数 | 3,500+ |

---

## 测试文件列表

### 核心模块 (10)

| 模块 | 测试文件 | 场景 |
|------|---------|------|
| DriverCollector | test_driver_collector.sv | 16 |
| LoadTracer | test_load_tracer.sv | 18 |
| DependencyAnalyzer | test_dependency_analyzer.sv | 18 |
| FanoutAnalyzer | test_fanout_analyzer.sv | 15 |
| DataFlowTracer | test_dataflow_tracer.sv | 18 |
| ControlFlowTracer | test_controlflow_tracer.sv | 18 |
| ConnectionTracer | test_connection_tracer.sv | 18 |
| ClockTreeAnalyzer | test_clock_tree_analyzer.sv | 12 |
| TimedPathAnalyzer | test_timed_path_analyzer.sv | 12 |
| ConditionCoverage | test_condition_coverage.sv | 12 |

### Corner Case (8)

- test_fsm_corners.sv
- test_cdc_corners.sv
- test_condition_corners.sv
- test_fanout_reset_corners.sv
- test_edge_cases_advanced.sv
- test_opentitan_style.sv
- test_verification_patterns.sv

### Targeted (8)

- test_fsm_targeted.sv
- test_cdc_targeted.sv
- test_condition_targeted.sv
- test_fanout_targeted.sv
- test_reset_targeted.sv

### Foundation (4)

- test_load_tracer_foundation.sv
- test_dataflow_foundation.sv
- test_controlflow_foundation.sv
- test_connection_foundation.sv

---

## 运行测试

```bash
python tests/test_all.py
python tests/test_comprehensive.py
```

---

## 总计: 30个测试文件, 180+测试场景

