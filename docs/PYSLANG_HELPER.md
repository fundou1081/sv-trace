# pyslang_helper 模块说明

> 基于 pyslang 的辅助解析工具

## 定位

`pyslang_helper` 是 SVParser 的补充工具，提供：
1. 增强的解析功能
2. 快捷的数据提取方法
3. 特殊语法处理

## 主要功能

### 数据类 (7个)

| 类 | 用途 |
|---|------|
| PortInfo | 端口信息 |
| MemberInfo | 成员信息 |
| ConstraintInfo | 约束信息 |
| MethodInfo | 方法信息 |
| ClassInfo | 类信息 |
| ModuleInfo | 模块信息 |
| FunctionInfo | 函数信息 |

### 提取函数

| 函数 | 功能 |
|------|------|
| extract_all() | 提取所有信息 |
| parse() | 快速解析 |

### SVParser 类

增强版的解析器，包含：
- 基础解析
- 错误处理
- 警告系统

## 与 parse 的关系

```
parse (核心解析器)
    ↓ 返回 SyntaxTree
pyslang_helper (辅助工具)
    ↓ 提取结构化数据
数据类 (PortInfo, MemberInfo, ...)
```

## 使用示例

```python
from pyslang_helper import extract_all

# 提取所有信息
result = extract_all(code)
modules = result['modules']
classes = result['classes']
functions = result['functions']
```

## 与铁律的关系

⚠️ **注意**: pyslang_helper 中有3处使用正则:

| 行号 | 用途 | 是否违反 |
|------|------|---------|
| 536 | `[7:0]` 维度处理 | ⚠️ 字符串处理,可接受 |
| 554 | 声明解析 | ⚠️ 字符串处理,可接受 |
| 585 | function/task 解析 | ⚠️ 字符串处理,可接受 |

这些正则用于处理**字符串表示** (非 AST 解析)，属于铁律1的例外场景。

---

## 总结

| 项目 | 说明 |
|------|------|
| 代码行数 | ~23KB |
| 数据类 | 7个 |
| 提取函数 | 多个 |
| 特殊处理 | 3处正则 (非语义) |

