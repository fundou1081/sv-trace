
# SV-TRACE 模块详细文档

---

## 1. trace.driver (DriverCollector)

### 用途
查找信号的所有驱动源,包括连续赋值、always_ff、always_comb等

### 输入
```python
parser = SVParser()
parser.parse_file('top.sv')
dc = DriverCollector(parser)
drivers = dc.find_driver('signal_name')
```

### 输出
```python
List[Driver]
Driver: signal, kind, module, sources, clock, reset, enable, lines
```

### 当前限制
- 仅支持基本always块类型
- 不支持generate语句内的驱动

### 测试状态 ✅
- test_driver.py: 8/8 passed
- 边界测试: PASS

---

## 2. trace.load (LoadTracer)

### 用途
查找信号的所有加载(读取)位置

### 输入
```python
lt = LoadTracer(parser)
loads = lt.find_load('signal_name')
```

### 输出
```python
List[Load]
Load: signal_name, context, line, module, statement_type, condition
```

### 当前限制
- 函数参数追踪需完善

### 测试状态 ✅
- test_driver.py: 8/8 passed  
- 边界测试: 8/8 PASS

---

## 3. trace.datapath (DataPathAnalyzer)

### 用途
分析信号的数据路径,包括组合逻辑链

### 输入
```python
analyzer = DataPathAnalyzer(parser)
result = analyzer.analyze('result_signal')
```

### 输出
```python
DataPath: nodes, chain, stages
DataPathNode: signal, drivers, exprs, driver_kinds
```

### 当前限制
- 不支持多时钟域

### 测试状态 ✅
- P1测试: PASS

---

## 4. trace.dependency (DependencyAnalyzer)

### 用途
分析信号的依赖关系,找出源信号和影响信号

### 输入
```python
analyzer = DependencyAnalyzer(parser)
result = analyzer.analyze('signal_name')
```

### 输出
```python
SignalDependency: depends_on, influences, source_signals, sink_signals
```

### 当前限制
- 仅支持单层依赖

### 测试状态 ✅
- P1测试: PASS

---

## 5. trace.connection (ConnectionTracer)

### 用途
追踪模块实例化和端口连接关系

### 输入
```python
tracer = ConnectionTracer(parser)
instances = tracer.get_all_instances()
```

### 输出
```python
List[Instance]
Instance: module, name, ports, connections
```

### 当前限制
- 不支持参数化模块

### 测试状态 ✅
- test_hierarchy.py: PASS

---

## 6. trace.controlflow (ControlFlowTracer)

### 用途
分析信号的控制流依赖(if/case/while等)

### 输入
```python
cf = ControlFlowTracer(parser)
result = cf.find_control_dependencies('signal')
```

### 输出
```python
ControlFlow: conditions, controlling_signals
```

### 当前限制
- 不支持多分支嵌套

### 测试状态 ✅
- test_control_dependency.py: PASS

---

## 7. trace.dataflow (DataFlowTracer)

### 用途
追踪数据流,构建数据流图

### 输入
```python
tracer = DataFlowTracer(parser)
result = tracer.find_flow('signal_name')
```

### 输出
```python
DataFlow: (需确认具体结构)
```

### 当前限制
- 需更多测试验证

### 测试状态 ✅
- P2测试: PASS

---

## 8. trace.bitselect (BitSelectTracer)

### 用途
分析位选择操作 (data[3], data[7:0]等)

### 输入
```python
tracer = BitSelectTracer(parser)
result = tracer.find_bit_drivers('data')
```

### 输出
```python
List[Tuple[str, BitSelect]]
```

### 当前限制
- 仅支持静态位选择

### 测试状态 ✅
- P2测试: PASS

---

## 9. trace.pipeline_analyzer (PipelineAnalyzer)

### 用途
检测流水线阶段和寄存器

### 输入
```python
analyzer = PipelineAnalyzer(parser)
result = analyzer.analyze()
```

### 输出
```python
PipelineInfo: stages, registers
```

### 当前限制
- 仅支持简单流水线

### 测试状态 ✅
- P1测试: PASS

---

## 10. trace.timing_depth (TimingDepthAnalyzer)

### 用途
计算信号的时序深度(寄存器级数)

### 输入
```python
analyzer = TimingDepthAnalyzer(parser)
result = analyzer.analyze()
```

### 输出
```python
list of timing domains
```

### 当前限制
- 不支持异步逻辑

### 测试状态 ✅
- P1测试: PASS

---

## 11. trace.flow_analyzer (SignalFlowAnalyzer)

### 用途
统一信号流分析,整合多个模块

### 输入
```python
analyzer = SignalFlowAnalyzer(parser)
result = analyzer.analyze('signal')
```

### 输出
```python
SignalFlow: (结构需确认)
```

### 当前限制
- API需完善

### 测试状态 ✅
- P2测试: PASS

---

## 12. trace.visualize (GraphVisualizer)

### 用途
生成DOT格式的流程图

### 输入
```python
viz = GraphVisualizer()
viz.add_node(...)
dot = viz.to_dot('graph_name')
```

### 输出
```python
str: DOT format graph
```

### 当前限制
- 样式选项有限

### 测试状态 ✅
- P2测试: PASS

---

## 13. query.signal (SignalQuery)

### 用途
查询信号的基本信息

### 输入
```python
querier = SignalQuery(parser)
result = querier.find_signal('signal_name')
```

### 输出
```python
Signal: name, width, is_reg, is_wire, is_input, is_output, module
```

### 当前限制
- 不支持层级信号

### 测试状态 ✅
- P1测试: PASS

---

## 14. query.condition_relation_extractor (ConditionRelationExtractor)

### 用途
提取case/if条件关系,检测互斥条件

### 输入
```python
extractor = ConditionRelationExtractor(parser)
result = extractor.extract('signal')
```

### 输出
```python
ConditionRelation: target_signal, conditions, cross_bins
```

### 当前限制
- 不支持复杂嵌套

### 测试状态 ✅
- 边界测试: PASS (38/38)

---

## 15. query.overflow_risk_detector (OverflowRiskDetector)

### 用途
检测溢出风险(加法/乘法/移位)

### 输入
```python
detector = OverflowRiskDetector(parser)
result = detector.detect()
```

### 输出
```python
OverflowResult: risks (List[OverflowRisk])
OverflowRisk: signal, expression, risk_level, description, suggestion
```

### 当前限制
- 不支持定宽溢出

### 测试状态 ✅
- 边界测试: PASS

---

## 16. debug.class_extractor

### 用途
提取类信息(用于SystemVerilog面向对象)

### 输入
```python
extractor = ClassExtractor()
```

### 输出
```python
Class info structure
```

### 当前限制
- 需更多测试

### 测试状态 ✅
- 导入测试: PASS

---

## 17. debug.complexity (CyclomaticComplexityAnalyzer)

### 用途
计算圈复杂度

### 输入
```python
analyzer = CyclomaticComplexityAnalyzer()
```

### 输出
```python
ComplexityResult
```

### 当前限制
- 需更多验证

### 测试状态 ✅
- 导入测试: PASS

---

## 18. trace.resource_estimation (ResourceEstimation)

### 用途
估算LUT/FF等资源使用

### 输入
```python
est = ResourceEstimation(parser)
result = est.analyze_module('module_name')
```

### 输出
```python
ModuleResource: lut_count, ff_count, dsp_count, reg_bits
```

### 当前限制
- 估算精度有限

### 测试状态 ✅
- P3测试: PASS

---

## 19. trace.performance (PerformanceEstimator)

### 用途
估算时序性能

### 输入
```python
est = PerformanceEstimator(parser)
result = est.analyze()
```

### 输出
```python
PerformanceReport
```

### 当前限制
- 仅基础估算

### 测试状态 ✅
- P3测试: PASS

---

