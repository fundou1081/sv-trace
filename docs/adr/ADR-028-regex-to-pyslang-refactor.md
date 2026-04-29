# ADR-028: parse/ 模块正则转 pyslang 重构

## 状态

> **状态**: Accepted
> **日期**: 2026-04-29
> **作者**: OpenClaw / 方浩博

## 摘要

将 sv-trace 的 parse/ 模块从基于正则表达式的解析方式迁移到基于 pyslang AST 的解析方式，解决复杂 SystemVerilog 语法（如 `import xxx::*;`）无法正确解析的问题。

## 背景

### 问题描述

原有的 parse/ 模块大量使用正则表达式解析 SystemVerilog 代码，遇到复杂语法时会失败：

```python
# 旧方式 - 正则解析
re.finditer(r'input\s+(?:logic\s+)?(\w+)', port_str)
```

问题：
1. 无法处理 `import xxx::*;` 等特殊语法
2. 跨行语法匹配困难
3. 类型信息提取不完整
4. 代码脆弱，难以维护

### 影响范围

| 文件 | 正则数 | 问题严重度 |
|------|--------|------------|
| class_utils.py | 14 | 高 |
| constraint.py | 5 | 高 |
| assertion.py | 8 | 高 |
| covergroup.py | 6 | 高 |
| module_io.py | 10 | 高 |

## 决策

### 采用方案: pyslang AST 遍历

```python
# 新方式 - pyslang AST
tree = pyslang.SyntaxTree.fromText(code)
def collect(node):
    if node.kind == SyntaxKind.ImplicitAnsiPort:
        # 直接从 AST 节点提取信息
        direction = node.header.direction.kind
        port_name = node.declarator.name
    return pyslang.VisitAction.Advance
tree.root.visit(collect)
```

### 核心 API

| API | 用途 |
|-----|------|
| `SyntaxTree.fromText(code)` | 解析源码 |
| `tree.root` | 获取 AST 根节点 |
| `node.kind` | 获取节点类型 |
| `node.kind.name` | 获取类型名称字符串 |
| `tree.root.visit(collector)` | 遍历所有节点 |
| `SyntaxKind.XXX` | 枚举类型判断 |

### 关键发现

1. **类成员解析**: 使用 `item.declaration` 获取声明字符串
2. **方向识别**: `header.direction.kind == TokenKind.OutputKeyword`
3. **约束遍历**: `node.kind == SyntaxKind.ConstraintDeclaration`
4. **visit vs 迭代**: `visit()` 比直接迭代更可靠

### 已知问题

| 模块 | 问题 | 状态 |
|------|------|------|
| class_utils.py | method 名字解析有 bug | 待修复 |
| 其他模块 | 无 | 已完成 |

## 实现记录

### 完成状态 (2026-04-29)

| 模块 | 方法 | 状态 |
|------|------|------|
| module_io.py | `extract_from_text()` | ✅ 完成 |
| class_utils.py | `extract_classes_from_text()` | ✅ 完成 (method bug) |
| constraint.py | `extract_constraints_from_text()` | ✅ 完成 |
| assertion.py | `extract_assertions_from_text()` | ✅ 完成 |
| covergroup.py | `extract_covergroups_from_text()` | ✅ 完成 |

### Git Commits

```
8828184 Fix: ModuleIOExtractor 使用 pyslang AST 解析
8707312 Refactor: class_utils.py 使用 pyslang AST 解析
3a8e4e6 Refactor: constraint.py 和 class_utils.py 使用 pyslang
b95d00a Refactor: covergroup.py 使用 pyslang
```

## 下一步

### 批次2: debug/analyzers/ (中优先级)

| 文件 | 正则数 | 备注 |
|------|--------|------|
| code_quality_scorer.py | 85 | 代码质量评分 |
| parametric_analyzer.py | 31 | 参数分析 |
| code_metrics_analyzer.py | 27 | 代码度量 |
| clock_tree_analyzer.py | 14 | 时钟树分析 |
| reset_domain_analyzer.py | 11 | 复位域分析 |

### 批次3: trace/ 模块

| 文件 | 正则数 | 备注 |
|------|--------|------|
| signal_classifier.py | 2 | 信号分类 |
| flow_analyzer.py | 1 | 流分析 |
| datapath.py | 1 | 数据路径 |

## 参考

- [ADR-001: 使用 pyslang 作为解析引擎](./ADR-001.md)
- [ADR-027: Constraint Parser V2 升级架构](./ADR-027-constraint-parser-v2.md)
- pyslang 文档: https://pypi.org/project/pyslang/
