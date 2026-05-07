# Trace 模块详解

## 模块列表

| 模块 | 类 | 功能 |
|---|---|---|
| [bitselect](./bitselect.md) | `BitSelect` | 位选择信号追踪 |
| [connection](./connection.md) | `Connection`, `Instance` | 连接与实例分析 |
| [controlflow](./controlflow.md) | `ControlFlow`, `ControlCondition` | 控制流分析 |
| [dataflow](./dataflow.md) | `DataFlowTracer` | 数据流分析 |
| [datapath](./datapath.md) | `DataPath`, `PipelineStage` | 数据通路与流水线 |
| [dependency](./dependency.md) | `SignalDependency` | 信号依赖分析 |
| [driver](./driver_collector.md) | `DriverCollector` | 驱动收集 |
| [flow_analyzer](./flow_analyzer.md) | `SignalFlow`, `FlowNode` | 统一信号流分析 |
| [load](./load.md) | `LoadTracer` | 负载追踪 |
| [pipeline_analyzer](./pipeline_analyzer.md) | `PipelineStage`, `HandshakeChannel` | 流水线分析 |
| [timing_depth](./timing_depth.md) | `TimingDepthAnalyzer` | 时序深度 |
| [timing_path](./timing_path.md) | `TimingPathExtractor` | 时序路径提取 |
| [visualize](./visualize.md) | `GraphVisualizer` | 可视化 |

## 快速开始

```python
from trace.driver import DriverCollector
from trace.timing_depth import TimingDepthAnalyzer
from trace.dataflow import DataFlowTracer
from trace.pipeline_analyzer import PipelineAnalyzer
from trace.visualize import GraphVisualizer
```
