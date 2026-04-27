# Constraint Parser V2 架构文档

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V1 | 2024 | 基于字符串解析，简单实现 |
| **V2** | **2026-04-27** | **pyslang + z3 重大升级** |

## V2 架构

### 核心组件

```
┌─────────────────────────────────────────────┐
│         SVParser (pyslang)                  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│       ConstraintParserV2                   │
├─────────────────────────────────────────────┤
│  解析层:                                    │
│  - _extract_classes()                      │
│  - _extract_constraints()                  │
│  - _parse_constraint_declaration()        │
│  - _parse_constraint_item()                │
│                                             │
│  分析层:                                   │
│  - _analyze_dependencies()                 │
│  - _analyze_inheritance_dependencies()      │
│                                             │
│  检测层:                                    │
│  - ConflictDetector (z3-based)            │
│  - LowProbabilityAnalyzer                  │
└─────────────────────────────────────────────┘
```

### 类图

```
ConstraintVariable
    │
    └─ name, is_rand, line_number

ConstraintDetail
    ├─ 基础: name, class_name, constraint_type
    ├─ 变量: variables[], external_refs[]
    ├─ 条件: condition, then_expr, else_expr
    ├─ 循环: loop_var, loop_iterable
    ├─ 分布: dist_items[]
    ├─ 解题: before_vars, after_vars
    └─ 元数据: line_number, is_soft, parent_class

ConstraintDependency
    ├─ from_constraint
    ├─ to_constraint
    ├─ via_variable
    └─ dependency_type

ConflictDetector (Z3)
    ├─ _detect_unsatisfiable()
    ├─ _detect_cyclic()
    └─ get_conflicts()
```

### 方法列表

| 方法 | 功能 |
|------|------|
| **解析** | |
| get_all_constraints() | 获取所有约束 |
| get_class_constraints(cls) | 获取class的约束 |
| **分析** | |
| get_report() | 生成报告 |
| find_overridden_constraints() | 查找覆盖约束 |
| find_variable_in_constraints(var) | 查找变量约束 |
| get_constraint_type_summary() | 类型统计 |
| get_inheritance_chain(cls) | 继承链 |
| get_cross_class_references(cls) | 跨类引用 |
| **可视化** | |
| visualize_relationships() | 变量-约束-Class图 |
| visualize_dependency_graph() | 依赖图 |
| visualize_constraint_interaction() | 交互图 |
| **检测** | |
| detect_conflicts() | 冲突检测(z3) |

## 支持的 Constraint 类型

| 类型 | 示例 | 解析器标识 |
|------|------|-----------|
| simple | `x > 0` | ExpressionConstraintSyntax |
| soft | `soft x > 5` | ExpressionConstraintSyntax (soft) |
| conditional | `if (x > 10) x < 100` | ConditionalConstraintSyntax |
| implication | `valid -> data > 0` | ImplicationConstraintSyntax |
| loop | `foreach (arr[i]) arr[i] > 0` | LoopConstraintSyntax |
| dist | `x dist {1:=1, 2:=3}` | ExpressionConstraintSyntax (dist) |
| unique | `unique {a, b}` | UniquenessConstraintSyntax |
| solve_before | `solve a before b` | SolveBeforeConstraintSyntax |

## 依赖

- pyslang: SystemVerilog AST 解析
- graphviz: 可视化
- z3-solver: 冲突检测

## 使用示例

```python
from parse import SVParser
from debug import ConstraintParser as CP

parser = SVParser()
parser.parse_file('design.sv')
cp = CP(parser)

# 基础分析
report = cp.get_report()

# 可视化
dot = cp.visualize_relationships()
dot.render('output/constraints')

# 冲突检测
detector = cp.detect_conflicts()
print(detector.get_report())
```
