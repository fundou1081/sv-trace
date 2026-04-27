# SV-Trace

SystemVerilog 静态分析工具库 - 用于信号追踪、TLM 连接分析、UVM testbench 结构提取

## 功能

### 核心分析
- **SV 解析**: 使用 pyslang 解析 SystemVerilog 代码
- **信号追踪**: 驱动追踪、负载追踪、数据流分析
- **层级解析**: 跨模块信号追踪

### Class 分析
- **Class 提取器**: 提取类成员、方法、约束、继承关系
- **类关系图**: 方法调用图、继承层次
- **UVM 组件**: 自动识别 agent/monitor/driver/sequencer

### UVM Testbench 分析
- **组件结构**: 提取 testbench 层次
- **TLM 连接**: analysis/put/get/transport 端口
- **Phase 方法**: build/connect/run 等

## 使用

```python
from parse.parser import SVParser
from debug.class_extractor import ClassExtractor
from debug.uvm.uvm_extractor import UVMExtractor

parser = SVParser()
parser.parse_file('testbench.sv')

extractor = ClassExtractor(parser)
uvm = UVMExtractor(extractor, relation_extractor)
uvm.extract_tlm_connections(code)

print(uvm.get_report())
```

## 测试

```bash
python tests/unit/test_class.py   # 18/18 passed
python test_all.py              # 10/10 passed
```

## 版本

- v0.4: UVM 分析 + ClassExtractor 修复
- v0.3: 层级解析、代码召回
- v0.2: Class/Constraint 提取器

## 文档

- [PLAN.md](PLAN.md) - 开发计划
- [Idea.md](Idea.md) - 功能想法池

## 项目结构

```
src/
├── parse/      # SVParser
├── trace/      # 追踪器
├── query/      # 查询接口
├── debug/      # 分析工具
│   └── uvm/   # UVM 分析
└── lint/      # Linting
```

---

## 🛠️ 已实现工具

### 追踪器 (Trace)
| 模块 | 功能 | 状态 | 说明 |
|------|------|------|------|
| `driver.py` | DriverTracer | ✅ | 查找信号驱动源 (assign/always_ff/comb/latch) |
| `load.py` | LoadTracer | ✅ | 查找信号被读取的位置 |
| `connection.py` | ConnectionTracer | ✅ | 模块实例连接、端口连接 |
| `dataflow.py` | DataFlowTracer | ✅ | 数据流连接追踪 |
| `datapath.py` | DataPathAnalyzer | ✅ | 数据流深度追踪 |
| `controlflow.py` | ControlFlowTracer | ✅ | 控制流分析 |
| `dependency.py` | DependencyAnalyzer | ✅ | 依赖分析 |

### 分析器 (Debug Analyzers)
| 模块 | 功能 | 状态 | 说明 |
|------|------|------|------|
| `multi_driver.py` | MultiDriverDetector | ✅ | 检测多驱动冲突 |
| `cdc.py` | CDCAnalyzer | ✅ | Clock Domain Crossing |
| `clock_domain.py` | ClockDomainAnalyzer | ✅ | 时钟域分析 |
| `dangling_port.py` | DanglingPortDetector | ✅ | 悬空端口检测 |
| `uninitialized.py` | UninitializedDetector | ✅ | 未初始化检测 |
| `xvalue.py` | XValueDetector | ✅ | X 值传播检测 |
| `fsm/extractor.py` | FSMExtractor | ✅ | 状态机提取 |

### 测试
```bash
python test_all.py           # 7/7 通过
python tests/unit/test_driver.py   # 4/4 通过
python tests/unit/test_class.py  # 18/18 通过
```

---

## 🎯 可继续开发的高价值工具

### ✅ 新增: 性能估算 (v0.6)

### ✅ 新增: 仿真性能 (v0.6x)

| 模块 | 功能 | 描述 |
|------|------|------|
| `sim_performance.py` | SimulationPerformance | 仿真运行时间估算 |

```python
from trace.sim_performance import SimulationPerformance

sim = SimulationPerformance(parser)
result = sim.analyze("module_name", clock_freq_mhz=100.0,
                  sim_type="accellera", total_cycles=1000000)
print(result.visualize())
```

支持仿真器: verilator, accellera, iverilog, cadence

输出示例:
```
⏱️ SIMULATION PERFORMANCE
🔔 Clock Domains: clk
📐 Complexity: Comb: 1, Seq: 0
⏱️ Clock: 100 MHz (10.00 ns)
🚀 Sim Speed: 15M cycles/sec
Est. Runtime: 0.07s
🔄 Design Cycles: 1,000,000
⏳ Design Time: 10 ms
```

| 模块 | 功能 | 描述 |
|------|------|------|
| `resource_estimation.py` | ResourceEstimation | 资源利用率估算 (LUT/FF/DSP) |
| `throughput_estimation.py` | ThroughputEstimation | 吞吐量分析 (带宽/Pipeline效率) |
| `performance.py` | PerformanceEstimator | 统一性能报告 |

```python
from trace.performance import PerformanceEstimator

perf = PerformanceEstimator(parser)
report = perf.analyze("module_name", clock_freq_mhz=200.0)
print(report.visualize())
```

输出示例:
```
⚡ PERFORMANCE REPORT: module_name
============================================================

📊 Resources:
  LUT: 248, FF: 1, DSP: 0

⏱️ Timing: Clock: 200.0 MHz

📈 Throughput: Max: 1.00/cycle, Bandwidth: 1.60 Gbps
```

### 设计阶段

### ✅ 新增: 仿真性能 (v0.6x)

| 模块 | 功能 | 描述 |
|------|------|------|
| `sim_performance.py` | SimulationPerformance | 仿真运行时间估算 |

```python
from trace.sim_performance import SimulationPerformance

sim = SimulationPerformance(parser)
result = sim.analyze("module_name", clock_freq_mhz=100.0,
                  sim_type="accellera", total_cycles=1000000)
print(result.visualize())
```

支持仿真器: verilator, accellera, iverilog, cadence

输出示例:
```
⏱️ SIMULATION PERFORMANCE
🔔 Clock Domains: clk
📐 Complexity: Comb: 1, Seq: 0
⏱️ Clock: 100 MHz (10.00 ns)
🚀 Sim Speed: 15M cycles/sec
Est. Runtime: 0.07s
🔄 Design Cycles: 1,000,000
⏳ Design Time: 10 ms
```
| 功能 | 价值 | 描述 |
|------|------|------|
| **PipelineAnalyzer** | ⭐⭐⭐⭐⭐ | 流水线数据路径分析，握手信号时序 |
| **TimingPathExtractor** | ⭐⭐⭐⭐ | 关键路径提取 (组合逻辑深度) |
| **ClockTreeAnalyzer** | ⭐⭐⭐⭐ | 时钟树结构分析 |
| **ResetDomainAnalyzer** | ⭐⭐⭐⭐ | 复位域分析 |

### 验证阶段
| 功能 | 价值 | 描述 |
|------|------|------|
| **CoverageAnalyzer** | ⭐⭐⭐⭐⭐ | 覆盖组解析、覆盖率统计 |
| **CoverageHtmlReporter** | ⭐⭐⭐⭐ | HTML 覆盖率报告生成 |
| **ScoreboardExtractor** | ⭐⭐⭐⭐ | Scoreboard 结构提取 |
| **SequencerAnalyzer** | ⭐⭐⭐⭐ | Sequencer/Driver 关系追踪 |
| **ConfigDBExtractor** | ⭐⭐⭐⭐ | uvm_config_db 追踪 |

### 调试阶段
| 功能 | 价值 | 描述 |
|------|------|------|
| **WaveDumper** | ⭐⭐⭐⭐⭐ | 生成波形追踪脚本 |
| **LogAnalyzer** | ⭐⭐⭐⭐ | 日志模式匹配 |
| **ErrorPatternDetector** | ⭐⭐⭐⭐ | 错误模式检测 |

### 文档/报告
| 功能 | 价值 | 描述 |
|------|------|------|
| **ArchitectureDocGenerator** | ⭐⭐⭐⭐ | 架构文档自动生成 |
| **HTMLReportGenerator** | ⭐⭐⭐⭐ | HTML 报告生成器 |
| **MarkdownExporter** | ⭐⭐⭐⭐ | Markdown 导出 |

---

## 📋 待实现功能优先级

### ✅ 新增: 性能估算 (v0.6)

### ✅ 新增: 仿真性能 (v0.6x)

| 模块 | 功能 | 描述 |
|------|------|------|
| `sim_performance.py` | SimulationPerformance | 仿真运行时间估算 |

```python
from trace.sim_performance import SimulationPerformance

sim = SimulationPerformance(parser)
result = sim.analyze("module_name", clock_freq_mhz=100.0,
                  sim_type="accellera", total_cycles=1000000)
print(result.visualize())
```

支持仿真器: verilator, accellera, iverilog, cadence

输出示例:
```
⏱️ SIMULATION PERFORMANCE
🔔 Clock Domains: clk
📐 Complexity: Comb: 1, Seq: 0
⏱️ Clock: 100 MHz (10.00 ns)
🚀 Sim Speed: 15M cycles/sec
Est. Runtime: 0.07s
🔄 Design Cycles: 1,000,000
⏳ Design Time: 10 ms
```

| 模块 | 功能 | 描述 |
|------|------|------|
| `resource_estimation.py` | ResourceEstimation | 资源利用率估算 (LUT/FF/DSP) |
| `throughput_estimation.py` | ThroughputEstimation | 吞吐量分析 (带宽/Pipeline效率) |
| `performance.py` | PerformanceEstimator | 统一性能报告 |

```python
from trace.performance import PerformanceEstimator

perf = PerformanceEstimator(parser)
report = perf.analyze("module_name", clock_freq_mhz=200.0)
print(report.visualize())
```

输出示例:
```
⚡ PERFORMANCE REPORT: module_name
============================================================

📊 Resources:
  LUT: 248, FF: 1, DSP: 0

⏱️ Timing: Clock: 200.0 MHz

📈 Throughput: Max: 1.00/cycle, Bandwidth: 1.60 Gbps
```

1. **P0 - 立即需要**
   - CoverageHtmlReporter
   - ConfigDBExtractor

2. **P1 - 高价值**
   - PipelineAnalyzer
   - WaveDumper
   - ArchitectureDocGenerator

3. **P2 - 增强功能**
   - TimingPathExtractor
   - HTMLReportGenerator

---

## ✅ 新增: PipelineAnalyzer (v0.5)

```python
from trace.pipeline_analyzer import PipelineAnalyzer

analyzer = PipelineAnalyzer(parser)
result = analyzer.analyze_signal('stage2_data')
print(result.visualize())
```

输出示例:
```
📊 Summary: 3 stages, 6 registers
🔄 Stages:
  [0] Stage1 - stage1_valid, stage1_data
  [1] Stage2 - stage2_valid, stage2_data
  [2] Stage3 - stage3_data, stage3_valid
```

---

## ✅ 新增: TimingPathExtractor (v0.5)

```python
from trace.timing_path import extract_timing_paths

result = extract_timing_paths(parser)
print(result.visualize())

# Critical paths
for p in result.paths:
    print(f"{p.start_signal} -> {p.end_signal} [depth={p.depth}]")
```

输出示例:
```
TIMING PATH ANALYSIS
Total paths: 2
Max logic depth: 1
Critical: c -> b
Paths:
  c -> b [type=comb, depth=1]
  a -> c [type=comb, depth=1]
```

## Constraint Parser V2 (2026-04)

全新架构使用 pyslang + z3:

```bash
bin/svtrace constraint design.sv  # 使用
```

完整文档: `docs/CONSTRAINT_PARSER_V2.md`
