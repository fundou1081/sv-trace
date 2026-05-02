# pyslang 语法规范

## 概述

`pyslang-spec` 是 SV-TRACE 项目的核心文档，定义了如何将 SystemVerilog 语法映射到 pyslang AST（抽象语法树），帮助开发者理解和使用 pyslang 进行代码分析。

## 在项目中的定位

```
SV-TRACE 项目架构
=================

    ┌─────────────────────────────────────────────┐
    │         SV-TRACE 用户入口                    │
    └─────────────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────────────┐
    │         pyslang-spec (本项目)               │  ← 你在这里
    │  - 语法规范定义                              │
    │  - SyntaxKind 映射                          │
    │  - AST 节点处理示例                          │
    └─────────────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────────────┐
    │         parse/ 模块                          │
    │  - parser.py (核心解析器)                   │
    │  - class_utils.py (类提取)                   │
    │  - constraint.py (约束提取)                  │
    │  - interface.py (接口提取)                 │
    │  ...                                        │
    └─────────────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────────────┐
    │         trace/ 模块                         │
    │  - driver.py (驱动追踪)                     │
    │  - connection.py (连接追踪)                 │
    │  - vcd_analyzer.py (波形分析)              │
    │  ...                                        │
    └─────────────────────────────────────────────┘
```

## 用来做什么

### 1. 理解 pyslang AST 结构

pyslang 解析 SystemVerilog 代码生成 AST（抽象语法树）。`pyslang-spec` 文档化了各种语法节点：

```python
# 例如，解析一个 always_ff 块
module 示例:
    always_ff @(posedge clk)
        if (!rst_n) q <= 0;
        else q <= d;

AST 结构:
    AlwaysFFBlock
        └── Statement
            └── ...
```

### 2. 映射 SyntaxKind 到实际语法

pyslang 有 536 种 SyntaxKind，需要正确映射：

| SyntaxKind | 实际语法 | 处理方式 |
|------------|----------|----------|
| ModuleDeclaration | module ... endmodule | 提取模块名 |
| AlwaysFFBlock | always_ff ... | 提取时钟域 |
| ContinuousAssign | assign ... | 提取连续赋值 |
| ClassDeclaration | class ... endclass | 提取类定义 |
| InterfaceDeclaration | interface ... endinterface | 接口定义 |

### 3. 提供代码示例

`SKILL.md` 包含 8 个可运行的示例：

```python
# 示例 1: 解析模块
from parse import SVParser
p = SVParser()
tree = p.parse_text(code)

# 示例 2: 提取类
from parse.class_utils import ClassExtractor
ce = ClassExtractor(None)
classes = ce.extract_from_text(class_code)
```

### 4. 处理特殊情况

文档化了处理边界情况的最佳实践：

- 非ANSI端口不支持
- 嵌套generate处理
- 参数化模块
- 接口与模块混合

## 文件说明

| 文件 | 说明 | 状态 |
|------|------|------|
| README.md | 本文件 | ✅ |
| SKILL.md | 主技能文档，包含完整示例 | ✅ |
| SV_UNIQUE.md | SystemVerilog 独有语法 | ✅ |
| ast_structure.md | AST 结构详解 | ✅ |

## 使用方法

### 新手入门

1. **从 SKILL.md 开始** - 包含所有需要的基础知识
2. **参考示例代码** - 8个完整可运行的示例
3. **查看 ast_structure.md** - 理解 AST 节点层次

### 进阶使用

1. **查阅 SV_UNIQUE.md** - 了解 SV 独有特性
2. **参考 SyntaxKind 映射** - 了解如何映射语法节点

### 开发者

1. **遵循本规范** - 添加新解析器时保持一致性
2. **更新示例** - 确保代码可以运行
3. **记录边界情况** - 帮助他人理解

## 参与贡献

1. Fork 项目
2. 添加新示例到 SKILL.md
3. 更新 SyntaxKind 映射
4. 提交 Pull Request

## 相关文档

- [SV-TRACE 主文档](../)
- [API 文档](../API.md)
- [项目状态](../PROJECT_STATUS.md)

---

最后更新: 2026-05-01

## 重要: SyntaxKind 命名规范

pyslang 使用特定的命名格式:

| 语法 | pyslang SyntaxKind 名称 |
|------|-------------------------|
| module | ModuleDeclaration |
| always_ff | AlwaysFFBlock |
| always_comb | AlwaysCombBlock |
| always_latch | AlwaysLatchBlock |
| assign | ContinuousAssign |
| logic/reg/wire | DataDeclaration |
| class | ClassDeclaration |
| interface | InterfaceDeclaration |
| constraint | ConstraintBlock |


```python
if item.kind == SyntaxKind.ModuleDeclaration:
    ...
```
```

