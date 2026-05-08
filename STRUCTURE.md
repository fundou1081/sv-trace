# sv-trace 项目结构

> 更新时间: 2026-05-08

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
│  - ConnectionTracer  → 端口连接                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Pass 3: SemanticEnricher (semantic/)                       │
│  输入: SemanticGraph + AgentContext                         │
│  输出: EnrichedSemanticGraph                                │
│  - 置信度评估                                              │
│  - 自然语言描述生成                                         │
│  - AGENT 填充 business_meaning / tags                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  QueryInterface (trace/query/, trace/debug/)                │
│  - 信号查询、路径追踪、覆盖率分析                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
src/
├── scope/                    # 🆕 Scope 体系 (Phase 0)
│   ├── __init__.py
│   ├── models.py             # ScopeInfo, SignalRef, ScopeKind, ScopeTree
│   ├── builder.py            # ScopeBuilder (Pass 1)
│   ├── symbol_table.py       # SymbolTable
│   └── utils.py             # extract_identifier 等工具函数
│
├── extractors/              # 🆕 统一 Extractor 体系 (Phase 0)
│   ├── __init__.py
│   ├── base.py             # Extractor 基类, SemanticGraph, LoadPoint, DriverPoint
│   ├── load.py             # LoadExtractor
│   └── driver.py           # DriverExtractor (骨架)
│
├── semantic/               # 🔄 语义增强层 (Phase 2)
│   ├── __init__.py
│   ├── models.py          # EnrichedSignal, EnrichedSemanticGraph
│   ├── enricher.py       # SemanticEnricher
│   ├── agent_interface.py  # AgentContext
│   └── base.py           # ⚠️ 兼容层，内部调用 extractors
│
├── trace/                 # 🔄 对外 API 层
│   ├── __init__.py
│   ├── load.py           # LoadTracer (底层 → extractors/)
│   ├── driver.py         # DriverCollector (底层 → extractors/)
│   ├── load_ext.py      # LoadTracerExt 兼容层
│   ├── connection.py     # 端口连接追踪
│   ├── controlflow.py   # 控制流分析
│   ├── dataflow.py       # 数据流分析
│   ├── dependency.py     # 依赖图构建
│   ├── signal_classifier.py
│   ├── pipeline_analyzer.py
│   ├── power_estimation.py
│   ├── flow_analyzer.py
│   ├── area_estimator.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── signal.py
│   │   ├── module.py
│   │   ├── instance.py
│   │   └── connection.py
│   └── query/
│       ├── __init__.py
│       ├── signal.py
│       ├── path.py
│       ├── signal_chain.py
│       ├── condition_relation_extractor.py
│       ├── sample_condition_analyzer.py
│       ├── nested_condition_expander.py
│       └── hierarchy/
│           ├── __init__.py
│           └── resolver.py
│
├── debug/                 # 🔄 调试分析器
│   ├── __init__.py
│   ├── analyzers/       # 分析器集合
│   │   ├── multi_driver.py
│   │   ├── clock_domain.py
│   │   ├── reset_domain_analyzer.py
│   │   ├── fsm_analyzer.py
│   │   ├── coverage_analyzer.py
│   │   ├── xvalue.py
│   │   ├── uninitialized.py
│   │   ├── cdc.py
│   │   ├── timing_analyzer.py
│   │   ├── class_extractor.py
│   │   ├── class_quality.py
│   │   ├── complexity.py
│   │   ├── code_metrics_analyzer.py
│   │   └── design_evaluator.py
│   ├── patterns/
│   └── reports/
│
├── parse/                # 解析器 (pyslang 封装)
│   ├── __init__.py
│   └── sv_parser.py
│
└── apps/                # 应用层
    ├── __init__.py
    ├── dataflow.py
    ├── controlflow.py
    └── evaluate.py
```

---

## ⚠️ 已废弃模块

以下目录/文件已删除，不再可用：

| 目录/文件 | 原因 |
|-----------|------|
| `src/pyslang-ast-ref/` | 删除：297 个参考文件，违反铁律 23 |
| `src/debug/_archive/` | 删除：备份文件 |
| `src/trace/load_ext.py` (旧版) | 被新版覆盖 |

---

## 核心数据流

```
1. SVParser.parse_text() → SyntaxTree
2. ScopeBuilder.build() → ScopeTree + SymbolTable
3. LoadExtractor.extract() → SemanticGraph (loads)
4. DriverExtractor.extract() → SemanticGraph (drivers)
5. SemanticEnricher.enrich() → EnrichedSemanticGraph
6. QueryInterface → 用户查询
```

---

## 命名约定

| 类型 | 前缀/后缀 | 示例 |
|------|-----------|------|
| Extractor | Extractor | `LoadExtractor`, `DriverExtractor` |
| 数据模型 | Point / Info / Ref | `LoadPoint`, `ScopeInfo`, `SignalRef` |
| Builder | Builder | `ScopeBuilder` |
| Enricher | Enricher | `SemanticEnricher` |
| Analyzer | Analyzer | `ClockDomainAnalyzer`, `FSMAnalyzer` |
| 查询类 | Query | `SignalQuery`, `PathQuery` |

---

## 相关文档

- `docs/DEVELOPMENT_DISCIPLINE.md` - 开发纪律（铁律 1-23）
- `docs/MULTI_PASS_ARCHITECTURE_PLAN.md` - 多轮架构迁移计划
- `docs/pyslang-spec/` - pyslang AST 规范
