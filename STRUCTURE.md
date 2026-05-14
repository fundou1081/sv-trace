# sv-trace 项目结构

> 更新时间: 2026-05-15

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│  Parse (pyslang)                                           │
│  输入: .sv 源码 → 输出: SyntaxTree                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Pass 1: ScopeBuilder (scope/)                               │
│  输入: SyntaxTree → 输出: ScopeTree + SymbolTable             │
│  - 模块/接口/program 定义边界                               │
│  - 过程块 (always_ff/comb/always) 边界                      │
│  - 实例层级 (module → instance → sub_instance)              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Pass 2: Extractors (extractors/)                           │
│  输入: SyntaxTree + ScopeTree + SymbolTable                 │
│  输出: SemanticGraph                                        │
│  - LoadExtractor     → 负载关系                             │
│  - DriverExtractor   → 驱动关系                             │
│  - ConnectionExtractor → 端口连接                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Pass 3: SemanticEnricher (semantic/)                       │
│  输入: SemanticGraph + AgentContext                         │
│  输出: EnrichedSemanticGraph                                │
│  - 置信度评估 (ConfidenceLevel)                            │
│  - 自然语言描述生成                                         │
│  - AGENT 填充 business_meaning / tags                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  QueryInterface (trace/)                                    │
│  - driver.py: DriverCollector (驱动收集)                   │
│  - load.py: LoadTracer (负载追踪)                          │
│  - connection.py, dataflow.py, controlflow.py              │
│  - query/clock_domain.py, signal_chain.py, timing_path.py  │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
src/
├── scope/                    # ✅ Pass 1: 作用域体系
│   ├── __init__.py
│   ├── models.py             # ScopeKind, ScopeInfo, SignalRef, ScopeTree
│   ├── builder.py            # ScopeBuilder
│   ├── symbol_table.py       # SymbolTable
│   └── utils.py              # extract_identifier 等工具函数
│
├── extractors/              # ✅ Pass 2: 提取器体系
│   ├── __init__.py
│   ├── base.py              # Extractor 基类, SemanticGraph, LoadPoint, DriverPoint
│   ├── load.py              # LoadExtractor (负载关系)
│   ├── driver.py            # DriverExtractor (驱动关系)
│   └── connection.py         # ConnectionExtractor (端口连接)
│
├── semantic/               # ✅ Pass 3: 语义增强层
│   ├── __init__.py
│   ├── models.py           # EnrichedSignal, EnrichedSemanticGraph
│   ├── enricher.py          # SemanticEnricher
│   └── agent_interface.py   # AgentContext
│
├── trace/                 # ✅ 对外 API 层
│   ├── __init__.py
│   ├── load.py             # LoadTracer (底层 → extractors/)
│   ├── driver.py           # DriverCollector (底层 → extractors/)
│   ├── parse_warn.py       # ParseWarningHandler
│   ├── connection.py       # 端口连接追踪
│   ├── controlflow.py      # 控制流分析
│   ├── dataflow.py         # 数据流分析
│   ├── dependency.py        # 依赖分析
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── interfaces.py
│   └── query/
│       ├── __init__.py
│       ├── clock_domain.py    # 时钟域追踪
│       ├── signal_chain.py    # 信号链路追踪
│       ├── timing_path.py     # 时序路径追踪
│       └── module_connections.py
│
├── debug/                 # 🔄 调试分析器 (待适配)
│   ├── analyzers/
│   └── ...
│
├── parse/                # ✅ pyslang 封装
│   ├── __init__.py
│   └── sv_parser.py       # SVParser
│
└── apps/                # 🔄 应用层 (待评估)
```

---

## ✅ 已完成架构

| 模块 | 状态 | 文件数 | 说明 |
|------|------|--------|------|
| scope/ | ✅ | 4 | Pass 1: ScopeTree 构建 |
| extractors/ | ✅ | 4 | Pass 2: SemanticGraph 提取 |
| semantic/ | ✅ | 3 | Pass 3: 语义增强 |
| trace/ 核心 | ✅ | 3 | load, driver, parse_warn |
| parse/ | ✅ | 1 | SVParser |

---

## 🔄 待适配模块

| 模块 | 说明 |
|------|------|
| trace/ 其他 | connection, dataflow, controlflow 等已添加 fallback |
| trace/query/ | 已适配: clock_domain, signal_chain, timing_path |
| debug/ | 调试分析器，待适配新架构 |
| apps/ | 独立入口，待评估是否需要 |

---

## 📁 _archive/ 归档

```
_archive/
├── semantic_old/           # 归档的 semantic 旧模块
│   ├── base.py              # 兼容层（已废弃）
│   ├── clock.py, driver.py, fsm.py, load.py 等
├── test_driver_semantic_validation.py  # 归档的测试
└── ...
```

**说明**: 归档的文件不再使用，但保留以防需要回溯。

---

## 核心数据流

```
1. SVParser.parse_text() → SyntaxTree
2. ScopeBuilder.build() → ScopeTree + SymbolTable
3. LoadExtractor.extract() → SemanticGraph (loads)
4. DriverExtractor.extract() → SemanticGraph (drivers)
5. SemanticEnricher.enrich() → EnrichedSemanticGraph
6. DriverCollector / LoadTracer → 用户查询
```

---

## 命名约定

| 类型 | 前缀/后缀 | 示例 |
|------|-----------|------|
| Extractor | Extractor | `LoadExtractor`, `DriverExtractor` |
| 数据模型 | Point / Info / Ref | `LoadPoint`, `ScopeInfo`, `SignalRef` |
| Builder | Builder | `ScopeBuilder` |
| Enricher | Enricher | `SemanticEnricher` |
| Tracer | Tracer | `LoadTracer`, `DriverCollector` |
| Analyzer | Analyzer | `ClockDomainAnalyzer` |

---

## 相关文档

- `docs/README.md` - 项目首页
- `docs/MIGRATION_GUIDE.md` - 架构迁移指南
- `docs/DEVELOPMENT_DISCIPLINE.md` - 开发纪律（铁律 1-24）
- `docs/MULTI_PASS_ARCHITECTURE_PLAN.md` - 多轮架构迁移计划