# SV-Trace

> **开发说明**: 本项目由 [OpenClaw](https://github.com/openclaw) AI助手 驱动

**SystemVerilog 静态分析工具库** - RTL 设计分析、信号追踪、时钟域分析

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 项目定位

**AI Agent 硬件理解引擎** - 给 AI Agent 调用的"感知器官"

### 核心理念

1. **AST 优先** - 所有分析基于 pyslang AST，禁止正则分析源码
2. **原子化、可组合** - 每个功能像"技能原子"，Agent 可按需调用
3. **置信度标注** - 所有 API 返回包含 confidence 字段

### 核心功能

| 功能 | 模块 | 说明 |
|------|------|------|
| 信号驱动追踪 | `trace/driver.py` | 追踪信号的驱动源 |
| 信号负载追踪 | `trace/load.py` | 追踪信号的负载 |
| 数据流追踪 | `trace/dataflow.py` | 追踪数据流路径 |
| 控制流分析 | `trace/controlflow.py` | 分析 always_ff/always_comb |
| 时钟域追踪 | `query/clock_domain.py` | 识别时钟域内寄存器 |
| 模块端口追踪 | `query/module_connections.py` | 追踪模块端口连接 |

---

## ⚡ 快速开始

### Python API

```python
from parse import SVParser
from trace.driver import DriverCollector
from trace.query import ClockDomainTracer

# 解析文件
parser = SVParser()
parser.parse_file('design.sv')

# 查找信号驱动
collector = DriverCollector(parser)
drivers = collector.find_driver('signal_name')

# 时钟域追踪
tracer = ClockDomainTracer(parser)
result = tracer.trace('clk')
```

---

## 📦 模块统计

| 模块 | 文件数 | 说明 |
|------|--------|------|
| trace | 28 | 核心分析工具 |
| query | 11 | 查询接口 |
| parse | 302 | 语法解析器 |
| lint | 4 | 代码检查 |
| apps | 4 | 应用工具 |
| 测试 | 42+ | 测试用例 |

### 测试分类

| 测试类型 | 说明 |
|----------|------|
| unit | 单元测试 |
| opentitan | OpenTitan 验证 |
| integration | 集成测试 |
| edge_cases | 边界用例 |

---

## 📋 核心工具列表

### 信号分析 (trace/)

| 工具 | 功能 | AST | 置信度 | 测试 |
|------|------|-----|------|-------|
| driver | 驱动追踪 | ✅ | ❌ | ✅ |
| load | 负载追踪 | ✅ | ❌ | ❌ |
| connection | 连接追踪 | ✅ | ❌ | ❌ |
| dataflow | 数据流追踪 | ✅ | ❌ | ❌ |
| controlflow | 控制流分析 | ✅ | ❌ | ✅ |
| signal_classifier | 信号分类 | ❌ | ❌ | ❌ |
| flow_analyzer | 流分析 | ❌ | ❌ | ❌ |
| pipeline_analyzer | 流水线分析 | ❌ | ❌ | ❌ |

### 查询接口 (query/)

| 工具 | 功能 | AST | 置信度 | 测试 |
|------|------|-----|------|-------|
| module_connections | 模块端口 | ✅ | ✅ | ✅ |
| clock_domain | 时钟域追踪 | ✅ | ✅ | ✅ |
| signal_chain | 信号链追踪 | ✅ | ✅ | ✅ |
| signal_chain_query | 高级查询 | ✅ | ✅ | ✅ |

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [DEVELOPMENT_DISCIPLINE.md](./DEVELOPMENT_DISCIPLINE.md) | 开发纪律 (14条铁律) |
| [docs/TOOLS_AUDIT.md](./docs/TOOLS_AUDIT.md) | 工具审计报告 |
| [docs/adr/README.md](./docs/adr/README.md) | 架构决策记录 |

---

## 🔧 开发纪律

本项目遵循 14 条铁律:

1. **AST 唯一数据源** - 禁止正则分析源码
2. **位精确性** - 保留完整位级信息
3. **不可信则不输出** - 无法解析时标 uncertain
4. **模型即契约** - 数据字段有填充代码
5. **原子化必须保持** - 一个语法节点一个文件
6. **Schema 即宪法** - 严格遵循 Schema 定义
7. **新功能必须先有边界测试**
8. **文档与代码同步更新**
9. **任何公开承诺必须在代码中可验证**
10. **每次 API 返回必须有置信度标注**
11. **必须提供 Agent 调用示例**
12. **速度优化必须在正确性之后**
13. **金标准测试** - 先推导金标准再验证
14. **核心三原则**

详细文档: [DEVELOPMENT_DISCIPLINE.md](./DEVELOPMENT_DISCIPLINE.md)

---

## 📋 TODO 列表

### 高优先级
- [ ] flow_analyzer.py - 需重构为使用 AST
- [ ] pipeline_analyzer.py - 需重构为使用 AST

### 中优先级
- [ ] connection.py - 需添加 confidence 返回
- [ ] dataflow.py - 需添加 confidence 返回

### 低优先级
- [ ] 添加更多金标准测试

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

<p align="center">
  <strong>SV-Trace</strong> - SystemVerilog 分析利器
</p>
