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

---

## 批次2: debug/analyzers/ (2026-04-29 进行中)

| 模块 | 正则数 | pyslang方法 | 状态 |
|------|--------|-------------|------|
| code_quality_scorer.py | 85 | 计数为主，可保留正则 | ⏳ |
| parametric_analyzer.py | 31 | ✅ extract_params/func/interface/class | ✅ |
| code_metrics_analyzer.py | 27 | 计数为主，可保留正则 | ⏳ |
| clock_tree_analyzer.py | 14 | ✅ extract_clock_signals | ✅ |
| reset_domain_analyzer.py | 11 | ✅ extract_reset_signals/async_reset | ✅ |

### Git Commits (批次2)

```
11402d0 Refactor: reset_domain_analyzer.py 添加 pyslang 方法
2cb3796 Refactor: clock_tree_analyzer.py 添加 pyslang 时钟提取
9aeb2ba Refactor: parametric_analyzer.py 添加 pyslang 方法
```

### 说明

- **code_quality_scorer.py** 和 **code_metrics_analyzer.py** 主要用于统计计数（关键字出现次数），这些用正则即可，不需要 pyslang
- 高优先级的结构化提取已完成

---

## 批次3: trace/ & query/ (2026-04-29 分析完成)

### 分析结果

| 模块 | 正则数 | 分析 |
|------|--------|------|
| trace/load.py | 7 | 简单模式匹配 |
| query/overflow_risk_detector.py | 7 | 简单模式匹配 |
| query/signal.py | 6 | 简单模式匹配 |
| trace/datapath.py | 1 | 简单模式匹配 |
| trace/flow_analyzer.py | 1 | 简单模式匹配 |

### 结论

批次3的文件主要是**简单模式匹配**（信号名、赋值语句解析），这些用正则即可满足需求，不需要 pyslang AST。

**不需要迁移到 pyslang 的场景**：
1. 关键字计数（如 `re.findall(r'\binput\b', content)`）
2. 简单字符串模式匹配（如 `re.match(r'clk.*', name)`）
3. 赋值语句解析（如 `re.search(r'(\w+)\s*=', line)`）

**需要迁移到 pyslang 的场景**：
1. 复杂语法结构（class/constraint/assertion）
2. 嵌套层级结构
3. 需要精确的 AST 节点信息

### 最终状态

| 批次 | 模块数 | 完成 | 保留正则 |
|------|--------|------|----------|
| 批次1 parse/ | 5 | ✅ 5 | 少量 |
| 批次2 debug/analyzers/ | 5 | ✅ 3 (2个保留) | 2个计数为主 |
| 批次3 trace/query/ | ~20 | ✅ 分析完成 | 全部保留 |

**正则转 pyslang 重构任务基本完成！**

---

## 测试验证 (2026-04-29)

### 针对性测试结果

| 测试组 | 测试文件 | 结果 |
|--------|----------|------|
| Class | class_test.sv | ✅ 11 classes |
| Module IO | module_io_test.sv | ✅ 7 modules |
| Clock | clock_reset_test.sv | ✅ 14 clocks |

### 测试用例覆盖

**Class 测试覆盖:**
- 简单类、多成员类
- 继承类 (extends)
- randc 类型
- 软约束 (soft)
- foreach 约束
- dist 约束
- 条件约束 (if-else)
- solve before
- 方法类 (function/task)

**Module IO 测试覆盖:**
- ANSI 风格端口
- 位宽指定端口
- 参数化模块
- 多时钟模块
- 复杂端口类型

**Clock/Reset 测试覆盖:**
- 同步复位
- 异步复位
- 多时钟
- 门控时钟
- 双沿时钟
- 多复位域

### 已知限制

1. **非ANSI风格端口暂不支持** - module_io 目前只支持 ANSI 风格 (input clk, ...) 端口声明
2. **方法未单独统计** - 函数/任务声明与 constraint 是不同概念，当前未分开统计

### 测试文件位置

```
tests/sv_cases/pyslang_tests/
├── class_test.sv          # 11 class 测试用例
├── module_io_test.sv      # 7 module 测试用例
├── clock_reset_test.sv    # 6 clock/reset 测试用例
└── run_pyslang_tests.py    # 测试运行器
```

---

## 新增场景测试 (2026-04-29 晚)

### 测试结果 (8/8 全部通过)

| 场景 | 测试文件 | 结果 |
|------|----------|------|
| Class | class_test.sv | ✅ 11 classes |
| Module IO | module_io_test.sv | ✅ 7 modules |
| Clock/Reset | clock_reset_test.sv | ✅ 14 clocks |
| Sequence/Property | sequence_property_test.sv | ✅ 6 assertions |
| Interface | interface_test.sv | ✅ 4 interfaces |
| Package | package_test.sv | ✅ 3 packages |
| Covergroup | covergroup_test.sv | ✅ 4 covergroups |
| Function/Task | function_task_test.sv | ✅ 5 functions/tasks |

### 测试用例文件清单

```
tests/sv_cases/pyslang_tests/
├── class_test.sv              # 11 class 测试用例
├── module_io_test.sv         # 7 module 测试用例
├── clock_reset_test.sv       # 6 clock/reset 测试用例
├── sequence_property_test.sv  # 6 sequence/property 测试用例
├── interface_test.sv         # 4 interface 测试用例
├── package_test.sv          # 3 package 测试用例
├── covergroup_test.sv        # 4 covergroup 测试用例
├── function_task_test.sv     # 5 function/task 测试用例
├── struct_union_test.sv      # struct/union 测试用例
├── generate_test.sv          # generate 块测试用例
└── run_pyslang_tests.py     # 测试运行器
```

### 修复记录

1. **parametric_analyzer**: 支持 Interface 和 Package 名称提取
   - InterfaceDeclaration/PackageDeclaration 需要从 header 获取名称
