# parse 模块分析报告

> 分析时间: 2026-05-04

---

## 模块概述

parse 模块是 sv-trace 的核心解析层，基于 pyslang 提供 SystemVerilog 代码解析能力。

---

## 文件统计

| 指标 | 数量 | 说明 |
|------|------|------|
| 总文件数 | 302 | parse/*.py |
| 核心解析器 | 7 | __init__.py 明确导出 |
| 实际使用 | ~7 | 被主动引用的模块 |

---

## 架构分析

### 1. 核心入口 (7个)

| 模块 | 用途 | 引用 |
|------|------|------|
| parser.py (536行) | 主解析器 SVParser | ✅ 主要入口 |
| extractors.py | 提取器集合 | ✅ 常用 |
| class_utils.py | 类提取 | ✅ 常用 |
| pyslang_helper.py | pyslang 封装 | ✅ 辅助 |
| package.py | package 处理 | ✅ |
| interface.py | interface 处理 | ✅ |
| covergroup.py | covergroup 处理 | ✅ |

### 2. 原子解析器 (295个)

这些是自动生成的辅助解析器，提供基础语法支持：
- `*_parser.py` 格式 (如 always_block_parser.py)
- 主要被 `__init__.py` 动态加载
- 不需要手动引用

---

## 实际使用模式

### 模式1: 直接使用 SVParser

```python
from parse import SVParser

parser = SVParser()
tree = parser.parse_file('design.sv')
```

### 模式2: 使用提取器

```python
from parse.extractors import ModuleExtractor, SignalExtractor

extractor = ModuleExtractor()
modules = extractor.extract(tree)
```

### 模式3: 使用辅助函数

```python
from parse import get_source_safe, get_classes

classes = get_classes(tree)
```

---

## trace 模块对 parse 的使用

| trace 模块 | 功能 | parse 使用方式 |
|----------|------|------------|
| driver.py | 驱动追踪 | 直接使用 pyslang.Compilation |
| load.py | 负载追踪 | 直接使用 pyslang.Compilation |
| connection.py | 连接追踪 | 直接使用 pyslang.Compilation |
| dataflow.py | 数据流追踪 | 直接使用 pyslang.Compilation |
| controlflow.py | 控制流分析 | 直接使用 pyslang.Compilation |
| query/module_connections.py | 模块追踪 | 使用 SVParser |
| query/clock_domain.py | 时钟域 | 使用 SVParser |

---

## 结论

### parse 模块的价值

1. **基础解析** - 302个解析器提供语法覆盖
2. **警告机制** - 显式提示不支持的语法
3. **提取工具** - 提供常用的提取函数

### 实际使用

- **主动引用**: 仅 7 个核心模块
- **被动使用**: 295 个自动加载的辅助模块
- **trace 层**: 多数直接使用 pyslang，跳过 parse 层

### 建议优化方向

1. **简化导出** - 只导出常用的 7 个模块
2. **减少冗余** - 295 个辅助模块可能是历史遗留
3. **统一接口** - trace 层统一通过 parse 层访问 pyslang

