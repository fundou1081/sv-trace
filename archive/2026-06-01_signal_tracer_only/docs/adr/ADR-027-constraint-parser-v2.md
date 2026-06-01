# ADR-027: Constraint Parser V2 升级架构

## 状态

> **状态**: Accepted
> **日期**: 2026-04-27
> **作者**: 方浩博

## 摘要

将 sv-trace 的 constraint 解析器从基于字符串的简单实现 (V1) 升级到基于 pyslang AST + z3 求解器的 V2 版本，提供精确解析和冲突检测能力。

## 背景

### V1 问题

1. **解析精度不足** - 基于正则和字符串匹配，无法处理复杂约束结构
2. **类型支持有限** - 仅支持简单类型，conditional/implication/loop 支持不完善
3. **无冲突检测** - 无法检测约束之间的冲突
4. **无可视化** - 无法图形化展示关系

### 需求

验证工程师核心痛点:
- 识别约束中的低概率组合
- 检测约束冲突
- 可视化约束关系

## 决策

### 采用方案: pyslang + z3

**备选方案对比:**

| 方案 | 解析精度 | 冲突检测 | 可视化 | 复杂度 |
|------|----------|----------|--------|--------|
| 自己写解析器 | 中 | 无 | 无 | 高 |
| **pyslang + z3** | **高** | **是** | **是** | 中 |
| slang C++ | 高 | 是 | 是 | 需要绑定 |

**选择理由:**
- pyslang 已被 ADR-001 确认使用
- z3 是开源 SMT 求解器
- graphviz 已有依赖

## 架构

### 组件关系

```
SVParser (pyslang)
    │
    ▼
ConstraintParserV2
    │
    ├─ 解析层 ──→ ClassExtractor → ConstraintDetail
    │
    ├─ 分析层 ──→ DependencyAnalyzer
    │                  │
    │                  ├─ Variable dependencies
    │                  ├─ Inheritance dependencies  
    │                  └─ Solve order dependencies
    │
    ├─ 检测层 ──→ ConflictDetector (z3)
    │                  │
    │                  ├─ Unsatisfiable detection
    │                  └─ Cycle detection
    │
    └─ 可视化层 ──→ Graphviz
                         │
                         ├─ Relationship graph
                         ├─ Dependency graph
                         └─ Interaction graph
```

### 核心类设计

```python
@dataclass
class ConstraintVariable:
    name: str
    is_rand: bool
    line_number: int

@dataclass
class ConstraintDetail:
    name: str
    class_name: str
    constraint_type: str  # simple/conditional/implication/loop/dist/unique/solve_before/soft
    variables: List[ConstraintVariable]
    raw_expression: str
    # ... 更多字段

class ConstraintParserV2:
    def __init__(self, parser: SVParser):
        self.classes = {}
        self.constraints = {}
        self.dependencies = []
    
    # 基础方法
    def get_class_constraints(cls) -> List[ConstraintDetail]
    def find_variable_in_constraints(var) -> List[ConstraintDetail]
    def get_constraint_type_summary() -> Dict[str, int]
    
    # 分析方法
    def get_inheritance_chain(cls) -> List[str]
    def get_cross_class_references(cls) -> Dict
    
    # 可视化方法
    def visualize_relationships() -> graphviz.Graph
    def visualize_dependency_graph() -> graphviz.Digraph
    
    # 检测方法
    def detect_conflicts() -> ConflictDetector
```

## 实现

### 依赖

```txt
pyslang>=4.0
graphviz>=2.0  
z3-solver>=4.8
```

### 方法映射

| V1 方法 | V2 状态 | 说明 |
|---------|---------|------|
| get_constraint_type_summary | ✅ 兼容 | 相同 |
| get_cross_variable_constraints | ✅ 增强 | 增加分析 |
| find_overridden_constraints | ✅ 兼容 | 相同 |
| find_variable_in_constraints | ✅ 兼容 | 相同 |
| get_report | ⚠️ 兼容 | 签名略�� |
| get_all_constraints | ✅ 新增 | 无参数 |
| get_class_constraints | ✅ 新增 | 需要cls |

### 新增方法

- `visualize_relationships()` - 生成变量-约束-Class关系图
- `visualize_dependency_graph()` - 生成依赖图
- `visualize_constraint_interaction()` - 生成交互图
- `detect_conflicts()` - 返回 ConflictDetector
- `get_inheritance_chain()` - 返回继承链
- `get_cross_class_references()` - 返回跨类引用

## 影响

### API 变更

1. 导入路径不变: `from debug import ConstraintParser`
2. 使用方式基本兼容
3. 新增可选参数

### 性能影响

- 解析时间: 增加 ~20% (pyslang AST 遍历)
- 内存: 增加 ~50MB (z3 依赖)

## 测试验证

```python
# 冲突检测测试
tests = [
    ('无冲突', 'x > 10; x < 100', 0),
    ('范围冲突', 'x > 100; x < 50', 2),
    ('Inside无重叠', 'x inside [1:10]; x inside [20:30]', 2),
    ('Inside+范围', 'x inside [1:50]; x > 100', 2),
]

# 结果: 全部通过 ✓
```

## 结论

| 功能 | V1 | V2 | 改进 |
|------|:--:|:--:|:---:|
| 解析精度 | 字符串 | AST | ✅ 大幅提升 |
| 约束类型 | 4种 | 8种 | ✅ +100% |
| 冲突检测 | 无 | z3 | ✅ 新增 |
| 可视化 | 无 | graphviz | ✅ 新增 |
| 跨class | 无 | 有 | ✅ 新增 |

**V2 已完全替代 V1，旧版已归档。**

## 参考文档

- docs/CONSTRAINT_PARSER_V2.md
- src/debug/_archive/constraint_parser_backup.py
