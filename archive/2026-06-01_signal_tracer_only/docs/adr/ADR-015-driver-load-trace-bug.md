# ADR-015: Driver/Load/ControlFlow 追踪模块 Bug - 已全部修复

## 状态
**已修复** - 2026-04-24

## 问题描述

sv-trace 项目中的 DriverCollector、LoadTracer 和 ControlFlowTracer 模块无法正确收集信号信息。

## 根本原因

### pyslang AST 结构特点
1. **AlwaysBlock.statement = TimingControlStatement**
2. **TimingControlStatement.statement = body (SequentialBlockStatement)**
3. **SequentialBlockStatement.items = SyntaxList** (用 `items[i]` 访问，不是 `statements`)
4. **ExpressionStatement.expr = expression** (不是 `expression` 属性)
5. **SourceLocation 只有 offset 属性**，没有 `line`

### Driver/LoadTracer 问题
1. 使用 `str(node)` 无法获取完整 AST 信息
2. 使用错误的属性名 `statements`/`expression`
3. 使用不存在的 `sourceRange.start.line`

### ControlFlowTracer 问题
1. 枚举名称不匹配: `'ALWAYS_FF'` vs `'AlwaysFF'`
2. `Driver` 模型使用 `lines` (列表) 而不是 `line`

## 解决方案

### 1. DriverCollector 修复
- 使用 `pyslang.visit()` API 遍历 AST
- 使用 `items[i]` 访问 SequentialBlockStatement 子节点
- 使用 `expr` 而不是 `expression`
- 使用 `offset` 而不是 `line`

### 2. LoadTracer 修复
- 重写为使用 `pyslang.visit()` API
- 同样的属性名修复

### 3. ControlFlowTracer 修复
- 修复枚举名称: `'ALWAYS_FF'` → `'AlwaysFF'`
- 修复 driver.line → driver.lines[0]

## 修复后的测试结果

```
1. DriverCollector: 119 signals, 182 drivers ✅
   - Continuous: 87
   - AlwaysFF: 95

2. LoadTracer: 21 signals with loads ✅

3. ControlFlowTracer: controlling=1, conditions=1 ✅

4. DataPathAnalyzer: 214 nodes ✅

5. ConnectionTracer: 4 instances ✅
```

## 经验教训

1. **pyslang AST 结构与预期不同** - 需要仔细检查实际的属性名
2. **使用 `dir()` 和 `hasattr()` 检查** - 确保属性存在
3. **使用 `str(node.kind)` 比较** - 而不是直接比较 SyntaxKind 枚举
4. **使用 visit API** - 更可靠地遍历 AST

## 后续行动

- [x] 修复 DriverCollector
- [x] 修复 LoadTracer
- [x] 修复 ControlFlowTracer
- [ ] 更新单元测试

## 相关信息

- 相关 ADR: ADR-014 (pyslang limitations)
- 测试文件: `tests/test_driver.py`
- 源码: `src/trace/driver.py`, `src/trace/load.py`, `src/trace/controlflow.py`
