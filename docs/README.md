# SV-TRACE 项目文档

## 文档索引

### 核心文档
| 文档 | 描述 |
|------|------|
| [README.md](./docs/README.md) | 项目总览 |
| [PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md) | 项目结构 |
| [api_reference.md](./docs/api_reference.md) | API参考 |

### 模块文档
| 文档 | 模块 |
|------|------|
| [driver_collector.md](./docs/driver_collector.md) | trace.driver |
| [load.md](./docs/load.md) | trace.load |
| [datapath.md](./docs/datapath.md) | trace.datapath |
| [dependency.md](./docs/dependency.md) | trace.dependency |
| [connection.md](./docs/connection.md) | trace.connection |
| [controlflow.md](./docs/controlflow.md) | trace.controlflow |
| [dataflow.md](./docs/dataflow.md) | trace.dataflow |
| [flow_analyzer.md](./docs/flow_analyzer.md) | trace.flow_analyzer |
| [bitselect.md](./docs/bitselect.md) | trace.bitselect |
| [pipeline_analyzer.md](./docs/pipeline_analyzer.md) | trace.pipeline_analyzer |
| [timing_depth.md](./docs/timing_depth.md) | trace.timing_depth |
| [timing_path.md](./docs/timing_path.md) | trace.timing_path |
| [timing_report.md](./docs/timing_report.md) | trace.timing_report |
| [visualize.md](./docs/visualize.md) | trace.visualize |
| [cdc_analyzer.md](./docs/cdc_analyzer.md) | debug.CDCAnalyzer |

### 测试文档
| 文档 | 描述 |
|------|------|
| [MODULE_SUMMARY.md](./docs/MODULE_SUMMARY.md) | 模块汇总 |
| [MODULE_DETAILS.md](./docs/MODULE_DETAILS.md) | 详细API文档 |
| [EDGE_CASE_RESULTS_V2.md](./docs/EDGE_CASE_RESULTS_V2.md) | 边界测试结果 |

---

## 快速开始

```python
from parse import SVParser
from trace.driver import DriverCollector
from trace.load import LoadTracer
from query.signal import SignalQuery

# 解析
parser = SVParser()
parser.parse_file('design.sv')

# 追踪驱动
dc = DriverCollector(parser)
drivers = dc.find_driver('signal_name')

# 追踪加载
lt = LoadTracer(parser)
loads = lt.find_load('signal_name')

# 查询信号
sq = SignalQuery(parser)
signal = sq.find_signal('signal_name')
```

---

## 测试覆盖

| 测试类型 | 状态 |
|----------|------|
| 核心测试 | ✅ 6/6 |
| 边界测试 | ✅ 38/38 |
| P1-P3模块 | ✅ 17+ |

---

## 模块统计

- **Trace**: 22 modules
- **Query**: 13 modules  
- **Debug**: 21 modules
- **总计**: 65 source files
