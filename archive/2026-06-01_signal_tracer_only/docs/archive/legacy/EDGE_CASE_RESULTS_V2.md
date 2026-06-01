# SV-Trace 边界测试结果 V2

## 测试时间
2026-04-25 08:35

## 测试概述
为底层功能库创建边界测试用例，每个库至少 8 个测试场景。

## 测试结果汇总

| 模块 | 通过 | 失败 | 通过率 |
|------|------|------|--------|
| DriverCollector | 6 | 2 | 75% |
| LoadTracer | 2 | 6 | 25% |
| DependencyAnalyzer | 8 | 0 | 100% |
| Debug Analyzers | 7 | 1 | 87% |
| Query Modules | 1 | 7 | 12% |
| **总计** | **23** | **15** | **60%** |

---

## 修复记录

### 2026-04-25 修复 (v0.3.1)

#### 已修复 (8个问题)
1. ✅ LoadTracer: If statement 属性 (thenStatement→statement)
2. ✅ LoadTracer: Case statement 属性 (cases→items)
3. ✅ LoadTracer: always_ff/always_latch 处理
4. ✅ LoadTracer: Binary expression 匹配 (.endswith('Expression'))
5. ✅ LoadTracer: ConditionalExpression 属性 (before Binary)
6. ✅ MultiDriverDetector: 隐式 wire 多驱动检测
7. ✅ DanglingPortDetector: 端口提取修复 (PortDeclaration)
8. ✅ DanglingPortDetector: 输出端口悬空检测

#### 待修复 (15个问题)

| 序号 | 模块 | 问题 | 状态 |
|------|------|------|------|
| 1 | DriverCollector | 数组下标赋值 | ❌ |
| 2 | DriverCollector | 位选择赋值 | ❌ |
| 3 | LoadTracer | 多维数组加载 | ❌ |
| 4 | LoadTracer | 嵌套表达式加载 | ❌ |
| 5 | LoadTracer | generate for 加载 | ❌ |
| 6 | LoadTracer | 函数参数加载 | ❌ |
| 7 | LoadTracer | 位选择加载 | ❌ |
| 8 | UninitializedDetector | 数组未初始化检测 | ❌ |
| 9 | OverflowRiskDetector | 乘法溢出检测 | ❌ |
| 10 | OverflowRiskDetector | 移位溢出检测 | ❌ |
| 11 | OverflowRiskDetector | 有边界加法检测 | ❌ |
| 12 | ConditionRelationExtractor | 互斥条件提取 | ❌ |
| 13 | ConditionRelationExtractor | 嵌套条件提取 | ❌ |
| 14 | ConditionRelationExtractor | 优先级条件提取 | ❌ |
| 15 | SignalQuery | 信号查询 | ❌ |

---

## 版本历史

| 版本 | 日期 | 描述 |
|------|------|------|
| V1 | 2026-04-24 | 初始边界测试结果 |
| V2 | 2026-04-25 | 底层功能库边界测试 - 60% 通过 |
