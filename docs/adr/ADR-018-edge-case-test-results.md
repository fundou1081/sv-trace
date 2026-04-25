# ADR-018: 底层功能库边界测试结果

## 状态
**已接受** (Accepted)

## 决策者
方浩博

## 日期
2026-04-25

## 背景
在修复 DriverCollector 的 pyslang API 问题后，需要为底层功能库创建边界测试用例，确保每个库至少发现 3 个 bug。

## 决策
创建 `tests/edge_cases/` 目录，包含以下边界测试套件：
- `test_driver_edge.py` - DriverCollector 边界测试 (8 个用例)
- `test_load_edge.py` - LoadTracer 边界测试 (8 个用例)
- `test_dependency_edge.py` - DependencyAnalyzer 边界测试 (8 个用例)
- `test_debug_edge.py` - Debug Analyzers 边界测试 (8 个用例)
- `test_query_edge.py` - Query Modules 边界测试 (8 个用例)

## 结果
- 总计 40 个测试用例
- 通过 20 个 (52%)
- 发现 18 个待修复问题

### 通过的测试
- DriverCollector: 6/8 (75%)
- LoadTracer: 2/8 (25%)
- DependencyAnalyzer: 8/8 (100%) ✅
- Debug Analyzers: 4/8 (50%)
- Query Modules: 1/8 (12%)

## 关键发现

### 1. pyslang API 兼容性问题
- `thenStatement` → `statement`
- `elseStatement` → `elseClause.clause`
- `cases` → `items`
- `case.statement` → `case.clause`
- `Binary` → 具体表达式类型 (`AddExpression`, etc.)
- always_ff/always_latch 需要访问两层 `.statement`

### 2. 功能缺失
- 数组下标赋值/加载
- 位选择赋值/加载
- generate 块遍历
- 隐式 wire 检测
- 三元表达式处理

## 待修复问题 (按优先级)

### P0 - 立即修复
1. LoadTracer: 三元表达式加载
2. MultiDriverDetector: 隐式 wire 多驱动检测
3. DanglingPortDetector: 输出端口悬空检测

### P1 - 高优先级
4. LoadTracer: generate for 加载
5. ConditionRelationExtractor: 条件关系提取
6. DriverCollector: 数组下标赋值

### P2 - 中优先级
7. LoadTracer: 函数参数加载
8. LoadTracer: 多维数组加载
9. OverflowRiskDetector: 乘法/移位溢出

## 引用
- `docs/EDGE_CASE_RESULTS_V2.md` - 详细测试结果
- `tests/edge_cases/` - 边界测试套件
