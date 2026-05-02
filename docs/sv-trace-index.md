# SV-Trace Project Index

## Overview
SV-Trace is a SystemVerilog static analysis library for RTL design analysis, testbench quality evaluation, and constraint conflict detection.

## Core Capabilities

### Parser Foundation (v1.0)
- **302 parsers** covering 603 syntax kinds
- **112% coverage** of pyslang syntax
- **100% success rate** on sv-tests
- AST-first approach, no regex

### Trace Modules
| Module | Class | Function |
|--------|-------|----------|
| DriverCollector | DriverCollector | Find signal drivers |
| LoadTracer | LoadTracer | Find signal loads |
| DependencyAnalyzer | DependencyAnalyzer | Signal dependency analysis |
| DataFlowTracer | DataFlowTracer | Data flow tracing |
| ControlFlowTracer | ControlFlowTracer | Control flow analysis |

### Debug Analyzers
| Analyzer | Function |
|----------|----------|
| CDCAnalyzer | Clock domain crossing detection |
| FSMAnalyzer | Finite state machine analysis |
| ResetIntegrityChecker | Reset signal integrity |
| ConditionCoverageAnalyzer | Condition coverage |
| FanoutAnalyzer | Signal fanout analysis |

---

## Documentation Index

### Architecture
| Document | Description |
|----------|-------------|
| [PARSER_SUPPORT.md](./PARSER_SUPPORT.md) | Parser support documentation |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | Project structure |
| [adr/README.md](./adr/README.md) | Architecture decision records |

### API Reference
| Document | Description |
|----------|-------------|
| [api_reference.md](./api_reference.md) | API reference |
| [SCHEMAS.md](./SCHEMAS.md) | JSON schema definitions |

### Modules
| Document | Module |
|----------|--------|
| [driver_collector.md](./driver_collector.md) | trace.driver |
| [load.md](./load.md) | trace.load |
| [dependency.md](./dependency.md) | trace.dependency |
| [controlflow.md](./controlflow.md) | trace.controlflow |
| [dataflow.md](./dataflow.md) | trace.dataflow |
| [datapath.md](./datapath.md) | trace.datapath |
| [connection.md](./connection.md) | trace.connection |
| [bitselect.md](./bitselect.md) | trace.bitselect |
| [pipeline_analyzer.md](./pipeline_analyzer.md) | trace.pipeline_analyzer |
| [timing_depth.md](./timing_depth.md) | trace.timing_depth |
| [timing_path.md](./timing_path.md) | trace.timing_path |
| [flow_analyzer.md](./flow_analyzer.md) | trace.flow_analyzer |
| [visualize.md](./visualize.md) | trace.visualize |
| [cdc_analyzer.md](./cdc_analyzer.md) | debug.CDCAnalyzer |

---

## Quick Start

```python
from parse.parser import SVParser
from trace.driver import DriverCollector

# Parse SystemVerilog
parser = SVParser()
parser.parse_file('design.sv')

# Find drivers
collector = DriverCollector(parser)
drivers = collector.find_driver('signal_name')
```

---

*Last updated: 2026-05-02*
