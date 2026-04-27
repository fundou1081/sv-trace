# SV-Trace

**SystemVerilog 静态分析工具库** - 用于RTL设计分析、验证testbench质量评估、约束冲突检测

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 目录

- [特性](#特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [工具列表](#工具列表)
- [CLI工具](#cli工具)
- [Python API](#python-api)
- [项目结构](#项目结构)
- [贡献](#贡献)
- [许可证](#许可证)

---

## 特性

### 🔍 RTL分析
- **信号追踪**: 驱动/负载追踪、数据流分析、控制流分析
- **依赖分析**: 模块间依赖关系、信号依赖图
- **时序路径**: 关键路径提取、组合逻辑深度分析

### ✅ 验证支持
- **Constraint分析**: 8种约束类型解析、z3冲突检测
- **概率分析**: 低概率组合发现、Danger Zone检测
- **TB质量评估**: 复杂度评分、UVM组件统计

### 📊 数据通路
- **RTL数据通路提取**: 操作单元识别、数据流图构建
- **概率分析**: SCC检测、rare path发现

### 🎯 UVM Testbench
- **Class分析**: 继承关系、方法映射、约束提取
- **组件识别**: Agent/Driver/Monitor/Sequencer自动识别
- **TLM连接**: analysis/put/get端口追踪

---

## 安装

### 依赖

```bash
pip install pyslang>=10.0 z3-solver>=4.16 graphviz
```

### 验证安装

```bash
python3 -c "from parse import SVParser; print('OK')"
```

---

## 快速开始

### CLI工具

```bash
# 约束分析
sv-constraint design.sv

# 约束概率分析
sv-constraint-prob design.sv

# 数据通路分析
sv-datapath design.sv

# TB复杂度分析
sv-tb-complexity testbench.sv

# 信号分类
sv-signal design.sv

# 代码质量分析
sv-quality design.sv
```

### Python API

```python
from parse import SVParser
from debug.constraint_parser_v2 import parse_constraints
from trace.data_path import analyze_data_path
from verify.tb_analyzer import TBComplexityAnalyzer

# 解析文件
parser = SVParser()
parser.parse_file('design.sv')

# 约束分析
constraints = parse_constraints(parser)
print(constraints.get_report())

# TB复杂度分析
analyzer = TBComplexityAnalyzer(filepath='testbench.sv')
print(analyzer.get_report())
```

---

## CLI工具

### sv-constraint

约束分析工具，支持8种约束类型和z3冲突检测。

```bash
sv-constraint testbench.sv
```

### sv-tb-complexity

TB复杂度分析工具，评估testbench质量和复杂度。

```bash
sv-tb-complexity testbench.sv
```

### sv-datapath

RTL数据通路分析工具。

```bash
sv-datapath design.sv
```

---

## Python API

### 约束分析

```python
from parse import SVParser
from debug.constraint_parser_v2 import parse_constraints
from debug.probabilistic_constraint import ProbabilisticConstraintAnalyzer

parser = SVParser()
parser.parse_file('design.sv')

# 基本约束分析
constraints = parse_constraints(parser)
print(constraints.get_report())

# 概率分析
analyzer = ProbabilisticConstraintAnalyzer(
    constraints.constraints, 
    constraints.dependencies
)
print(analyzer.get_report())
```

### TB复杂度分析

```python
from verify.tb_analyzer import TBComplexityAnalyzer
import json

analyzer = TBComplexityAnalyzer(filepath='testbench.sv')

# 文本报告
print(analyzer.get_report())

# JSON格式
data = analyzer.get_json()
print(json.dumps(data, indent=2))
```

---

## 项目结构

```
sv-trace/
├── src/
│   ├── parse/          # 核心解析器 (pyslang)
│   ├── trace/          # 追踪器模块
│   │   └── data_path/ # 数据通路分析
│   ├── debug/          # 分析工具
│   ├── verify/         # 验证支持
│   └── ...
├── bin/                # CLI工具
├── skills/             # Agent Skills
├── tests/              # 测试用例
├── docs/               # 文档
└── templates/          # 模板
```

---

## 贡献

欢迎提交Issue和Pull Request！

---

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 版本

### v0.7 (2026-04)
- TB复杂度分析器增强 (质量/性能指标)
- Package引用关系分析
- UVM组件详细统计

### v0.6 (2026-04)
- Constraint Parser V2 (pyslang + z3)
- RTL数据通路概率分析
- ProbabilisticConstraintAnalyzer

### v0.5 (2026-04)
- Pipeline分析器
- 时序路径提取
- 性能估算

<p align="center">
  <strong>SV-Trace</strong> - 让SystemVerilog分析更简单
</p>
