# SV-Trace 工具文档

SystemVerilog 时序与CDC分析工具集

## 目录

### 核心模块
1. [README](./README.md) - 总览
2. [API 参考](./api_reference.md) - API 索引

### Trace 模块
- [02_trace_modules](./02_trace_modules.md) - 模块总览
- [driver_collector](./driver_collector.md) - 驱动收集器
- [timing_depth](./timing_depth.md) - 时序深度分析
- [timing_report](./timing_report.md) - 时序报告生成
- [cdc_analyzer](./cdc_analyzer.md) - CDC分析
- [bitselect](./bitselect.md) - 位选分析
- [connection](./connection.md) - 连接追踪
- [controlflow](./controlflow.md) - 控制流分析
- [dataflow](./dataflow.md) - 数据流分析
- [datapath](./datapath.md) - 数据路径分析
- [dependency](./dependency.md) - 依赖分析
- [flow_analyzer](./flow_analyzer.md) - 统一信号流
- [load](./load.md) - 负载追踪
- [pipeline_analyzer](./pipeline_analyzer.md) - 流水线分析
- [timing_path](./timing_path.md) - 时序路径提取
- [visualize](./visualize.md) - 可视化

## 快速开始

```python
from parse.parser import SVParser
from trace.timing_depth import TimingDepthAnalyzer
from trace.reports import generate_report

# 解析文件
parser = SVParser()
parser.parse_file('design.sv')

# 时序分析
analyzer = TimingDepthAnalyzer(parser)
paths = analyzer.analyze()
critical = analyzer.find_critical_path()

# 生成报告
generate_report(parser, 'report.html', format='html')
```

## 架构

```
parse.parser (pyslang)
       ↓
DriverCollector (driver.py)
       ↓
TimingDepthAnalyzer (timing_depth.py)
       ↓
┌──────┴──────┐
↓              ↓
TimingReport  CDCAnalyzer
```
