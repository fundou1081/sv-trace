# SV-Trace 边界测试结果 V2

## 测试时间
2026-04-25 08:30

## 测试概述
为底层功能库创建边界测试用例，每个库至少 8 个测试场景。

## 测试结果汇总

| 模块 | 通过 | 失败 | 通过率 |
|------|------|------|--------|
| DriverCollector | 6 | 2 | 75% |
| LoadTracer | 2 | 6 | 25% |
| DependencyAnalyzer | 8 | 0 | 100% |
| Debug Analyzers | 4 | 4 | 50% |
| Query Modules | 1 | 7 | 12% |
| **总计** | **20** | **18** | **52%** |

---

## 详细测试结果

### 1. DriverCollector (6/8 通过)

| # | 测试用例 | 描述 | 状态 | 结果 |
|---|---------|------|------|------|
| 1 | array_index_assign | 连续赋值中的数组下标 | ❌ 失败 | 0 drivers |
| 2 | gen_if | generate if 中的驱动 | ✅ 通过 | 4 drivers |
| 3 | multi_always | 多个 always 块驱动同一信号 | ✅ 通过 | 2 drivers |
| 4 | func_call | 函数调用中的驱动 | ✅ 通过 | 2 drivers |
| 5 | bit_select | 位选择赋值 | ❌ 失败 | 0 drivers |
| 6 | blocking_ff | 阻塞赋值在 always_ff 中 | ✅ 通过 | 2 drivers |
| 7 | implicit_port | 隐式端口连接 | ✅ 通过 | 2 drivers |
| 8 | ifdef | 条件编译中的驱动 | ✅ 通过 | 2 drivers |

**未通过原因分析:**
- **array_index_assign**: 未处理 `mem[idx] = data` 形式的数组元素赋值
- **bit_select**: 未处理 `data[idx] = bit_val` 形式的位选择赋值

### 2. LoadTracer (2/8 通过)

| # | 测试用例 | 描述 | 状态 | 结果 |
|---|---------|------|------|------|
| 1 | multi_dim_array | 多维数组的加载 | ❌ 失败 | 0 loads |
| 2 | nested_expr | 嵌套表达式中的加载 | ❌ 失败 | 0 loads |
| 3 | for_loop | for 循环中的加载 | ✅ 通过 | 1 load |
| 4 | ternary | 三元表达式中的加载 | ❌ 失败 | 0 loads |
| 5 | gen_for | generate for 中的加载 | ❌ 失败 | 0 loads |
| 6 | func_param | 函数参数中的加载 | ❌ 失败 | 0 loads |
| 7 | repeated_signal | 重复信号在右侧 | ✅ 通过 | 3 loads |
| 8 | bit_select_load | 位选择作为加载 | ❌ 失败 | 0 loads |

**未通过原因分析:**
- **multi_dim_array**: 多维数组下标未处理 (mem[i][j])
- **nested_expr**: 表达式递归检查可能不完整
- **ternary**: 三元表达式 (conditional) 解析问题
- **gen_for**: generate for 块未遍历
- **func_param**: 函数参数未递归检查
- **bit_select_load**: 位选择 (ElementSelect) 未处理

### 3. DependencyAnalyzer (8/8 通过)

| # | 测试用例 | 描述 | 状态 | 结果 |
|---|---------|------|------|------|
| 1 | simple_chain | 简单依赖链 | ✅ 通过 | 1 |
| 2 | multi_layer | 多层依赖 | ✅ 通过 | 1 |
| 3 | conditional | 条件依赖 | ✅ 通过 | 1 |
| 4 | array_dep | 数组依赖 | ✅ 通过 | 1 |
| 5 | ternary | 三元表达式依赖 | ✅ 通过 | 1 |
| 6 | for_loop | for 循环依赖 | ✅ 通过 | 1 |
| 7 | function | 函数依赖 | ✅ 通过 | 1 |
| 8 | cross_module | 跨模块依赖 | ✅ 通过 | 1 |

**状态**: 全部通过 ✅

### 4. Debug Analyzers (4/8 通过)

| # | 测试用例 | 描述 | 状态 | 结果 |
|---|---------|------|------|------|
| 1 | multi_driver_implicit | wire 隐式声明的多驱动 | ❌ 失败 | 0 |
| 2 | multi_driver_gen | generate 块中的多驱动 | ✅ 通过 | 1 |
| 3 | uninit_array | 数组寄存器未初始化 | ❌ 失败 | 0 |
| 4 | uninit_async_rst | 异步复位时未初始化 | ✅ 通过 | 1 |
| 5 | xval_casez | casez 通配符导致的 X | ✅ 通过 | 2 |
| 6 | xval_full_case | full_case 未使用导致的 X | ✅ 通过 | 2 |
| 7 | dangling_output | 输出端口被连续赋值但未使用 | ❌ 失败 | 0 |
| 8 | dangling_instance | 模块实例化时未连接的输出 | ❌ 失败 | 0 |

**未通过原因分析:**
- **multi_driver_implicit**: MultiDriverDetector 仅扫描 DataDeclaration，未检测隐式 wire
- **uninit_array**: 未处理数组类型的未初始化检测
- **dangling_output**: DanglingPortDetector 检测逻辑问题
- **dangling_instance**: 实例化时的悬空端口检测不完整

### 5. Query Modules (1/8 通过)

| # | 测试用例 | 描述 | 状态 | 结果 |
|---|---------|------|------|------|
| 1 | overflow_counter | 饱和计数器 | ✅ 通过 | 1 risk |
| 2 | overflow_checked | 有边界的加法 | ❌ 失败 | 0 |
| 3 | cond_mutual_exclusive | 互斥条件 | ❌ 失败 | 0 |
| 4 | cond_nested | 嵌套条件 | ❌ 失败 | 0 |
| 5 | signal_query | 查找信号 | ❌ 失败 | 0 |
| 6 | overflow_mult | 乘法溢出 | ❌ 失败 | 0 |
| 7 | cond_priority | 优先级条件 | ❌ 失败 | 0 |
| 8 | overflow_shift | 移位溢出 | ❌ 失败 | 0 |

**未通过原因分析:**
- **overflow_checked**: 检测器无法识别带有溢出标志的加法
- **cond_mutual_exclusive**: ConditionRelationExtractor 返回结果为空
- **cond_nested**: 嵌套条件提取失败
- **signal_query**: SignalQuery.find_signal() 可能存在问题
- **overflow_mult**: 未检测乘法溢出风险
- **cond_priority**: 优先级条件提取失败
- **overflow_shift**: 未检测移位溢出风险

---

## 待修复问题清单

### 高优先级 (影响功能正确性)

| 序号 | 模块 | 问题 | 严重程度 |
|------|------|------|----------|
| 1 | DriverCollector | 数组下标赋值不支持 | 中 |
| 2 | DriverCollector | 位选择赋值不支持 | 中 |
| 3 | LoadTracer | 三元表达式加载不支持 | 高 |
| 4 | LoadTracer | generate for 加载不支持 | 高 |
| 5 | LoadTracer | 函数参数加载不支持 | 中 |
| 6 | MultiDriverDetector | 隐式 wire 多驱动检测 | 高 |
| 7 | DanglingPortDetector | 输出端口悬空检测 | 高 |
| 8 | ConditionRelationExtractor | 条件关系提取失败 | 高 |

### 中优先级 (边界情况)

| 序号 | 模块 | 问题 | 严重程度 |
|------|------|------|----------|
| 9 | LoadTracer | 多维数组加载 | 中 |
| 10 | LoadTracer | 嵌套表达式加载 | 中 |
| 11 | LoadTracer | 位选择加载 | 中 |
| 12 | UninitializedDetector | 数组未初始化检测 | 中 |
| 13 | OverflowRiskDetector | 乘法溢出检测 | 中 |
| 14 | OverflowRiskDetector | 移位溢出检测 | 中 |
| 15 | SignalQuery | 信号查询失败 | 中 |

### 低优先级 (改进)

| 序号 | 模块 | 问题 | 严重程度 |
|------|------|------|----------|
| 16 | OverflowRiskDetector | 有边界加法检测 | 低 |
| 17 | ConditionRelationExtractor | 嵌套条件提取 | 低 |
| 18 | ConditionRelationExtractor | 优先级条件提取 | 低 |

---

## 修复建议

1. **DriverCollector**: 添加 ElementSelect 和 ArrayIndex 表达式的处理
2. **LoadTracer**: 
   - 完善 ConditionalExpression 处理
   - 添加 generate 块遍历
   - 完善函数参数递归检查
3. **MultiDriverDetector**: 扩展信号扫描范围，包含连续赋值推断的信号
4. **DanglingPortDetector**: 修复输出端口悬空检测逻辑
5. **ConditionRelationExtractor**: 调试返回结果为空的问题
6. **OverflowRiskDetector**: 添加乘法和移位操作的溢出检测

---

## 版本历史

| 版本 | 日期 | 描述 |
|------|------|------|
| V1 | 2026-04-24 | 初始边界测试结果 |
| V2 | 2026-04-25 | 新增底层功能库边界测试 |
