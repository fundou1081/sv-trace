# SV-Trace 项目架构文档

> 更新时间: 2026-05-13
> 项目路径: `/Users/fundou/my_dv_proj/sv-trace`

---

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                    (Apps / CLI / Agent)                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Semantic Layer (语义增强)                    │
│            semantic/enricher.py, semantic/agent_interface.py     │
│                                                                  │
│   - EnrichedSignal, EnrichedDriverPoint, EnrichedLoadPoint     │
│   - SemanticEnricher: 置信度标注 + caveats                      │
│   - AgentContext: 智能体上下文                                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Extractors Layer (提取器)                    │
│                         extractors/                             │
│                                                                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐ │
│   │  Driver     │  │   Load      │  │ Connection  │  │ base   │ │
│   │  Extractor  │  │  Extractor  │  │  Extractor  │  │ (通用) │ │
│   └─────────────┘  └─────────────┘  └─────────────┘  └────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Scope Builder                             │
│                    scope/builder.py, scope/tree.py              │
│                                                                  │
│   - ScopeTree: 模块/接口/package 作用域树                       │
│   - SymbolTable: 符号表                                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Parse Layer (解析)                           │
│                         parse/                                  │
│                                                                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│   │  SVParser   │  │   Module    │  │  Signal     │  ...        │
│   │  (入口)     │  │  Extractor  │  │  Extractor  │             │
│   └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Pyslang (底层 AST)                           │
│                  python-pyslang 库                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心模块

### 2.1 parse/ - 解析层

**入口**: `parse/parser.py` → `SVParser`

```python
from parse import SVParser

parser = SVParser(verbose=False)
tree = parser.parse_file('design.sv')  # 返回 pyslang.SyntaxTree
tree = parser.parse_text(RTL_CODE)     # 解析文本
```

**子模块**:
| 文件 | 功能 |
|------|------|
| `parser.py` | 主解析器，封装 pyslang |
| `extractors.py` | Module/Signal/Port/Instance 提取器 |
| `class_utils.py` | Class 定义提取 |
| `interface.py` | Interface/Modport/Clocking 提取 |
| `package.py` | Package 提取 |
| `covergroup.py` | Covergroup 提取 |

---

### 2.2 extractors/ - 提取器层

**核心类**: `Extractor` (基类), `SemanticGraph`

```python
from extractors.base import SemanticGraph, Extractor, DriverPoint, LoadPoint

# SemanticGraph 包含所有提取结果
graph.drivers   # {signal: [DriverPoint]}
graph.loads     # {signal: [LoadPoint]}
graph.connections  # [Connection]
```

**导出**:
| 文件 | 功能 |
|------|------|
| `base.py` | `Extractor`, `SemanticGraph`, `DriverPoint`, `LoadPoint`, `Connection` |
| `driver.py` | `DriverExtractor` |
| `load.py` | `LoadExtractor` |
| `connection.py` | `ConnectionExtractor` |

---

### 2.3 scope/ - 作用域构建

**入口**: `scope/builder.py` → `ScopeBuilder`

```python
from scope.builder import ScopeBuilder

builder = ScopeBuilder()
scope_tree, symbol_table = builder.build(tree)
```

**子模块**:
| 文件 | 功能 |
|------|------|
| `builder.py` | `ScopeBuilder` |
| `tree.py` | `ScopeTree` |
| `symbol.py` | `SymbolTable` |

---

### 2.4 trace/ - 追踪层

**入口**: `trace/driver.py` → `DriverCollector`

```python
from trace.driver import DriverCollector

dc = DriverCollector(parser=parser, verbose=False)
dc.collect(tree, 'module.sv')
dc.drivers  # {'signal': [DriverPoint, ...]}
dc.get_drivers('signal')  # 获取特定信号的驱动
```

**导出** (通过 `trace/__init__.py`):
```python
from trace import DriverTracer, LoadTracer, DataFlowTracer, ConnectionTracer
# 注意: 这些是 DriverCollector 等的别名
```

**子模块**:
| 文件 | 功能 |
|------|------|
| `driver.py` | `DriverCollector`, `DriverTracer` (别名) |
| `load.py` | `LoadTracer` |
| `connection.py` | `ConnectionTracer` |
| `dataflow.py` | `DataFlowTracer` |
| `controlflow.py` | `ControlFlowTracer` |

---

### 2.5 semantic/ - 语义增强层

**入口**: `semantic/enricher.py` → `SemanticEnricher`

```python
from semantic.enricher import SemanticEnricher
from semantic.models import EnrichedSignal

enricher = SemanticEnricher(parser, scope_tree, symbol_table)
enriched = enricher.enrich(graph)
```

**子模块**:
| 文件 | 功能 |
|------|------|
| `base.py` | 兼容层 (重导出 extractors) |
| `enricher.py` | `SemanticEnricher` |
| `agent_interface.py` | `AgentContext` |
| `models.py` | `EnrichedSignal`, `EnrichedDriverPoint` |
| `clock.py` | `ClockDomainItem`, `ClockSignalItem` |
| `reset.py` | `ResetSignalItem` |
| `driver.py` | 驱动语义增强 |
| `load.py` | 负载语义增强 |

---

## 3. 数据模型

### 3.1 DriverPoint

```python
@dataclass
class DriverPoint:
    signal: str       # 被驱动的信号名
    driver: str       # 驱动表达式 (RHS)
    kind: str         # 'always_ff' | 'always_comb' | 'continuous'
    line: int = 0
    clock: str = ""    # 关联时钟
    reset: str = ""    # 关联复位
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)
```

### 3.2 LoadPoint

```python
@dataclass
class LoadPoint:
    signal: str        # 被使用的信号名
    consumer: str      # 使用者表达式
    kind: str          # 'always_ff' | 'always_comb' | 'continuous'
    line: int = 0
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)
```

### 3.3 Connection

```python
@dataclass
class Connection:
    from_instance: str  # 源实例
    from_port: str       # 源端口
    to_instance: str    # 目标实例
    to_port: str         # 目标端口
    signal: str = ""     # 连接信号
    line: int = 0
```

### 3.4 ConfidenceLevel

```python
class ConfidenceLevel(Enum):
    HIGH = "high"       # 高置信度
    MEDIUM = "medium"   # 中置信度
    LOW = "low"         # 低置信度
    UNCERTAIN = "uncertain"  # 不确定
```

---

## 4. 迁移说明 (2026-05)

### 4.1 新架构 vs 旧架构

| 旧架构 | 新架构 | 状态 |
|--------|--------|------|
| `LoadTracerRegex` | `LoadTracer` | ✅ 已移除 |
| `ModuleConnectionsQuery` | `ConnectionTracer` | ✅ 已移除 |
| `SignalChainQuery` | `DriverCollector` + `LoadTracer` | ✅ 已移除 |
| `SemanticCollector` | `DriverCollector` | ✅ 兼容层保留 |
| `trace.query.*` | `trace.*` | ⚠️ 迁移中 |

### 4.2 已废弃模块

```python
# 旧 (已废弃)
from trace.query.clock_domain import ClockDomainTracer

# 新
from trace.driver import DriverCollector  # 包含时钟/复位提取
```

### 4.3 正确用法

```python
from parse import SVParser
from trace.driver import DriverCollector

# 1. 解析
parser = SVParser(verbose=False)
tree = parser.parse_file('design.sv')

# 2. 收集驱动
dc = DriverCollector(parser=parser, verbose=False)
dc.collect(tree, 'design.sv')

# 3. 查询
drivers = dc.get_drivers('signal_name')
for d in drivers['signal_name']:
    print(f"  {d.signal} <- {d.driver} ({d.kind})")
    print(f"  clock={d.clock}, reset={d.reset}")
```

---

## 5. 调试和验证

### 5.1 测试命令

```bash
cd ~/my_dv_proj/sv-trace

# 运行核心测试 (tools/ + sv_trace/)
python -m pytest tests/unit/tools/ tests/unit/sv_trace/ -v --tb=short

# 快速验证
python -m pytest tests/unit/tools/ -q --tb=no
```

### 5.2 当前测试状态 (2026-05-15)

| 目录 | 通过 | 错误 |
|------|------|------|
| `tests/unit/trace/` | 90 | 0 |
| **总计** | **90** | **0** |

---

## 6. 项目结构

```
src/
├── parse/              # 解析层
│   ├── parser.py       # SVParser 入口
│   ├── extractors.py   # 基础提取器
│   ├── class_utils.py  # Class 提取
│   ├── interface.py     # Interface 提取
│   └── ...
│
├── extractors/         # 提取器层
│   ├── base.py         # 核心数据结构
│   ├── driver.py       # 驱动提取
│   ├── load.py         # 负载提取
│   └── connection.py   # 连接提取
│
├── scope/              # 作用域构建
│   ├── builder.py      # ScopeBuilder
│   └── ...
│
├── trace/              # 追踪层
│   ├── driver.py       # DriverCollector
│   ├── load.py         # LoadTracer
│   ├── connection.py   # ConnectionTracer
│   ├── dataflow.py     # DataFlowTracer
│   └── ...
│
├── semantic/           # 语义增强层
│   ├── enricher.py     # SemanticEnricher
│   ├── models.py       # 增强模型
│   ├── clock.py        # 时钟语义
│   ├── reset.py        # 复位语义
│   └── ...
│
└── ...                 # 其他工具
```

---

## 7. 铁律 (开发纪律)

| 序号 | 描述 |
|------|------|
| 铁律1 | 所有硬件语义提取必须通过 pyslang AST 遍历实现，禁止正则分析源码 |
| 铁律3 | 不可信不输出 - 无法确认时标记 uncertain |
| 铁律13 | 金标准测试 - 先推导金标准再对比验证 |
| 铁律17 | 提取逻辑封装为独立 Visitor 类 |
| 铁律21 | Semantic 层不得直接遍历 AST |
| 铁律22 | Enricher 必须标注 confidence 和 caveats |
| 铁律23 | 底层模块 (extractors/) 不得依赖上层 (semantic/) |

---

*文档生成时间: 2026-05-13*