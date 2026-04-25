# SV-TRACE 模块汇总

## Trace 模块

- **driver_collector** (`DriverCollector`): Find signal drivers
- **load** (`LoadTracer`): Find signal loads
- **datapath** (`DataPathAnalyzer`): Analyze data path
- **dependency** (`DependencyAnalyzer`): Analyze signal dependencies
- **connection** (`ConnectionTracer`): Trace module connections
- **controlflow** (`ControlFlowTracer`): Analyze control flow
- **dataflow** (`DataFlowTracer`): Trace data flow
- **bitselect** (`BitSelectTracer`): Trace bit-select operations
- **pipeline_analyzer** (`PipelineAnalyzer`): Detect pipeline stages
- **timing_depth** (`TimingDepthAnalyzer`): Calculate timing depth
- **flow_analyzer** (`SignalFlowAnalyzer`): Analyze signal flow
- **visualize** (`GraphVisualizer`): Generate DOT graphs
- **resource_estimation** (`ResourceEstimation`): Estimate LUT/FF usage
- **performance** (`PerformanceEstimator`): Estimate performance

## Query 模块

- **signal** (`SignalQuery`): Query signal information
- **path** (`PathQuerier`): Query signal paths
- **condition_relation_extractor** (`ConditionRelationExtractor`): Extract condition relations
- **overflow_risk_detector** (`OverflowRiskDetector`): Detect overflow risks

## Debug 模块

- **class_extractor** (`ClassExtractor`): Extract class information
- **class_hierarchy** (`ClassHierarchy`): Build class hierarchy
- **class_info** (`ClassInfo`): Gather class info
- **class_usage** (`ClassUsage`): Analyze class usage
- **complexity** (`CyclomaticComplexityAnalyzer`): Calculate cyclomatic complexity

---

总计: 23 modules