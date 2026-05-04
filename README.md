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

## 📦 模块结构

```
src/
├── parse/              # 核心解析器 (6个纯AST文件)
│   ├── parser.py       # SVParser 主解析器
│   ├── extractors.py   # 提取器集合
│   └── ...
├── trace/              # 核心分析工具 (28个)
│   ├── driver.py       # 驱动追踪
│   ├── load.py        # 负载追踪
│   └── ...
├── query/              # 查询接口 (11个)
│   ├── module_connections.py  # 模块端口
│   ├── clock_domain.py        # 时钟域
│   └── ...
├── pyslang_ast_ref/     # AST参考 (295个未使用)
└── pyslang_helper/     # 辅助工具
```

| 模块 | 文件数 | 说明 |
|------|--------|------|
| parse | 6 | 核心解析器 |
| trace | 28 | 分析工具 |
| query | 11 | 查询接口 |
| pyslang_ast_ref | 295 | AST参考 |

---

## ⚡ 快速开始

### 安装

```bash
pip install pyslang>=10.0
```

### 基本使用

```python
from parse import SVParser
from trace.driver import DriverCollector
from trace.query import ClockDomainTracer

# 解析
parser = SVParser()
tree = parser.parse_file('design.sv')

# 驱动追踪
driver = DriverCollector(parser)
drivers = driver.find_driver('signal_name')

# 时钟域追踪
tracer = ClockDomainTracer(parser)
result = tracer.trace('clk')
```

---

## 📋 核心功能

### 信号分析 (trace/)

| 工具 | 功能 | AST | 置信度 |
|------|------|-----|--------|
| driver | 驱动追踪 | ✅ | ❌ |
| load | 负载追踪 | ✅ | ❌ |
| connection | 连接追踪 | ✅ | ❌ |
| dataflow | 数据流追踪 | ✅ | ❌ |
| controlflow | 控制流分析 | ✅ | ❌ |

### 查询接口 (query/)

| 工具 | 功能 | AST | 置信度 |
|------|------|-----|--------|
| module_connections | 模块端口 | ✅ | ✅ |
| clock_domain | 时钟域追踪 | ✅ | ✅ |
| signal_chain | 信号链追踪 | ✅ | ✅ |

### 解析器 (parse/)

| 方法 | 功能 |
|------|------|
| parse_file() | 解析文件 |
| parse_text() | 解析字符串 |
| get_modules() | 获取模块 |
| get_diagnostics() | 诊断信息 |

---

## 📚 开发纪律 (14条铁律)

| 铁律 | 内容 |
|------|------|
| 1 | AST 唯一数据源 |
| 2 | 位精确性不可妥协 |
| 3 | 不可信则不输出 |
| 4 | 模型即契约 |
| 5 | 原子化必须保持 |
| 6 | Schema 即宪法 |
| 7 | 新功能必须先有边界测试 |
| 8 | 文档与代码同步更新 |
| 9 | 公开承诺必须在代码中可验证 |
| 10 | 每次 API 返回必须有置信度标注 |
| 11 | 必须提供 Agent 调用示例 |
| 12 | 速度优化必须在正确性之后 |
| 13 | 金标准测试 (核心) |
| 14 | 核心三原则 |

详细文档: [DEVELOPMENT_DISCIPLINE.md](./DEVELOPMENT_DISCIPLINE.md)

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [DEVELOPMENT_DISCIPLINE.md](./DEVELOPMENT_DISCIPLINE.md) | 开发纪律 |
| [docs/SV_PARSER_GUIDE.md](./docs/SV_PARSER_GUIDE.md) | SVParser 指南 |
| [docs/TOOLS_AUDIT.md](./docs/TOOLS_AUDIT.md) | 工具审计报告 |
| [docs/PARSE_ANALYSIS.md](./docs/PARSE_ANALYSIS.md) | parse 模块分析 |
| [docs/pyslang-semantic/](./docs/pyslang-semantic/) | 语义解析参考 |
| [docs/pyslang-ast-ref/](./docs/pyslang-ast-ref/) | AST 结构参考 |

---

## 🔧 工具审计状态

| 状态 | 数量 | 占比 |
|------|------|------|
| ✅ 完全符合 | 9 | 33% |
| ⚠️ 部分符合 | 7 | 26% |
| ❌ 需修复 | 11 | 41% |

详见: [docs/TOOLS_AUDIT.md](./docs/TOOLS_AUDIT.md)

---

## 📋 TODO

### 高优先级
- [ ] 重构 flow_analyzer.py 为使用 AST
- [ ] 重构 pipeline_analyzer.py 为使用 AST

### 中优先级
- [ ] 为 connection.py 添加 confidence
- [ ] 为 dataflow.py 添加 confidence

### 低优先级
- [ ] 添加更多金标准测试

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

<p align="center">
  <strong>SV-Trace</strong> - SystemVerilog 分析利器
</p>
