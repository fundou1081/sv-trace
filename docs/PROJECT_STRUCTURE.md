# SV-TRACE 项目结构

## 目录结构

```
sv-trace/
├── src/                    # 核心源代码 (62 files)
│   ├── parse/             # 解析器 (9 files)
│   ├── trace/            # 追踪模块 (22 files)
│   ├── query/           # 查询模块 (13 files)
│   └── debug/           # 调试模块 (21 files)
│
├── tests/                 # 测试 (62 files)
│   ├── test_*.py         # 基本测试
│   ├── edge_cases/       # 边界测试
│   └── ...
│
├── docs/                  # 文档 (21 files)
│   ├── MODULE_SUMMARY.md # 模块汇总
│   ├── MODULE_DETAILS.md # 详细API文档
│   └── *.md              # 各模块文档
│
└── [项目根目录文件]       # 配置文件等
``` 

## 统计

| 目录 | 文件数 |
|------|--------|
| src/parse | 9 |
| src/trace | 22 |
| src/query | 13 |
| src/debug | 21 |
| **src总计** | **65** |
| tests/ | 62 |
| docs/ | 21 |
| 项目根目录 | 41 |

## 模块列表

### Trace 模块 (22)
- driver, load, datapath, dependency, connection
- controlflow, dataflow, bitselect, flow_analyzer
- pipeline_analyzer, timing_depth, timing_path
- performance, resource_estimation, power_estimation
- throughput_estimation, sim_performance, visualize
- driver_simple

### Query 模块 (13)
- signal, path, condition_relation_extractor
- overflow_risk_detector, datapath_boundary_analyzer
- fuzzy_path_matcher, nested_condition_expander
- sample_condition_analyzer, stimulus_path_finder
- stim1

### Debug 模块 (21)
- class_extractor, class_hierarchy, class_info
- class_usage, class_quality, class_relation
- class_const_parser, constraint_parser
- design_evaluator, assistant, complexity

## 测试覆盖

| 测试类型 | 状态 |
|----------|------|
| 核心测试 | ✅ 6/6 |
| 边界测试 | ✅ 38/38 |
| P1模块 | ✅ 5/5 |
| P2模块 | ✅ 4/4 |
| P3模块 | ✅ 8+ |

## 最新提交

- 测试: 边界测试100% (38/38)
- 文档: MODULE_DETAILS.md

---

*最后更新: 2026-04-25*
