# SV-Trace 使用指南

_SystemVerilog 静态分析工具库的实用工作流程_

---

## 📁 工具分类

### 1. 解析 (Parse)

| 工具 | 功能 | 用途 |
|------|------|------|
| `SVParser` | 解析 SV 文件 | 所有分析的基础 |
| `ParameterResolver` | 参数解析 | 参数化模块 |
| `AssertionExtractor` | SVA 断言提取 | 断言分析 |
| `CovergroupExtractor` | 覆盖率组提取 | 覆盖率分析 |
| `ConstraintExtractor` | 约束提取 | UVM 约束分析 |

### 2. 追踪 (Trace)

| 工具 | 功能 | 用途 |
|------|------|------|
| `DriverTracer` | 驱动追踪 | 信号驱动源 |
| `LoadTracer` | 负载追踪 | 信号消费 |
| `DataFlowTracer` | 数据流追踪 | 信号传递 |
| `ConnectionTracer` | 连接追踪 | 模块互联 |
| `ControlFlowTracer` | 控制流追踪 | if/case/loop |

### 3. 分析 (Analysis)

| 工具 | 功能 | 用途 |
|------|------|------|
| `DataPathAnalyzer` | 数据路径 | 数据流深度 |
| `PipelineAnalyzer` | 流水线分析 | Pipeline 结构 |
| `TimingDepthAnalyzer` | 时序深度 | 路径延迟 |
| `TimingPathExtractor` | 关键路径 | 时序路径 |
| `DependencyAnalyzer` | 依赖分析 | 信号依赖 |
| `ResourceEstimation` | 资源估算 | LUT/FF/DSP |
| `ThroughputEstimation` | 吞吐量分析 | 带宽/效率 |
| `SimulationPerformance` | 仿真性能 | 运行时间 |

### 4. 调试 (Debug)

| 工具 | 功能 | 用途 |
|------|------|------|
| `CDCAnalyzer` | 跨时钟域 | CDC 检查 |
| `MultiDriverDetector` | 多驱动检测 | 冲突检测 |
| `UninitializedDetector` | 未初始化 | 初始化检查 |
| `XValueDetector` | X 值传播 | X 传播检查 |
| `DanglingPortDetector` | 悬空端口 | 连通性 |
| `FSMExtractor` | 状态机提取 | 状态机分析 |
| `ClockTreeAnalyzer` | 时钟树分析 | 时钟网络结构 |
| `ResetDomainAnalyzer` | 复位域分析 | 复位网络结构 |
| `ClassExtractor` | Class 分析 | OOP 分析 |

### 5. UVM

| 工具 | 功能 | 用途 |
|------|------|------|
| `UVMExtractor` | UVM 组件 | Testbench 结构 |
| `ConfigDBExtractor` | Config DB | UVM 配置追踪 |
| `IOSpecExtractor` | 端口规范 | IO 定义 |

### 6. 报告/查询

| 工具 | 功能 | 用途 |
|------|------|------|
| `SignalQuery` | 信号查询 | 信号定位 |
| `HierarchyQuery` | 层级查询 | 模块层级 |
| `CodeExtractor` | 代码提取 | 源代码 |
| `SVLinter` | 代码检查 | Lint |

---

## 🔧 实用工作流程

### 流程 1: RTL 设计分析

_分析模块结构、信号流向、时序路径_

```python
from parse.parser import SVParser
from trace.driver import DriverCollector
from trace.datapath import DataPathAnalyzer
from trace.timing_depth import TimingDepthAnalyzer
from trace.connection import ConnectionTracer

# 解析
parser = SVParser()
parser.parse_file("design.sv")

# 1. 模块结构
print("=== Module Structure ===")
dc = DriverCollector(parser)
for sig, drivers in dc.drivers.items():
    print(f"{sig}: {len(drivers)} drivers")

# 2. 数据路径
print("\n=== Data Path ===")
dpa = DataPathAnalyzer(parser)
path = dpa.analyze("data_out")
print(path.visualize())

# 3. 时序路径
print("\n=== Timing ===")
timing = TimingDepthAnalyzer(parser)
paths = timing.analyze()
for p in paths[:5]:
    print(f"{p.start_reg} -> {p.end_reg} [depth={p.timing_depth}]")

# 4. 连接
print("\n=== Connections ===")
conn = ConnectionTracer(parser)
connections = conn.trace_connections()
for c in connections:
    print(f"{c.src} -> {c.dst}")
```

### 流程 2: 综合性能评估

_估算硬件资源、吞吐量、仿真时间_

```python
from parse.parser import SVParser
from trace.performance import PerformanceEstimator
from trace.sim_performance import SimulationPerformance

parser = SVParser()
parser.parse_file("design.sv")

# 1. 综合性能
print("=== Performance ===")
perf = PerformanceEstimator(parser)
report = perf.analyze("module_name", clock_freq_mhz=200.0)
print(report.visualize())

# 2. 仿真时间
print("\n=== Simulation ===")
sim = SimulationPerformance(parser)
result = sim.analyze("module_name", 
                    clock_freq_mhz=100.0,
                    sim_type="accellera",
                    total_cycles=1000000)
print(result.visualize())

# 3. 吞吐量
print("\n=== Throughput ===")
from trace.throughput_estimation import ThroughputEstimation
thru = ThroughputEstimation(parser)
result = thru.analyze("module_name", clock_freq_mhz=200.0)
print(result.visualize())
```

### 流程 3: 设计验证

_检查设计问题：CDC、多驱动、未初始化、X 值等_

```python
from parse.parser import SVParser
from debug.analyzers.cdc import CDCAnalyzer
from debug.analyzers.multi_driver import MultiDriverDetector
from debug.analyzers.uninitialized import UninitializedDetector

parser = SVParser()
parser.parse_file("design.sv")

# 1. CDC 检查
print("=== CDC Analysis ===")
cdc = CDCAnalyzer(parser)
result = cdc.analyze()
for issue in result.crossings:
    print(f"{issue.signal}: {issue.issue_type}")

# 2. 多驱动检测
print("\n=== Multi-Driver ===")
md = MultiDriverDetector(parser)
issues = md.detect()
for issue in issues:
    print(f"{issue.signal}: {issue.driver_type}")

# 3. 未初始化
print("\n=== Uninitialized ===")
ud = UninitializedDetector(parser)
issues = ud.detect()
for issue in issues:
    print(f"{issue.signal} at line {issue.line}")
```

### 流程 4: Testbench 分析

_分析 UVM Testbench 结构_

```python
from parse.parser import SVParser
from debug.uvm.uvm_extractor import UVMExtractor
from parse.assertion import AssertionExtractor

parser = SVParser()
parser.parse_file("tb.sv")

# 1. UVM 组件
print("=== UVM Structure ===")
uvm = UVMExtractor(parser)
uvm.extract()
report = uvm.get_report()
print(report)

# 2. 断言
print("\n=== Assertions ===")
ae = AssertionExtractor(parser)
assertions = ae.extract()
for a in assertions:
    print(f"{a.name}: {a.type}")
```

### 流程 5: 代码审查

_Lint 检查和代码质量_

```python
from parse.parser import SVParser
from lint.linter import SVLinter

parser = SVParser()
parser.parse_file("design.sv")

# 1. Lint 检查
print("=== Lint Check ===")
linter = SVLinter(parser)
report = linter.lint()
for issue in report.issues:
    if issue.severity == IssueSeverity.ERROR:
        print(f"[ERROR] {issue.file}:{issue.line}: {issue.message}")
    elif issue.severity == IssueSeverity.WARNING:
        print(f"[WARNING] {issue.file}:{issue.line}: {issue.message}")
```

### 流程 6: 完整设计报告

_一键生成完整设计分析报告_

```python
from parse.parser import SVParser
from trace.performance import PerformanceEstimator
from trace.sim_performance import SimulationPerformance
from debug.analyzers.cdc import CDCAnalyzer

parser = SVParser()
parser.parse_file("design.sv")

# 综合报告
print("="*60)
print("DESIGN ANALYSIS REPORT")
print("="*60)

perf = PerformanceEstimator(parser)
sim = SimulationPerformance(parser)
cdc = CDCAnalyzer(parser)

# 获取所有模块名
import pyslang
modules = []
for fname, tree in parser.trees.items():
    if tree:
        for m in tree.root.members:
            if m.kind == pyslang.SyntaxKind.ModuleDeclaration:
                modules.append(str(m.header.name).strip())

# 分析每个模块
for mod in modules:
    print(f"\n{'='*60}")
    print(f"MODULE: {mod}")
    print(f"{'='*60}")
    
    # 性能
    p = perf.analyze(mod, clock_freq_mhz=100.0)
    print(p.visualize())
    
    # 仿真
    s = sim.analyze(mod, clock_freq_mhz=100.0, total_cycles=100000)
    print(s.visualize())
```

---

## ❌ 缺少的环节

经过工具流程组合分析，发现以下功能缺失：

### 高优先级

| 功能 | 描述 | 影响 |
|------|------|------|
| ✅ CoverageGenerator | 智能覆盖率 | 自动生成 I/O Coverage |
| **WaveDumper** | 波形生成 | 无法快速查看信号 |
| ✅ ConfigDBExtractor | 配置追踪 | UVM 配置检查 |

### 中优先级

| 功能 | 描述 | 影响 |
|------|------|------|
| **ScoreboardExtractor** | Scoreboard 提取 | 无法验证数据结构 |
| **SequencerAnalyzer** | Sequencer 分析 | 无法验证协议 |
| ✅ ClockTreeAnalyzer | 时钟树分析 | 时钟质量验证 ✅ |
| ✅ ResetDomainAnalyzer | 复位域分析 | 复位验证 ✅ |

### 低优先级

| 功能 | 描述 | 影响 |
|------|------|------|
| **PowerEstimator** | 功耗估算 | 设计功耗评估 |
| **TimingReportGenerator** | 时序报告生成 | 时序分析报告 |
| **HTMLExporter** | HTML 报告导出 | 便于分享 |

---

## 📝 使用示例

### 基本使用

```python
from parse.parser import SVParser
from trace.performance import PerformanceEstimator

# 解析
parser = SVParser()
parser.parse_file("module.sv")

# 分析
perf = PerformanceEstimator(parser)
report = perf.analyze("top", clock_freq_mhz=200.0)

# 输出
print(report.visualize())
```

### 批量分析

```python
# 分析整个项目
import glob

parser = SVParser()
for f in glob.glob("src/*.sv"):
    parser.parse_file(f)

perf = PerformanceEstimator(parser)
report = perf.analyze(clock_freq_mhz=100.0)

print(f"Total LUT: {report.lut_count}")
print(f"Total FF: {report.ff_count}")
```

---

## 🔗 工具依赖图

```
SVParser
    │
    ├─► DriverCollector ──────► DataPathAnalyzer
    │                              │
    │                              ├─► PipelineAnalyzer
    │                              └─► TimingDepthAnalyzer
    │
    ├─► ConnectionTracer
    │
    ├─► UVMExtractor
    │       │
    │       └─► AssertionExtractor
    │
    └─► CDCAnalyzer
            │
            ├─► MultiDriverDetector
            ├─► UninitializedDetector
            └─► XValueDetector
```

---

*更多工具流程持续更新中...*

### 流程 7: UVM 配置追踪

_追踪 uvm_config_db 的配置，检查未使用的配置_

```python
from parse.parser import SVParser
from debug.uvm.config_db_extractor import ConfigDBExtractor
from debug.uvm.uvm_extractor import UVMExtractor
from debug.class_extractor import ClassExtractor
from debug.class_relation import ClassRelationExtractor

# 解析
parser = SVParser()
parser.parse_file("tb.sv")

# 1. Config DB 提取
print("=== Config DB Analysis ===")
config = ConfigDBExtractor(parser)
result = config.extract_from_parser()
print(result.visualize())

# 2. 虚拟接口配置
interfaces = config.find_interface_configs()
for cfg in interfaces:
    print(f"Interface: {cfg.instance_path}.{cfg.field_name}")
    print(f"  -> {cfg.value}")

# 3. Sequence 配置
sequences = config.find_sequence_configs()
for cfg in sequences:
    print(f"Sequence: {cfg.instance_path}.{cfg.field_name}")
    print(f"  -> {cfg.value}")
```

---

## 🔗 工具依赖图 (更新)

```
SVParser
    │
    ├─► DriverCollector ──────► DataPathAnalyzer
    │                              │
    │                              ├─► PipelineAnalyzer
    │                              └─► TimingDepthAnalyzer
    │
    ├─► ConnectionTracer
    │
    ├─► UVMExtractor
    │       │
    │       ├─► ConfigDBExtractor  ← NEW
    │       └─► AssertionExtractor
    │
    └─► CDCAnalyzer
            │
            ├─► MultiDriverDetector
            ├─► UninitializedDetector
            └─► XValueDetector
```


### 流程 8: 时钟与复位分析

_分析时钟网络和复位结构_

```python
from parse.parser import SVParser
from debug.analyzers.clock_tree_analyzer import ClockTreeAnalyzer
from debug.analyzers.reset_domain_analyzer import ResetDomainAnalyzer

parser = SVParser()
parser.parse_file("design.sv")

# 1. 时钟分析
print("=== Clock Tree ===")
clock_analyzer = ClockTreeAnalyzer(parser)
clock_result = clock_analyzer.result

print(f"Sources: {len(clock_result.sources)}")
for s in clock_result.sources:
    print(f"  {s.name}: {s.type}")

print(f"Domains: {clock_analyzer.get_all_domains()}")

# 2. 复位分析
print("\n=== Reset Domain ===")
reset_analyzer = ResetDomainAnalyzer(parser)
reset_result = reset_analyzer.result

print(f"Sources: {len(reset_result.sources)}")
for s in reset_result.sources:
    print(f"  {s.name}: {s.type}, {s.polarity}")

for r in reset_analyzer.get_async_resets():
    print(f"  Async: {r.name}")

for r in reset_analyzer.get_sync_resets():
    print(f"  Sync: {r.name}")
```

---

### 流程 9: 完整验证检查

_一键检查设计的关键问题_

```python
from parse.parser import SVParser
from debug.analyzers.cdc import CDCAnalyzer
from debug.analyzers.clock_tree_analyzer import ClockTreeAnalyzer
from debug.analyzers.reset_domain_analyzer import ResetDomainAnalyzer
from debug.analyzers.multi_driver import MultiDriverDetector

parser = SVParser()
parser.parse_file("design.sv")

print("=" * 60)
print("DESIGN VERIFICATION CHECK")
print("=" * 60)

# CDC 检查
print("\n[CDC]")
cdc = CDCAnalyzer(parser)
# print(cdc.analyze())

# 时钟分析
print("\n[Clock]")
clock = ClockTreeAnalyzer(parser)
domains = clock.get_all_domains()
print(f"  Domains: {domains}")

# 复位分析  
print("\n[Reset]")
reset = ResetDomainAnalyzer(parser)
print(f"  Async: {len(reset.get_async_resets())}")
print(f"  Sync: {len(reset.get_sync_resets())}")

# 多驱动检查
print("\n[Multi-Driver]")
md = MultiDriverDetector(parser)
# print(md.detect())

print("\n✅ Verification complete")
```

