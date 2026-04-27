# SV-Trace Bug Fix Plan

## 来源

测试计划: [tests/TEST_PLAN_V2.md](tests/TEST_PLAN_V2.md)
测试结果: [tests/TEST_RESULTS_V2.md](tests/TEST_RESULTS_V2.md)

---

## Phase 2: 未修复Bug (5个)

| # | 模块 | 问题 | 原因 |
|---|------|------|------|
| 1 | XValueDetector | WrongClassNameAssertion | class名错误 |
| 2 | XValueDetector | get_is_sequential() fail | 方法缺失 |
| 3 | DependencyAnalyzer | driver.sources失败 | TypeError |
| 4 | GraphVisualizer | __init__参数错误 | 初始化参数 |
| 5 | FSMAnalyzer | 方法缺失 | - |

---

## Phase 3: Debug分析器Bug

| # | 模块 | 问题 |
|---|------|------|
| 1 | ClassAnalyzer | 需要完善 |
| 2 | ConstraintAnalyzer | - |
| 3 | AssertionAnalyzer | - |

---

## Phase 4: Query分析器Bug

| # | 模块 | 问题 |
|---|------|------|
| 1 | FlowAnalyzer | - |
| 2 | PathFinder | - |

---

## 建议修复顺序

### P0: 立即修复
1. **XValueDetector** - 类名错误导致无法导入
2. **GraphVisualizer** - __init__参数错误

### P1: 重要
3. **DependencyAnalyzer** - driver.sources TypeError
4. **FSMAnalyzer** - 方法缺失

### P2: 次要
5. Debug分析器完善
6. Query分析器完善

---

## 验证方法

修复后运行:
```bash
python -m pytest tests/unit/ -v
```

目标: 通过率 > 90%
