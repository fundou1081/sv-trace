# SV-Trace

> **开发说明**: 本项目由 [OpenClaw](https://github.com/openclaw) AI助手 驱动

**SystemVerilog 静态分析工具库** - RTL 设计分析、信号追踪、时钟域分析

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-80%25%20passed-yellow.svg)](#-测试结果)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 项目定位

**AI Agent 硬件理解引擎** - 给 AI Agent 调用的"感知器官"

通过 AST 遍历提取 SystemVerilog 设计的语义信息，为 AI Agent 提供硬件理解能力。

### 核心理念

1. **AST 优先** - 基于 pyslang AST，禁止正则分析源码
2. **3-Pass 架构** - ScopeBuilder → Extractors → SemanticEnricher
3. **原子化、可组合** - 每个功能像"技能原子"
4. **置信度标注** - 所有 API 返回包含 confidence 字段
5. **24条开发铁律** - 确保代码质量

---

## ⚡ 快速开始

### 安装

```bash
pip install pyslang>=10.0
cd ~/my_dv_proj/sv-trace
```

### 基本用法

```python
import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector
from trace.load import LoadTracer

# 解析
parser = SVParser()
parser.parse_file('design.sv')

# 收集驱动信息
dc = DriverCollector(parser)
for fname, tree in parser.trees.items():
    dc.collect(tree, fname)

print(f"Drivers: {list(dc.drivers.keys())}")
print(f"Clocks: {dc.all_clocks}")
print(f"Resets: {dc.all_resets}")

# 收集负载信息
lt = LoadTracer()
for fname, tree in parser.trees.items():
    lt.collect(tree, fname)

print(f"Loads: {list(lt.loads.keys())}")
```

### 时钟域分析

```python
from trace.query.clock_domain import ClockDomainTracer

ct = ClockDomainTracer(parser)
for fname, tree in parser.trees.items():
    ct.collect(tree, fname)

for clock, domain in ct.domains.items():
    print(f"Clock: {clock}, Registers: {len(domain.registers)}")
```

---

## 🏗️ 架构

### 3-Pass 设计

```
┌─────────────────────────────────────────────────────────────┐
│  Pass 1: ScopeBuilder → ScopeTree + SymbolTable            │
│  构建作用域边界 (module/always_ff/always_comb/generate)    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Pass 2: Extractors → SemanticGraph                         │
│  - LoadExtractor: 提取负载关系                              │
│  - DriverExtractor: 提取驱动关系 + 时钟/复位                 │
│  - ConnectionExtractor: 提取端口连接                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Pass 3: SemanticEnricher → EnrichedSemanticGraph          │
│  - 添加置信度 (ConfidenceLevel)                            │
│  - 添加业务标注 (tags, business_meaning)                    │
│  - AgentContext: AGENT 交互接口                             │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块

```
src/
├── scope/              # Pass 1: 作用域构建
│   ├── models.py       # ScopeKind, ScopeInfo, SignalRef, ScopeTree
│   ├── builder.py      # ScopeBuilder
│   ├── symbol_table.py # SymbolTable
│   └── utils.py        # extract_identifier 等工具
│
├── extractors/         # Pass 2: AST 遍历 → SemanticGraph
│   ├── base.py         # Extractor 基类, SemanticGraph, LoadPoint, DriverPoint
│   ├── load.py         # LoadExtractor
│   ├── driver.py       # DriverExtractor
│   └── connection.py   # ConnectionExtractor
│
├── semantic/           # Pass 3: 语义增强层
│   ├── enricher.py     # SemanticEnricher
│   ├── agent_interface.py # AgentContext
│   └── models.py       # EnrichedSignal, EnrichedSemanticGraph
│
├── trace/              # 对外 API 层
│   ├── driver.py       # DriverCollector
│   ├── load.py         # LoadTracer
│   ├── parse_warn.py   # ParseWarningHandler
│   └── ...
│
└── parse/              # pyslang 封装
    └── sv_parser.py    # SVParser
```

---

## ✨ 核心能力

| 能力 | 说明 |
|------|------|
| **信号追踪** | 追踪信号的驱动源和负载 |
| **时钟域分析** | 识别时钟信号和跨时钟域路径 |
| **复位分析** | 识别同步/异步复位 |
| **数据流分析** | 构建数据流图 |
| **控制流分析** | 分析 if/case/loop 结构 |
| **依赖分析** | 分析信号间依赖关系 |
| **面积估算** | 估算 LUT/FF/DSP 使用 |
| **功耗估算** | 估算功耗 |

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [STRUCTURE.md](STRUCTURE.md) | 项目结构总览 |
| [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) | 架构迁移指南 |
| [docs/DEVELOPMENT_DISCIPLINE.md](docs/DEVELOPMENT_DISCIPLINE.md) | 24条开发铁律 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 详细架构说明 |

---

## 🔧 开发

### 运行测试

```bash
cd ~/my_dv_proj/sv-trace
pytest tests/ -x -q
```

### 代码规范

遵循 [开发铁律](docs/DEVELOPMENT_DISCIPLINE.md):

- 铁律1: AST 唯一数据源
- 铁律2: 位精确性不可妥协
- 铁律3: 不可信则不输出
- ...
- 铁律24: 方案评估与用户确认

---

## 📊 项目状态

### ✅ 已完成

- 3-Pass 架构实现
- ScopeBuilder / Extractors / SemanticEnricher
- DriverCollector / LoadTracer / ParseWarningHandler
- 时钟域、负载、驱动关系提取
- 80% 测试通过

### 🔄 进行中

- 调试剩余 10 个失败测试
- 适配 debug/ 模块到新架构
- 完善置信度评估

---

## 📁 目录结构

```
sv-trace/
├── src/                    # 源代码
│   ├── scope/              # Pass 1: 作用域
│   ├── extractors/         # Pass 2: 提取器
│   ├── semantic/           # Pass 3: 语义增强
│   ├── trace/              # API 层
│   └── parse/              # pyslang 封装
├── tests/                  # 测试 (~1000)
├── docs/                   # 文档
├── _archive/               # 归档旧文件
├── STRUCTURE.md            # 结构说明
└── README.md               # 本文件
```