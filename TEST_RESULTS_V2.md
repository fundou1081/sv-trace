# SV-Trace 测试结果 V2

## 测试时间
2026-04-24

---

## 一、Phase 2 测试结果 (核心 trace 模块)

### 已验证模块 (11/18)

| # | 模块 | 类名 | 方法 | 状态 | 备注 |
|---|------|------|------|------|------|
| 1 | DriverCollector | DriverCollector | get_drivers() | ✅ PASS | signals:119, drivers:182 |
| 2 | LoadTracer | LoadTracer | find_load() | ✅ PASS | 方法正常 |
| 3 | ControlFlowTracer | ControlFlowTracer | find_control_dependencies() | ✅ PASS | 方法正常 |
| 4 | DataPathAnalyzer | DataPathAnalyzer | analyze() | ✅ PASS | datapaths:10 |
| 5 | ConnectionTracer | ConnectionTracer | get_all_instances() | ✅ PASS | instances:3, 深度100K+ |
| 6 | BitSelectTracer | BitSelectTracer | trace_bit_drivers() | ✅ PASS | 方法: trace_bit_drivers, find_bit_loads, get_driven_bits |
| 7 | SignalFlowAnalyzer | SignalFlowAnalyzer | analyze() | ✅ PASS | 方法: analyze, visualize |
| 8 | PipelineAnalyzer | PipelineAnalyzer | analyze() | ✅ PASS | 方法: analyze, analyze_signal |
| 9 | TimingDepthAnalyzer | TimingDepthAnalyzer | analyze() | ✅ PASS | 方法: analyze, find_critical_path, find_worst_logic_path |
| 10 | TimingPathExtractor | TimingPathExtractor | analyze() | ✅ PASS | 方法: analyze |
| 11 | PowerEstimator | PowerEstimator | estimate() | ✅ PASS | 方法: estimate |

### 待确认/有问题的模块 (7/18)

| # | 模块 | 类名 | 问题 | 状态 |
|---|------|------|------|------|
| 12 | DependencyAnalyzer | DependencyAnalyzer | TypeError: driver.sources is list, not string | ❌ FAIL |
| 13 | DataFlowTracer | DataFlowTracer | 需进一步验证方法调用 | ⚠️ PARTIAL |
| 14 | ResourceEstimator | ResourceEstimation | 方法: analyze_module | ⚠️ 待调用验证 |
| 15 | PerformanceEstimator | PerformanceEstimator | 方法: analyze | ⚠️ 待调用验证 |
| 16 | ThroughputEstimator | ThroughputEstimation | 方法: analyze | ⚠️ 待调用验证 |
| 17 | SimPerformanceEstimator | SimulationPerformance | 方法: analyze, estimate_cycles_for_duration | ⚠️ 待调用验证 |
| 18 | Visualizer | GraphVisualizer | TypeError: __init__() takes 1 positional argument | ❌ FAIL |

---

## 二、Phase 3 测试结果 (Debug 分析器)

### 已验证模块 (7/11)

| # | 模块 | 类名 | 方法 | 状态 | 备注 |
|---|------|------|------|------|------|
| 1 | CDCAnalyzer | CDCAnalyzer | detect_issues() | ✅ PASS | 返回 Report |
| 2 | ClockDomainAnalyzer | ClockDomainAnalyzer | get_all_domains() | ✅ PASS | 方法正常 |
| 3 | ClockTreeAnalyzer | ClockTreeAnalyzer | get_all_domains() | ✅ PASS | 方法正常 |
| 4 | ResetDomainAnalyzer | ResetDomainAnalyzer | get_reset_domains() | ✅ PASS | 方法正常 |
| 5 | RiskCollector | RiskCollector | collect() | ✅ PASS | 方法正常 |
| 6 | CoverageGenerator | CoverageGenerator | generate() | ✅ PASS | 方法正常 |

### 有问题的模块 (5/11)

| # | 模块 | 类名 | 问题 | 状态 |
|---|------|------|------|------|
| 7 | MultiDriverDetector | MultiDriverDetector | detect() requires 'signal' argument | ⚠️ 需参数 |
| 8 | DanglingPortDetector | DanglingPortDetector | detect() requires 'module_name' argument | ⚠️ 需参数 |
| 9 | UninitializedDetector | UninitializedDetector | detect() requires 'signal' argument | ⚠️ 需参数 |
| 10 | XValueDetector | XValueDetector | Wrong class name (was XValueAnalyzer) | ❌ FAIL |
| 11 | RootCauseAnalyzer | RootCauseAnalyzer | analyze() requires 'symptom' and 'module' arguments | ⚠️ 需参数 |

---

## 三、Phase 4 测试结果 (Query 模块)

### 已验证模块 (4/9)

| # | 模块 | 类名 | 方法 | 状态 | 备注 |
|---|------|------|------|------|------|
| 1 | FuzzyPathMatcher | FuzzyPathMatcher | match() | ✅ PASS | 返回 None |
| 2 | NestedConditionExpander | NestedConditionExpander | expand() | ✅ PASS | 返回 None |
| 3 | StimulusPathFinder | StimulusPathFinder | find() | ✅ PASS | 返回 None |

### 有问题的模块 (5/9)

| # | 模块 | 类名 | 问题 | 状态 |
|---|------|------|------|------|
| 4 | ConditionRelationExtractor | ConditionRelationExtractor | extract() requires 'signal' argument | ⚠️ 需参数 |
| 5 | DataPathBoundaryAnalyzer | DataPathBoundaryAnalyzer | analyze() requires 'signal' argument | ⚠️ 需参数 |
| 6 | OverflowRiskDetector | OverflowRiskDetector | re.error: invalid group reference | ❌ FAIL |
| 7 | PathQuerier | PathQuerier | Class name wrong, check module | ❌ FAIL |
| 8 | SampleConditionAnalyzer | SampleConditionAnalyzer | analyze() requires 'signal' argument | ⚠️ 需参数 |
| 9 | SignalQuerier | SignalQuerier | Class name wrong, check module | ❌ FAIL |

---

## 四、详细错误记录

### 4.1 DependencyAnalyzer - driver.sources 类型错误

**错误信息:**
```
TypeError: expected string or bytes-like object, got 'list'
```

**位置:** `src/trace/dependency.py:144`

**原因:** `_extract_signals()` 方法期望 `driver.sources` 是字符串，但实际是列表

**触发代码:**
```python
def _find_forward_dependencies(self, signal_name, module_name):
    ...
    signals = self._extract_signals(driver.sources)  # driver.sources is list
    ...

def _extract_signals(self, expr):
    for match in re.finditer(pattern, expr):  # expr is list, not string
```

**建议修复:** 在 `_extract_signals()` 入口处理列表情况

---

### 4.2 Visualizer - __init__ 参数错误

**错误信息:**
```
TypeError: GraphVisualizer.__init__() takes 1 positional argument but 2
```

**原因:** GraphVisualizer 的 __init__ 不接受 parser 参数

---

### 4.3 OverflowRiskDetector - 正则表达式错误

**错误信息:**
```
re.error: invalid group reference 1 at position 1
```

**位置:** `src/query/overflow_risk_detector.py:116`

**代码:**
```python
if re.search(r'\1\s*\+\s*1\b', expr) and 'if' not in expr:
```

**原因:** 反向引用 `\1` 在没有对应捕获组时使用

---

### 4.4 XValueDetector - 类名错误

**错误:** 测试代码使用 `XValueAnalyzer`，但实际类名是 `XValueDetector`

---

## 五、测试覆盖率汇总

| Phase | 模块总数 | 通过 | 失败 | 待确认 | 覆盖率 |
|-------|---------|------|------|--------|-------|
| Phase 1 (核心) | 5 | 5 | 0 | 0 | 100% |
| Phase 2 (核心) | 13 | 6 | 2 | 5 | 46% |
| Phase 3 (Debug) | 11 | 6 | 1 | 4 | 55% |
| Phase 4 (Query) | 9 | 3 | 3 | 2 | 33% |
| **总计** | **38** | **20** | **6** | **11** | **53%** |

---

## 六、下一步行动计划

### 立即修复 (P0)
1. **DependencyAnalyzer** - 修复 driver.sources 类型问题
2. **OverflowRiskDetector** - 修复正则表达式
3. **Visualizer** - 检查 GraphVisualizer 初始化

### 完善测试 (P1)
1. 为需要参数的方法编写完整测试用例
2. 验证 ResourceEstimator, PerformanceEstimator 等的 analyze_module() 方法
3. 修正类名错误 (XValueDetector)

### 待调查 (P2)
1. PathQuerier 和 SignalQuerier 的正确类名
2. Debug 分析器的 detect() 方法参数规范
