# SV-Trace 工具分级

## 概述

本文档对SV-Trace项目中的工具进行分级，按重要性和使用场景分类。

---

## 🏆 Tier 1 - 核心工具 (必备)

### 解析引擎
| 工具 | CLI | Skill | 说明 |
|------|-----|-------|------|
| `parser.py` | - | - | pyslang SystemVerilog解析器 |
| `constraint_parser_v2.py` | `sv-constraint` | ✅ | 约束解析+z3冲突检测 |
| `probabilistic_constraint.py` | `sv-constraint-prob` | ✅ | 约束概率分析 |

### TB分析
| 工具 | CLI | Skill | 说明 |
|------|-----|-------|------|
| `tb_analyzer/complexity.py` | `sv-tb-complexity` | ✅ | TB复杂度分析(40+指标) |
| `class_extractor.py` | - | - | Class提取 |
| `class_relation.py` | - | - | 类关系图 |

**推荐使用场景**: 验证IP开发、TB质量评估

---

## ⭐ Tier 2 - 重要工具 (常用)

### RTL追踪
| 工具 | CLI | Skill | 说明 |
|------|-----|-------|------|
| `trace/driver.py` | - | - | 驱动追踪 |
| `trace/load.py` | - | - | 负载追踪 |
| `trace/connection.py` | - | - | 连接追踪 |
| `trace/dataflow.py` | - | - | 数据流分析 |

### 数据通路
| 工具 | CLI | Skill | 说明 |
|------|-----|-------|------|
| `trace/data_path/` | `sv-datapath` | ✅ | 数据通路+corner case |
| `trace/datapath.py` | - | - | 数据通路分析 |
| `trace/pipeline_analyzer.py` | - | - | Pipeline分析 |

### 质量分析
| 工具 | CLI | Skill | 说明 |
|------|-----|-------|------|
| `complexity.py` | `sv-quality` | ✅ | 代码复杂度 |
| `signal_classifier.py` | `sv-signal` | ✅ | 信号分类 |

**推荐使用场景**: RTL开发、验证计划制定

---

## 📦 Tier 3 - 扩展工具 (场景)

### 时序分析
| 工具 | Skill | 说明 |
|------|-------|------|
| `trace/timing_path.py` | - | 时序路径提取 |
| `trace/timing_depth.py` | - | 时序深度分析 |
| `timing-equivalence/` | ✅ | 时序等价性 |
| `timing-fix-guide/` | ✅ | 时序修复指南 |

### CDC分析
| 工具 | Skill | 说明 |
|------|-------|------|
| `trace/cdc_analyzer.py` | - | CDC分析器 |
| `cdc-doc-skill/` | ✅ | CDC文档生成 |

### 覆盖率
| 工具 | Skill | 说明 |
|------|-------|------|
| `trace/vcd_analyzer.py` | - | VCD分析 |
| `verify/coverage_model.py` | - | 覆盖率模型 |

### 性能估算
| 工具 | Skill | 说明 |
|------|-------|------|
| `trace/performance.py` | - | 性能估算 |
| `trace/sim_performance.py` | - | 仿真性能 |
| `trace/resource_estimation.py` | - | 资源估算 |
| `trace/power_estimation.py` | - | 功耗估算 |
| `trace/throughput_estimation.py` | - | 吞吐量估算 |

**推荐使用场景**: 性能优化、功耗分析

---

## 🔧 Tier 4 - 辅助工具 (特定场景)

### 验证支持
| 工具 | Skill | 说明 |
|------|-------|------|
| `verify/risk_evaluator.py` | - | 风险评估 |
| `verify/test_manager.py` | - | 测试管理 |
| `verify/failure_cluster.py` | - | 失败聚类 |
| `verify/seed_manager.py` | - | 随机种子管理 |
| `verify/mode_switch_test.py` | - | 模式切换测试 |

### 自动化生成
| 工具 | Skill | 说明 |
|------|-------|------|
| `verify/constraint_generator.py` | - | 约束生成器 |
| `verify/stimulus_suggester.py` | - | 激励建议 |
| `verify/coverage_advisor.py` | - | 覆盖率建议 |

### 调试工具
| 工具 | Skill | 说明 |
|------|-------|------|
| `trace/visualize.py` | - | 可视化 |
| `trace/vcd_analyzer.py` | - | 波形分析 |
| `bug-tracker/` | ✅ | Bug追踪 |
| `debug-knowledge-base/` | ✅ | 知识库 |

### 文档生成
| 工具 | Skill | 说明 |
|------|-------|------|
| `rtl-2-assertion/` | ✅ | RTL到断言 |
| `spec-checker/` | ✅ | 规格检查 |
| `spec-corner-case/` | ✅ | Corner case |
| `spec-to-verification/` | ✅ | 规格到验证 |

### 其他
| 工具 | Skill | 说明 |
|------|-------|------|
| `trace/controlflow.py` | - | 控制流 |
| `trace/dependency.py` | - | 依赖分析 |
| `trace/bitselect.py` | - | 位选择 |
| `clock-gating-advisor/` | ✅ | Clock gating建议 |
| `feature-prioritizer/` | ✅ | 特性优先级 |
| `team-communication-log/` | ✅ | 团队沟通 |

---

## 📁 CLI工具速查

| CLI | Tier | 功能 |
|-----|------|------|
| `sv-constraint` | 1 | 约束分析+z3 |
| `sv-constraint-prob` | 1 | 约束概率分析 |
| `sv-tb-complexity` | 1 | TB复杂度分析 |
| `sv-datapath` | 2 | 数据通路 |
| `sv-quality` | 2 | 代码质量 |
| `sv-signal` | 2 | 信号分类 |
| `verify-suite` | 3 | 验证套件 |
| `verify-test` | 3 | 测试验证 |
| `bug-tracker` | 4 | Bug追踪 |

---

## 📊 统计

| 分类 | 数量 |
|------|------|
| 核心解析器 | 1 |
| Tier 1 工具 | 3 |
| Tier 2 工具 | 7 |
| Tier 3 工具 | 12 |
| Tier 4 工具 | 20+ |
| **总计CLI** | 9 |
| **总计Skills** | 20+ |

---

## 选择指南

**问: 我应该使用哪些工具?**

| 场景 | 推荐工具 |
|------|----------|
| 新项目启动 | `sv-constraint`, `sv-tb-complexity` |
| TB质量评估 | `sv-tb-complexity`, `sv-quality` |
| RTL分析 | `sv-datapath`, `sv-signal` |
| 性能优化 | `sv-tb-complexity`, timing相关 |
| 覆盖率提升 | coverage相关工具 |
| Debug | bug-tracker, visualize |
