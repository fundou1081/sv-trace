# SV-Trace

> **开发说明**: 本项目由 [OpenClaw](https://github.com/openclaw) AI助手 驱动

**SystemVerilog 静态分析工具库** - RTL 设计分析、信号追踪、时钟域分析

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 项目定位

**AI Agent 硬件理解引擎** - 给 AI Agent 调用的"感知器官"

### 核心理念

1. **AST 优先** - 基于 pyslang AST，禁止正则分析源码
2. **原子化、可组合** - 每个功能像"技能原子"
3. **置信度标注** - 所有 API 返回包含 confidence 字段
4. **14条开发铁律** - 确保代码质量

---

## 📦 模块结构 (2026-05)

```
src/
├── sv_manager.py      # 统一管理器 (新!)
│   ├── SVManager      - 解析入口
│   └── SVResult      - 统一返回(含confidence)
├── pyslang-ast-ref/  # AST参考 (295个文件)
├── trace/            # 核心分析工具 (28个)
└── ...
```

### 核心变更

| 组件 | 旧版 | 新版 |
|------|------|------|
| 解析入口 | parse/SVParser | sv_manager/SVManager |
| 返回值 | 无confidence | SVResult含confidence |
| 行号获取 | 手动 | get_line/get_scope_source |

---

## ⚡ 快速开始

### 安装

```bash
pip install pyslang>=10.0
```

### 新版 API (推荐)

```python
from sv_manager import SVManager

# 创建管理器
manager = SVManager()

# 解析文件
result = manager.parse_file('design.sv')
print(f"Success: {result.success}, Confidence: {result.confidence}")

# 访问 AST
tree = result.tree  # pyslang.SyntaxTree
trees = manager.trees  # dict of all parsed trees

# 获取源码
line = manager.get_line('design.sv', 10)
scope = manager.get_scope_source('design.sv', always_node, max_lines=50)
```

### 旧版 API (仍可用)

```python
from parse import SVParser
from trace.driver import DriverCollector

parser = SVParser()
parser.parse_file('design.sv')
collector = DriverCollector(parser)
```

---

## 📋 开发纪律 (14条铁律)

| 铁律 | 内容 |
|------|------|
| 1 | AST 唯一数据源 |
| 3 | 不可信则不输出 |
| 10 | 每次 API 返回必须有置信度标注 |
| 13 | 金标准测试 |

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [DEVELOPMENT_DISCIPLINE.md](./DEVELOPMENT_DISCIPLINE.md) | 开发纪律 |
| [docs/SV_PARSER_GUIDE.md](./docs/SV_PARSER_GUIDE.md) | SVParser 指南 |
| [docs/SVMANGER_LIMITS.md](./docs/SVMANGER_LIMITS.md) | SVManager 限制 |
| [docs/TOOLS_AUDIT.md](./docs/TOOLS_AUDIT.md) | 工具审计 |

---

## 🔧 TODO

- [x] SVManager 统一入口
- [ ] Driver/Load 使用 SVManager
- [ ] 更多金标准测试

