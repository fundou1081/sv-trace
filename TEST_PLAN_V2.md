# SV-Trace 测试计划 V2

## 测试范围

基于 SV-Trace 的 44+ 功能模块和开源项目列表，制定本测试计划。

---

## 一、测试项目

| # | 项目 | 路径 | 复杂度 | 描述 | 适用模块 |
|---|------|------|--------|------|----------|
| 1 | picorv32 | `picorv32/picorv32.v` | 中 | RISC-V 软核 (92KB, 119 signals) | 核心 trace 模块 |
| 2 | serv_top | `serv/rtl/serv_top.v` | 中 | SERV RISC-V 完整 top | 核心 trace 模块 |
| 3 | tiny-gpu | `tiny-gpu/src/gpu.sv` | 中 | GPU 核心 (4 instances) | 核心 trace 模块 |
| 4 | Vortex | `vortex/hw/rtl/Vortex.sv` | 中 | GPU SoC (6 instances) | 核心 trace 模块 |
| 5 | adder_tree | `basic_verilog/adder_tree.sv` | 低 | 加法器树 (简单) | 基础验证 |
| 6 | axi_logger | `basic_verilog/axi4l_logger.sv` | 中 | AXI 总线 (3 instances) | connection 追踪 |
| 7 | XiangShan | `XiangShan/` | 高 | 开源 RISC-V 处理器 | 全模块测试 |

### 测试项目详细要求

| 项目 | 必需特征 | 用于验证 |
|------|---------|---------|
| picorv32 | always_ff, always_comb, wire, reg | Driver, Load, CF, DataPath |
| serv_top | 多模块实例化 | Connection, Pipeline |
| tiny-gpu | 跨模块连接 | BitSelect, Dependency |
| Vortex | 复杂层次结构 | Flow, Visualizer |
| axi_logger | 总线协议 | CDC, MultiDriver |
| XiangShan | 大型复杂设计 | 性能, 极限测试 |

---

## 二、测试模块详细规范

### Phase 1: 核心 trace 模块 (已验证 ✅)

| # | 模块 | 主方法 | 输入 | 输出 | 验证指标 | 状态 |
|---|------|--------|------|------|----------|------|
| 1 | DriverCollector | get_drivers() | signal_name | List[Driver] | signals ≥ 1, drivers ≥ signals | ✅ |
| 2 | LoadTracer | find_load() | signal_name | List[Load] | returns list (can be empty) | ✅ |
| 3 | ControlFlowTracer | find_control_dependencies() | signal_name | ControlFlow | returns ControlFlow object | ✅ |
| 4 | DataPathAnalyzer | analyze() | signal_name | DataPath | nodes > 0 | ✅ |
| 5 | ConnectionTracer | get_all_instances() | - | List[Instance] | instances ≥ 0, 深度追踪 100K+ | ✅ |

### Phase 2: 核心 trace 模块 (待测试 ⬜)

| # | 模块 | 主方法 | 输入 | 输出 | 验证指标 | 测试优先级 |
|---|------|--------|------|------|----------|-----------|
| 6 | BitSelectTracer | trace_bit_drivers() | signal[7:0] | bit-level drivers | bits 0-7 traced | P1-Critical |
| 7 | DependencyAnalyzer | analyze() | signal_name | DependencyGraph | edges > 0 | P1-Critical |
| 8 | DataFlowTracer | analyze_flow() | signal_name | DataFlowGraph | paths found | P1-Critical |
| 9 | FlowAnalyzer | get_flow_graph() | - | FlowGraph | nodes > 0 | P2-Important |
| 10 | PipelineAnalyzer | detect_stages() | - | List[Stage] | stages ≥ 1 | P1-Critical |
| 11 | PerformanceAnalyzer | estimate_performance() | - | PerformanceReport | report generated | P2-Important |
| 12 | PowerEstimator | estimate_power() | - | PowerBreakdown | power numbers > 0 | P3-Nice |
| 13 | ResourceEstimator | count_operators() | - | OperatorStats | LUT/FF counts | P2-Important |
| 14 | TimingDepthAnalyzer | analyze_depth() | signal | depth value | depth ≥ 0 | P1-Critical |
| 15 | TimingPathExtractor | extract_paths() | - | List[TimingPath] | paths ≥ 0 | P2-Important |
| 16 | ThroughputEstimator | estimate_throughput() | - | Mbps value | throughput > 0 | P3-Nice |
| 17 | SimPerformanceAnalyzer | estimate_sim_time() | - | seconds | time > 0 | P3-Nice |
| 18 | Visualizer | generate_dot() | - | DOT string | valid DOT syntax | P2-Important |

### Phase 3: Debug 分析器 (待测试 ⬜)

| # | 模块 | 主方法 | 验证指标 | 测试优先级 |
|---|------|--------|----------|-----------|
| 19 | CDCAnalyzer | detect_issues() | issues detected | P1-Critical |
| 20 | ClockDomainAnalyzer | analyze_domains() | domains ≥ 1 | P1-Critical |
| 21 | ClockTreeAnalyzer | build_tree() | tree built | P2-Important |
| 22 | DanglingPortDetector | find_dangling() | ports found | P2-Important |
| 23 | MultiDriverDetector | find_multi() | issues detected | P1-Critical |
| 24 | ResetDomainAnalyzer | analyze_resets() | resets tracked | P2-Important |
| 25 | UninitializedDetector | find_uninit() | signals found | P2-Important |
| 26 | XValueAnalyzer | trace_x() | x-propagation traced | P2-Important |
| 27 | CoverageGenerator | generate() | coverage % | P3-Nice |
| 28 | RiskCollector | collect_risks() | risks ranked | P3-Nice |
| 29 | RootCauseAnalyzer | analyze_root_cause() | cause chain | P2-Important |

### Phase 4: Query 模块 (待测试 ⬜)

| # | 模块 | 主方法 | 验证指标 | 测试优先级 |
|---|------|--------|----------|-----------|
| 30 | ConditionRelationExtractor | extract() | relations found | P2-Important |
| 31 | DataPathBoundaryAnalyzer | analyze() | boundaries identified | P2-Important |
| 32 | FuzzyPathMatcher | match() | matches found | P3-Nice |
| 33 | NestedConditionExpander | expand() | expanded conditions | P2-Important |
| 34 | OverflowRiskDetector | detect() | risks identified | P1-Critical |
| 35 | PathQuerier | query_path() | path found | P2-Important |
| 36 | SampleConditionAnalyzer | analyze() | conditions analyzed | P3-Nice |
| 37 | SignalQuerier | query_signal() | signal info | P2-Important |
| 38 | StimulusPathFinder | find_path() | path from stimulus | P2-Important |

---

## 三、测试用例规范

### 3.1 标准测试用例模板

```
Test Case ID: TC-[模块]-[编号]
Module: [模块名]
Method: [被测方法]
Input: [输入参数]
Expected Output: [期望输出]
Pass Criteria: [判定标准]
```

### 3.2 必需测试场景

| 场景 | 描述 | 适用模块 |
|------|------|---------|
| 基本功能 | 输入有效信号，返回正确结果 | 全部 |
| 空输入 | 无信号时的行为 | 全部 |
| 大量信号 | 100+ signals 的性能 | 全部 |
| 深度追踪 | 1000+ 层级追踪 | Connection, DataPath |
| 边界条件 | 位选择 [0], [31], [7:0] | BitSelect |
| 模块依赖 | 跨模块信号传播 | Connection |

### 3.3 负面测试用例

| 场景 | 描述 | 期望行为 |
|------|------|---------|
| 空模块 | module xxx; endmodule | 返回空列表/0 |
| 无信号模块 | 只有端口无内部信号 | 返回 0 |
| 非法信号名 | 不存在的信号 | 返回空/None |
| 循环依赖 | A→B→C→A | 循环检测/处理 |

---

## 四、完整测试矩阵

| 项目 \ 模块 | Drv | Load | CF | DP | Conn | Bit | Dep | Flow | Pipe | CDC | Multi | ... |
|------------|-----|------|----|----|------|-----|-----|------|------|-----|-------|-----|
| picorv32 | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| serv_top | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| tiny-gpu | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| Vortex | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| axi_logger | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| XiangShan | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |

**图例**: ✅=已验证 ⬜=待测试

---

## 五、性能基准

| 模块 | 指标 | picorv32 (119 signals) | XiangShan (估计 10K+ signals) |
|------|------|------------------------|-------------------------------|
| DriverCollector | 解析时间 | < 1s | < 10s |
| ConnectionTracer | 实例识别 | < 1s | < 10s |
| DataPathAnalyzer | 路径分析 | < 2s | < 30s |
| Visualizer | DOT 生成 | < 1s | < 10s |

---

## 六、测试依赖关系

```
DriverCollector ─────┬─────> LoadTracer
                    │
                    ├─────> ControlFlowTracer
                    │
                    └─────> DataPathAnalyzer
                               │
ConnectionTracer ────> FlowAnalyzer ────> Visualizer
                               │
                               └─────> PipelineAnalyzer
                                         │
                                         └─────> TimingDepthAnalyzer
```

**注意**: Debug 分析器依赖 DriverCollector 的输出

---

## 七、测试执行计划

### Phase 1 (已完成)
- [x] DriverCollector
- [x] LoadTracer
- [x] ControlFlowTracer
- [x] DataPathAnalyzer
- [x] ConnectionTracer (含深度测试)

### Phase 2 (建议顺序)
- [ ] BitSelectTracer ⭐
- [ ] DependencyAnalyzer ⭐
- [ ] PipelineAnalyzer ⭐
- [ ] TimingDepthAnalyzer ⭐
- [ ] DataFlowTracer
- [ ] FlowAnalyzer
- [ ] ResourceEstimator
- [ ] TimingPathExtractor
- [ ] PerformanceAnalyzer
- [ ] ThroughputEstimator
- [ ] SimPerformanceAnalyzer
- [ ] PowerEstimator
- [ ] Visualizer

### Phase 3 (Debug 分析器)
- [ ] CDCAnalyzer ⭐
- [ ] MultiDriverDetector ⭐
- [ ] ClockDomainAnalyzer
- [ ] ClockTreeAnalyzer
- [ ] ResetDomainAnalyzer
- [ ] DanglingPortDetector
- [ ] UninitializedDetector
- [ ] XValueAnalyzer
- [ ] RootCauseAnalyzer
- [ ] CoverageGenerator
- [ ] RiskCollector

### Phase 4 (Query 模块)
- [ ] OverflowRiskDetector ⭐
- [ ] ConditionRelationExtractor
- [ ] DataPathBoundaryAnalyzer
- [ ] NestedConditionExpander
- [ ] PathQuerier
- [ ] SignalQuerier
- [ ] StimulusPathFinder
- [ ] SampleConditionAnalyzer
- [ ] FuzzyPathMatcher

⭐ = 高优先级

---

## 八、验收标准

### 8.1 模块级验收

| 标准 | 描述 |
|------|------|
| 方法可调用 | 所有公共方法可正常调用 |
| 返回类型正确 | 返回值类型符合 API 文档 |
| 无异常退出 | 不抛出未捕获异常 |
| 结果合理 | 输出结果符合预期 |

### 8.2 项目级验收

| 标准 | 描述 |
|------|------|
| 解析成功 | 能解析对应项目的所有 .v/.sv 文件 |
| 结果非空 | 至少返回有意义的分析结果 |
| 性能达标 | 在规定时间内完成 |

### 8.3 覆盖率目标

| 类别 | 目标 |
|------|------|
| 核心模块覆盖 | 100% (18/18) |
| Debug 分析器覆盖 | > 80% (9/11) |
| Query 模块覆盖 | > 70% (6/9) |
| 测试项目覆盖 | 6/7 (XiangShan 可选) |

---

## 九、测试记录模板

```python
# test_[module]_[project].py
def test_[module]_[method]():
    """Test [Module].[method]()"""
    # Arrange
    parser = SVParser()
    parser.parse_file(TEST_FILE)
    
    # Act
    analyzer = [Module](parser)
    result = analyzer.[method]([params])
    
    # Assert
    assert result is not None
    assert isinstance(result, [ExpectedType])
    assert [specific_assertion]
```

---

## 十、提交记录

| Commit | 描述 |
|--------|------|
| `e5c108c` | docs: create TEST_PLAN_V2.md - comprehensive test plan |
| `48bd2c7` | docs: update TEST_PLAN.md - depth testing 100K stages |
| `29225f7` | test: verify ConnectionTracer with 6 projects |
| `17c2d5a` | feat: ConnectionTracer enhanced |
