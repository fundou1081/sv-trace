# SV-Trace 测试计划 V2

## 测试范围

基于 SV-Trace 的 44+ 功能模块和开源项目列表，制定本测试计划。

## 测试项目

| # | 项目 | 路径 | 复杂度 | 描述 | 适用模块 |
|---|------|------|--------|------|----------|
| 1 | picorv32 | `picorv32/picorv32.v` | 中 | RISC-V 软核 (92KB) | 核心 trace 模块 |
| 2 | serv_top | `serv/rtl/serv_top.v` | 中 | SERV RISC-V 完整 top | 核心 trace 模块 |
| 3 | tiny-gpu | `tiny-gpu/src/gpu.sv` | 中 | GPU 核心 | 核心 trace 模块 |
| 4 | Vortex | `vortex/hw/rtl/Vortex.sv` | 中 | GPU SoC | 核心 trace 模块 |
| 5 | adder_tree | `basic_verilog/adder_tree.sv` | 低 | 加法器树 | 基础验证 |
| 6 | axi_logger | `basic_verilog/axi4l_logger.sv` | 中 | AXI 总线 | connection 追踪 |
| 7 | XiangShan | `XiangShan/` | 高 | 开源 RISC-V 处理器 | 全模块测试 |

## 测试模块

### Phase 1: 核心 trace 模块 (已验证)

| # | 模块 | 测试方法 | 验证状态 |
|---|------|---------|---------|
| 1 | DriverCollector | signals >= 1 | ✅ DONE |
| 2 | LoadTracer | find_load() 方法 | ✅ DONE |
| 3 | ControlFlowTracer | find_control_dependencies() | ✅ DONE |
| 4 | DataPathAnalyzer | analyze() 方法 | ✅ DONE |
| 5 | ConnectionTracer | 实例数量 + 深度追踪 | ✅ DONE |

### Phase 2: 核心 trace 模块 (待测试)

| # | 模块 | 功能 | 测试用例 |
|---|------|------|---------|
| 6 | BitSelectTracer | 位选信号分析 | trace_bit_drivers(), get_driven_bits() |
| 7 | DependencyAnalyzer | 依赖关系分析 | analyze(), find_path() |
| 8 | DataFlowTracer | 数据流分析 | analyze_flow() |
| 9 | FlowAnalyzer | 统一信号流 | get_flow_graph() |
| 10 | PipelineAnalyzer | 流水线分析 | detect_stages() |
| 11 | PerformanceAnalyzer | 性能估算 | estimate_performance() |
| 12 | PowerEstimator | 功耗估算 | estimate_power() |
| 13 | ResourceEstimator | 资源估算 | count_operators() |
| 14 | TimingDepthAnalyzer | 时序深度 | analyze_depth() |
| 15 | TimingPathExtractor | 时序路径 | extract_paths() |
| 16 | ThroughputEstimator | 吞吐率估算 | estimate_throughput() |
| 17 | SimPerformanceAnalyzer | 仿真性能 | estimate_sim_time() |
| 18 | Visualizer | 可视化 | generate_dot() |

### Phase 3: Debug 分析器

| # | 模块 | 功能 | 测试用例 |
|---|------|------|---------|
| 19 | CDCAnalyzer | 跨时钟域分析 | detect_issues() |
| 20 | ClockDomainAnalyzer | 时钟域分析 | analyze_domains() |
| 21 | ClockTreeAnalyzer | 时钟树分析 | build_tree() |
| 22 | DanglingPortDetector | 悬空端口 | find_dangling() |
| 23 | MultiDriverDetector | 多驱动检测 | find_multi() |
| 24 | ResetDomainAnalyzer | 复位域分析 | analyze_resets() |
| 25 | UninitializedDetector | 未初始化检测 | find_uninit() |
| 26 | XValueAnalyzer | X 值传播 | trace_x() |
| 27 | CoverageGenerator | 覆盖率生成 | generate() |
| 28 | RiskCollector | 风险收集 | collect_risks() |
| 29 | RootCauseAnalyzer | 根因分析 | analyze_root_cause() |

### Phase 4: Query 模块

| # | 模块 | 功能 | 测试用例 |
|---|------|------|---------|
| 30 | ConditionRelationExtractor | 条件关系 | extract() |
| 31 | DataPathBoundaryAnalyzer | 路径边界 | analyze() |
| 32 | FuzzyPathMatcher | 模糊匹配 | match() |
| 33 | NestedConditionExpander | 嵌套展开 | expand() |
| 34 | OverflowRiskDetector | 溢出检测 | detect() |
| 35 | PathQuerier | 路径查询 | query_path() |
| 36 | SampleConditionAnalyzer | 采样分析 | analyze() |
| 37 | SignalQuerier | 信号查询 | query_signal() |
| 38 | StimulusPathFinder | 激励路径 | find_path() |

## 测试矩阵

| 项目 \ 模块 | Driver | Load | CF | DataPath | Connection | BitSelect | Dep | Pipeline | CDC | ... |
|------------|--------|------|-----|----------|-----------|-----------|-----|----------|-----|-----|
| picorv32 | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | |
| serv_top | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| tiny-gpu | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| Vortex | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| axi_logger | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| XiangShan | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |

- ✅ = 已验证
- ⬜ = 待验证

## 深度追踪测试 (已完成)

| 测试类型 | 深度 | 结果 |
|---------|------|------|
| 线性 Pipeline | 10K ~ 100K | ✅ PASS |
| 复杂拓扑 | Diamond/Broadcast/Cycle | ✅ PASS |

## 下一步

1. **Phase 2**: 测试剩余核心 trace 模块 (BitSelect, Dependency, Pipeline 等)
2. **Phase 3**: 测试 Debug 分析器
3. **Phase 4**: 测试 Query 模块

## 提交记录

| Commit | 描述 |
|--------|------|
| `48bd2c7` | docs: update TEST_PLAN.md - complete verification with depth testing |
