# SV-Trace

> **开发说明**: 本项目由 [OpenClaw](https://github.com/openclaw) AI助手 驱动

**SystemVerilog 静态分析工具库** - 用于 RTL 设计分析、testbench 质量评估、约束冲突检测

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 项目定位

**AI Agent 硬件理解引擎** - 给 AI Agent 调用的"感知器官"

本项目不是给人类工程师直接用的 EDA 工具，而是做给 AI Agent 调用的"技能原子"。

### 核心理念

1. **非交互式、可编程** - Agent 通过 API 调用，返回结构化数据
2. **原子化、可组合** - 每个功能像"技能原子"，Agent 可按需调用
3. **上下文自扩展** - Agent 能根据前一步结果动态决定下一步操作

### 独特优势

- 打破传统 EDA 的"批次处理范式" - 支持流式、探索式增量分析
- 对"正确性"有更高容忍度 - Agent 可通过多轮交互自行修正
- AI 生成代码是优势 - 用 AI 快速生成技能，契合"覆盖面优先"目标

---

## 🚀 Parser Foundation v1.0

| 指标 | 值 |
|------|-----|
| **解析器文件** | 302 个 |
| **支持语法** | 603 种 |
| **覆盖率** | 112% |
| **sv-tests 成功率** | 100% |

设计原则:
- **AST 优先** - 所有解析器使用 pyslang AST 遍历，无正则表达式
- **原子化** - 每个解析器专注单一语法类别
- **可组合** - 基于现有 parser 可派生新 parser

详细文档: [PARSER_SUPPORT.md](./docs/PARSER_SUPPORT.md)

---

## 📦 安装

```bash
pip install pyslang>=10.0 z3-solver>=4.16 graphviz
```

验证安装:
```bash
python3 -c "from parse import SVParser; print('OK')"
```

---

## ⚡ 快速开始

### Python API

```python
from parse import SVParser
from trace.driver import DriverCollector
from trace.dataflow import DataFlowTracer

# 解析文件
parser = SVParser()
parser.parse_file('design.sv')

# 查找信号驱动
collector = DriverCollector(parser)
drivers = collector.find_driver('signal_name')

# 数据流追踪
tracer = DataFlowTracer(parser)
flow = tracer.trace('signal_name')
```

### CLI 工具

```bash
# 约束分析
sv-constraint design.sv

# 约束概率分析
sv-constraint-prob design.sv

# 数据通路分析
sv-datapath design.sv

# TB 复杂度分析
sv-tb-complexity testbench.sv

# 信号分类
sv-signal design.sv

# 代码质量分析
sv quality design.sv
```

---

## 🛠️ 工具列表

### Tier 1 - 核心工具 🏆

| 模块 | CLI | 功能 |
|------|-----|------|
| `constraint_parser_v2.py` | `sv-constraint` | 约束解析 + z3 冲突检测 |
| `probabilistic_constraint.py` | `sv-constraint-prob` | 约束概率分析 |
| `tb_analyzer/complexity.py` | `sv-tb-complexity` | TB 复杂度分析 (40+ 指标) |
| `class_extractor.py` | - | Class 提取 |
| `class_relation.py` | - | 类关系图 |

### Tier 2 - 重要工具 ⭐

| 模块 | CLI | 功能 |
|------|-----|------|
| `trace/data_path/` | `sv-datapath` | 数据通路 + corner case |
| `trace/driver.py` | - | 驱动追踪 |
| `trace/load.py` | - | 负载追踪 |
| `trace/connection.py` | - | 连接追踪 |
| `trace/dataflow.py` | - | 数据流分析 |
| `trace/pipeline_analyzer.py` | - | Pipeline 分析 |
| `signal_classifier.py` | `sv-signal` | 信号分类 |
| `complexity.py` | `sv-quality` | 代码复杂度 |

### Tier 3 - 扩展工具 📦

| 模块 | CLI | 功能 |
|------|-----|------|
| `trace/cdc_analyzer.py` | - | CDC 分析 |
| `trace/fsm_analyzer.py` | - | FSM 状态机分析 |
| `trace/timing_path.py` | - | 时序路径提取 |
| `trace/timing_depth.py` | - | 时序深度分析 |
| `trace/vcd_analyzer.py` | - | VCD 波形分析 |
| `trace/controlflow.py` | - | 控制流分析 |
| `trace/dependency.py` | - | 依赖分析 |

### Tier 4 - 辅助工具 🔧

| 模块 | CLI | 功能 |
|------|-----|------|
| `verify/risk_evaluator.py` | - | 风险评估 |
| `verify/test_manager.py` | - | 测试管理 |
| `verify/constraint_generator.py` | - | 约束生成 |
| `trace/bitselect.py` | - | 位选择分析 |
| `trace/interface_change.py` | - | 接口变更检测 |
| `lint/linter.py` | - | Lint 检查 |

---

## 📁 项目结构

```
sv-trace/
├── src/
│   ├── parse/          # ✅ 解析器 (302 files) - 基于 pyslang AST
│   ├── trace/          # 信号追踪模块 (22 files)
│   ├── query/          # 查询模块 (13 files)
│   ├── debug/          # 调试分析 (21 files)
│   ├── verify/         # 验证工具
│   ├── core/           # 核心数据模型
│   ├── lint/           # 代码检查
│   ├── apps/           # CLI 应用
│   └── pyslang_helper/ # pyslang 辅助
├── bin/                # CLI 工具 (9个)
├── skills/             # Agent Skills
├── tests/              # 测试用例 (784+)
├── docs/               # 文档 (80+)
│   └── adr/           # 架构决策记录 (28)
└── templates/         # 模板
```

详细文档: [PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md)

---

## 🧪 测试

本项目包含 **784+** 测试用例:

| 子项目 | 测试用例数 | 说明 |
|--------|-----------|------|
| sv_ast | 732 | AST 解析测试 |
| sv_trace | 27 | 信号追踪测试 |
| sv_verify | 22 | 验证工具测试 |
| sv_codecheck | 3 | 代码检查测试 |

测试数据来源: [sv-tests](https://github.com/verikito/sv-tests) (830 个 .sv 文件)

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [PARSER_SUPPORT.md](./docs/PARSER_SUPPORT.md) | Parser 支持文档 (v1.0) |
| [PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md) | 项目结构 |
| [API.md](./docs/API.md) | API 参考 |
| [SCHEMAS.md](./docs/SCHEMAS.md) | JSON Schema 定义 |
| [adr/README.md](./docs/adr/README.md) | 架构决策记录 |

完整索引: [sv-trace-index.md](./docs/sv-trace-index.md)

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

<p align="center">
  <strong>SV-Trace</strong> - SystemVerilog 分析利器
</p>
