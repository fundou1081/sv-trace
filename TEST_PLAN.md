# SV-Trace 测试计划

## 模块功能矩阵

| 模块 | 文件 | 功能 | 状态 |
|------|------|------|------|
| **Driver/Load/ControlFlow 追踪** | | | |
| DriverCollector | `trace/driver.py` | 收集信号驱动信息 | ✅ 已修复 |
| LoadTracer | `trace/load.py` | 追踪信号加载点 | ✅ 已修复 |
| ControlFlowTracer | `trace/controlflow.py` | 追踪控制依赖 | ✅ 已修复 |
| **路径/数据流分析** | | | |
| DataPathAnalyzer | `trace/datapath.py` | 数据路径分析 | ✅ 正常 |
| ConnectionTracer | `trace/connection.py` | 连接追踪 | ✅ 正常 |
| BitSelectTracer | `trace/bitselect.py` | 位选择追踪 | ✅ 正常 |
| **高级分析** | | | |
| DataflowAnalyzer | `trace/dataflow.py` | 数据流分析 | ⚠️ 待验证 |
| DependencyAnalyzer | `trace/dependency.py` | 依赖分析 | ⚠️ 待验证 |
| FlowAnalyzer | `trace/flow_analyzer.py` | 流量分析 | ⚠️ 待验证 |
| PipelineAnalyzer | `trace/pipeline_analyzer.py` | 流水线分析 | ⚠️ 待验证 |

## 测试项目

| # | 项目 | 路径 | 复杂度 | 用途 |
|---|------|------|--------|------|
| 1 | picorv32 | `/my_dv_proj/picorv32/picorv32.v` | 中 | 基准测试 |
| 2 | serv_ctrl | `/my_dv_proj/serv/rtl/serv_ctrl.v` | 低 | 快速验证 |

## 测试用例 (TC-1 ~ TC-7)

### TC-1: DriverCollector 基本功能
**目的**: 验证信号驱动收集功能
**输入**: picorv32.v
**预期**: 收集到 ≥100 个信号，正确区分类型
**结果**: ✅ **119 signals, 182 drivers** (Continuous: 87, AlwaysFF: 95)

### TC-2: LoadTracer 功能
**目的**: 验证信号负载追踪
**输入**: picorv32.v
**预期**: 能找到信号的负载点
**结果**: ✅ **工作正常**

### TC-3: ControlFlowTracer 功能
**目的**: 验证控制依赖追踪
**输入**: picorv32.v
**预期**: 能找到 always_ff 块中的条件
**结果**: ✅ **工作正常**

### TC-4: DataPathAnalyzer 功能
**目的**: 验证数据路径分析
**输入**: picorv32.v
**预期**: 返回有效的数据路径
**结果**: ✅ **214 nodes**

### TC-5: ConnectionTracer 功能
**目的**: 验证模块实例连接追踪
**输入**: picorv32.v
**预期**: 能找到模块实例
**结果**: ✅ **4 instances**

### TC-6: BitSelectTracer 功能
**目的**: 验证位选择追踪
**输入**: picorv32.v
**预期**: 能追踪位选驱动
**结果**: ✅ **工作正常**

### TC-7: find_driver 方法
**目的**: 验证 DriverCollector 的 find_driver 方法
**输入**: picorv32.v
**预期**: 能根据信号名查找驱动
**结果**: ✅ **1 result for pcpi_int_wr**

## 多项目验证

### picorv32 (主测试)
| 模块 | 结果 | 详情 |
|------|------|------|
| DriverCollector | ✅ | 119 signals, 182 drivers |
| LoadTracer | ✅ | 21 signals with loads |
| ControlFlowTracer | ✅ | 79 signals with CF |
| DataPathAnalyzer | ✅ | 214 nodes |
| ConnectionTracer | ✅ | 4 instances |
| BitSelectTracer | ✅ | 正常 |

### serv_ctrl
| 模块 | 结果 | 详情 |
|------|------|------|
| DriverCollector | ✅ | 15 signals, 16 drivers |
| LoadTracer | ✅ | 2 signals with loads |
| ControlFlowTracer | ✅ | 2 signals with CF |
| DataPathAnalyzer | ✅ | 2 nodes |
| ConnectionTracer | ✅ | 0 instances |

## 测试执行记录

| 日期 | 测试项 | 结果 | 备注 |
|------|--------|------|------|
| 2026-04-24 | TC-1 picorv32 | ✅ | 119 signals, 182 drivers |
| 2026-04-24 | TC-1 serv_ctrl | ✅ | 15 signals, 16 drivers |
| 2026-04-24 | TC-2 picorv32 | ✅ | 21 signals with loads |
| 2026-04-24 | TC-2 serv_ctrl | ✅ | 2 signals with loads |
| 2026-04-24 | TC-3 picorv32 | ✅ | 79 signals with CF |
| 2026-04-24 | TC-3 serv_ctrl | ✅ | 2 signals with CF |
| 2026-04-24 | TC-4 picorv32 | ✅ | 214 nodes |
| 2026-04-24 | TC-4 serv_ctrl | ✅ | 2 nodes |
| 2026-04-24 | TC-5 picorv32 | ✅ | 4 instances |
| 2026-04-24 | TC-6 picorv32 | ✅ | BitSelectTracer works |
| 2026-04-24 | TC-7 find_driver | ✅ | 1 result |
| 2026-04-24 | All modules | ✅ | 7/7 通过 |

## 待验证模块

- [ ] DataflowAnalyzer
- [ ] DependencyAnalyzer
- [ ] FlowAnalyzer
- [ ] PipelineAnalyzer
- [ ] PerformanceAnalyzer
- [ ] ResourceEstimator
