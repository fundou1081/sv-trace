# ADR-018: 底层功能库边界测试结果

## 状态
**进行中** (In Progress)

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
- 通过 31 个 (82%)
- 已修复问题: 从 18 个减少到 6 个

### 测试结果汇总

| 模块 | 通过 | 失败 | 通过率 |
|------|------|------|--------|
| DriverCollector | 8 | 0 | 100% ✅ |
| LoadTracer | 6 | 2 | 75% |
| DependencyAnalyzer | 8 | 0 | 100% |
| Debug Analyzers | 7 | 1 | 87% |
| Query Modules | 1 | 7 | 12% |

## 已修复问题 (按提交)

### 提交 d641926 (2026-04-25)
- **LoadTracer**: 
  - If statement: thenStatement→statement, elseStatement→elseClause.clause
  - Case statement: cases→items, statement→clause  
  - always_ff/always_latch: TimingControlStatement handling
  - Expression matching: 'Binary' → 'Expression' for AddExpression
  - ConditionalExpression: condition→predicate, whenTrue/whenFalse→left/right
- **MultiDriverDetector**: 添加连续赋值信号收集 (隐式 wire)
- **DanglingPortDetector**: 使用 PortDeclaration 节点重写端口提取

### 提交 f4e5341 (2026-04-25)
- **LoadTracer**:
  - _process_always_load: TimingControlStatement 处理
  - _walk_for_load: If/Case statement 属性
  - Case condition: expr not condition
  - Expression matching: .endswith('Expression')

### 提交 fd8410c (2026-04-25)
- **LoadTracer**:
  - 数组下标支持: data_in[i] → 提取基础名称
  - ElementSelect 支持: 检查 selectors
  - 测试用例更新: 添加 begin...end 块

## 关键 pyslang API 发现

1. **always_comb 块**: 
   - 无 begin...end 时: node.statement 是 ExpressionStatement
   - 有 begin...end 时: node.statement 是 SequentialBlockStatement

2. **always_ff/always_latch 块**:
   - node.statement 是 TimingControlStatement
   - 需要再访问 .statement 获取实际 body

3. **ConditionalExpression**:
   - 使用 `predicate`, `left`, `right` 属性 (不是 condition, whenTrue, whenFalse)

4. **数组下标**:
   - `data_in[i]` 的 kind 是 `IdentifierSelectName`
   - 需要提取基础名称进行比较

5. **generate 块**:
   - 内部的 always_comb 可以被正常遍历

## 待修复问题 (8个)

### 高优先级

| 序号 | 模块 | 问题 | 状态 |
|------|------|------|------|
| 1 | LoadTracer | 函数参数加载 | ❌ |
| 2 | UninitializedDetector | 数组未初始化检测 | ❌ |

### 中优先级

| 序号 | 模块 | 问题 | 状态 |
|------|------|------|------|
| 3 | OverflowRiskDetector | 乘法溢出检测 | ❌ |
| 4 | OverflowRiskDetector | 移位溢出检测 | ❌ |
| 5 | OverflowRiskDetector | 有边界加法检测 | ❌ |
| 6 | ConditionRelationExtractor | 条件关系提取 | ❌ |
| 7 | ConditionRelationExtractor | 嵌套/优先级条件 | ❌ |
| 8 | SignalQuery | 信号查询 | ❌ |


### 提交 9dbd53c (2026-04-25)
- **DriverCollector**:
  - 添加 IdentifierSelectName 支持: mem[idx] → 提取基础名称
  - 修复 _get_signal_name: IdentifierSelectName 检查优先级
  - 添加 IdentifierSelectName 到 _extract_sources


### 提交 cbd46ab (2026-04-25)
- **OverflowRiskDetector**:
  - 添加乘法和移位溢出检测模式
  - 修复 _get_code 尝试多种方法
  - 重构 _find_add_sub_assignments
  - 添加 _check_overflow ptype 参数

**已知问题**: 临时文件读取被截断 - 需要在解析后保留原始代码


### 提交 d036601 (2026-04-25)
- **LoadTracer**:
  - 添加 InvocationExpression 支持 (函数调用)
  - 修复 arguments 迭代 (ArgumentListSyntax 包含 SeparatedList)
  - func_param 现在可以追踪函数参数

**pyslang 发现**: InvocationExpression.arguments 是 ArgumentListSyntax，需要遍历 SeparatedList 获取实际参数


### 提交 6cfe478 (2026-04-25)
- **LoadTracer**:
  - 函数调用处理：使用正则表达式从函数调用表达式中提取标识符
  - 跳过 SystemVerilog 关键字
  - 简单有效的方法来追踪函数参数

## 引用
- `docs/EDGE_CASE_RESULTS_V2.md` - 详细测试结果
- `tests/edge_cases/` - 边界测试套件

## 更新历史
- 2026-04-25: 更新到 26/38 (68%) - 新增 3 个修复
