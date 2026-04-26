# SV-Trace TODO 列表

## 问题修复清单

### 🔴 高优先级 (P0) - 已完成

#### 1. ResetIntegrityChecker错误 ✅ 已修复
- **文件**: `src/debug/analyzers/reset_domain_analyzer.py`
- **问题**: 使用`check()`方法而非`analyze()`
- **修复**: 正确调用`checker.check()`

#### 2. CodeQualityScorer错误 ✅ 已修复
- **文件**: `src/debug/analyzers/code_quality_scorer.py`  
- **问题**: `analyze()`返回`Tuple[QualityScore, List[QualityIssue]]`
- **修复**: 使用tuple解包 `score, issues = coder.analyze()`

### 🟡 中优先级 (P1) - 已存在

#### 3. LoadTracer双重实现 ✅ 已验证
- **文件**: `src/trace/load.py`
- **状态**: LoadTracer和LoadTracerRegex并存
- **说明**: LoadTracerRegex更准确(6 vs 0 loads for clk)
- **建议**: 保留LoadTracerRegex作为主要实现

#### 4. 缓存机制 ✅ 已存在
- **文件**: `src/parse/parser.py` - GlobalParseCache类
- **状态**: 已实现
- **方法**: `GlobalParseCache.get_instance()`, `parse_file_cached()`

---

## 测试覆盖清单

### ✅ 已完成

| 功能模块 | 测试文件 | 测试场景数 |
|---------|---------|-----------|
| DriverCollector | test_driver_collector.sv | 16 |
| LoadTracer | test_load_tracer.sv | 18 |
| DependencyAnalyzer | test_dependency_analyzer.sv | 18 |
| FanoutAnalyzer | test_fanout_analyzer.sv | 15 |
| DataFlowTracer | test_dataflow_tracer.sv | 18 |
| ControlFlowTracer | test_controlflow_tracer.sv | 18 |
| ConnectionTracer | test_connection_tracer.sv | 18 |
| ClockTreeAnalyzer | test_clock_tree_analyzer.sv | 12 |
| TimedPathAnalyzer | test_timed_path_analyzer.sv | 12 |
| ConditionCoverageAnalyzer | test_condition_coverage.sv | 12 |

**总计**: 10个文件, 157个测试场景

---

## 版本历史

- v0.1: 初始版本
- v0.2: 测试用例扩展  
- v0.3: 问题修复 ✅

