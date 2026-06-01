# sv-trace 项目结构

> 更新时间: 2026-06-01
> 状态: 经历过 2026-06-01 的大幅精简，原 16+ 子模块已合并/删除

## 项目目标

> **只做一件事：信号追踪 + 上下文召回，做到极致。**

不做的：CDC 分析、多驱动检测、面积/功耗/性能估算、Lint、FSM 提取、约束分析、覆盖率建议、TB 复杂度评分、Code Quality 评分、Dependency 图、Visualize……

这些都已从 `src/` 删除（见 `archive/2026-06-01_signal_tracer_only/` 归档）。

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│  输入: .sv 源码 (单文件)                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  pyslang Compilation                                        │
│  SyntaxTree.fromText() → Compilation() → getRoot()           │
│  - 完整语义分析（含 generate 展开）                            │
│  - 统一符号表（PortSymbol / ProceduralBlockSymbol 等）         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PortResolver (语法层)                                        │
│  解析 .HierarchyInstantiation 获取实例端口连接                 │
│  例: dut u_dut(.data_in(sig_in)) → (u_dut, data_in, sig_in) │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  SignalTracer (语义层)                                        │
│  root.visit() 遍历所有 ProceduralBlockSymbol +               │
│  ContinuousAssignSymbol，提取 driver/load 关系                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  SignalTracerApp (应用层)                                     │
│  组合 SignalTracer + PortResolver                            │
│  提供跨模块 driver/load 追踪                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  输出: TraceSummary                                          │
│  signal_name, drivers[], loads[]                             │
│  每个 TraceResult 包含:                                       │
│  - file / line / char_offset                                │
│  - scope_kind / scope_text (整个 always_ff 块源码)            │
│  - clock / reset (从 event 表达式提取)                        │
│  - condition / condition_stack (嵌套 if 条件)                │
│  - hierarchical_path / is_port / port_direction              │
│  - port_connection (跨模块时填充)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
sv-trace/
├── src/
│   ├── __init__.py                  # 包入口（精简 docstring）
│   ├── sv_manager.py                # SV 文件加载、源码定位、行号查询
│   └── signal_tracer/               # 核心：信号追踪器
│       ├── __init__.py              # 公开 API
│       ├── models.py                # TraceResult / TraceSummary / ScopeInfo
│       ├── tracer.py                # SignalTracer: 语义层 driver/load 提取
│       ├── port_resolver.py         # PortResolver: 语法层端口连接解析
│       └── signal_tracer_app.py     # SignalTracerApp: 组合 + 跨模块追踪
│
├── benchmarks/                      # 12 个 SV fixture (1-10 + comprehensive)
│                                   # 涵盖 always_ff / always_comb / case / generate / FSM / pipeline
│
├── tests/
│   ├── unit/                       # 真测试 (pytest 可发现)
│   │   ├── test_real_projects.py
│   │   └── sv_trace/
│   │       └── test_all_tiers_extended.py
│   ├── targeted/                    # 40 个 .sv fixture (旧测试数据)
│   ├── unit/trace/sv_cases/         # 50+ 个 .sv fixture (按类别分目录)
│   │   ├── cdc/                     # (旧 CDC 测试代码)
│   │   ├── driver/                  # (driver 测试代码)
│   │   ├── fsm/                     # (FSM 测试代码)
│   │   └── ...
│   ├── advanced/test.sv
│   ├── testbed/cpu.sv
│   ├── README.md
│   └── TEST_PLAN.md
│
├── _archive/                        # 多轮历史归档（不动）
├── _archived/                       # 多轮历史归档（不动）
├── archive/                         # 多轮历史归档（不动）
│   ├── 2026-06-01_signal_tracer_only/  # 2026-06-01 重构前的 src/ 全部代码
│   ├── deprecated/                  # 早期废弃文件
│   └── ...
│
├── tests/_legacy/                   # 2026-06-01 重构前的旧测试 (167 .py + 7 .md + 1 .json)
│                                   # 保留以供回溯；不再被 pytest 发现
│
├── STRUCTURE.md                     # 本文件
├── TODO.md                          # 当前路线图
├── TEST_PLAN.md                     # 测试计划 (顶层)
├── tests/
│   ├── README.md                    # 测试总览
│   └── TEST_PLAN.md                 # 测试详细计划
├── pyproject.toml
├── pytest.ini
└── Makefile
```

---

## 公开 API

```python
from signal_tracer import trace_signal, trace_signal_from_file, TraceSummary

# 函数式 API
result: TraceSummary = trace_signal("data_out", sv_code, "test.sv")

# 类式 API
from signal_tracer import SignalTracer, SignalTracerApp
tracer = SignalTracer(sv_code, "test.sv").build()
result = tracer.trace("data_out")           # 包含跨模块追踪
```

`TraceSummary` 字段：

| 字段 | 类型 | 含义 |
|------|------|------|
| `signal_name` | str | 查询的信号名 |
| `drivers` | `List[DriverTrace]` | 所有驱动（谁在写它） |
| `loads` | `List[LoadTrace]` | 所有负载（谁在读它） |
| `.get_clock_domains()` | `List[str]` | 涉及的时钟域 |
| `.get_driver_chain(max_depth)` | `List[str]` | 驱动链（递归上游） |

`DriverTrace` / `LoadTrace` 字段（继承自 `TraceResult`）：

| 字段 | 类型 | 含义 |
|------|------|------|
| `signal_name` | str | 该 trace 关联的信号 |
| `source_expr` | str | 驱动源 / 负载源 表达式文本 |
| `source_signals` | `List[str]` | 表达式中引用的其他信号 |
| `file` | str | 文件路径 |
| `line` | int | 赋值语句行号 |
| `scope_kind` | ScopeKind | `ALWAYS_FF` / `ALWAYS_COMB` / `ALWAYS_LATCH` / `CONTINUOUS_ASSIGN` |
| `scope_text` | str | 整个 scope 的源码（always_ff 整块） |
| `scope_line_start/end` | int | scope 源码起止行 |
| `clock` | str | 提取出的时钟名（`posedge clk`） |
| `reset` | str | 提取出的复位名（`negedge rst_n`） |
| `condition` | str | 赋值所在 if 条件 |
| `condition_stack` | `List[str]` | 嵌套 if 条件栈 |
| `is_port` | bool | 是否是端口 |
| `port_direction` | str | `'in'` / `'out'` / `'inout'` |
| `hierarchical_path` | str | 完整层次路径（`top.u_dut.data_out`） |
| `confidence` | str | `'high'` / `'medium'` / `'low'` |

---

## 数据流（单次 `trace()` 调用）

```
1. SignalTracer.__init__()       存 sv_code, file_path
2. .build()                       pyslang parse → 遍历 ProceduralBlock/ContinuousAssign
                                  → self._drivers, self._loads, self._scopes
3. .trace(signal_name)            查 self._drivers / self._loads
                                  → 跨模块时调 self._cross_module_drivers/loads
                                  → 返回 TraceSummary
```

---

## 不做 / 已删除模块

下面这些在 2026-06-01 之前存在，已删除（归档在 `archive/2026-06-01_signal_tracer_only/`）：

| 旧模块 | 当时功能 | 删除原因 |
|--------|---------|---------|
| `parse/` (parser.py) | 自实现 SV 解析器 | pyslang 已完全替代 |
| `debug/analyzers/cdc` | 跨时钟域分析 | 不在"信号追踪"目标内 |
| `debug/analyzers/multi_driver` | 多驱动检测 | 同上 |
| `debug/analyzers/uninitialized` | 未初始化检测 | 同上 |
| `debug/analyzers/xvalue` | X 值传播 | 同上 |
| `debug/analyzers/dangling_port` | 悬空端口 | 同上 |
| `debug/analyzers/reset_domain` | 复位域分析 | 同上 |
| `debug/analyzers/fsm_analyzer` | FSM 提取 | 同上 |
| `debug/analyzers/timed_path` | 时序路径 | 同上 |
| `debug/class_extractor` | 类提取 | 同上 |
| `debug/dependency/` | 依赖图 | 同上 |
| `debug/iospec` | IO 规格 | 同上 |
| `verify/` | 验证支持（约束/覆盖/FSM→SVA） | 同上 |
| `lint/` | Lint | 同上 |
| `query/` | 各类查询（clock_domain/signal_chain/timing_path） | 被 SignalTracer 内置查询替代 |
| `power/`, `area/`, `performance/` | 资源/功耗/性能估算 | 同上 |
| `regression/`, `reports/`, `viz/`, `apps/` | 报表/可视化/应用 | 同上 |
| `extractors/`, `scope/`, `semantic/` | 3-pass 架构 | 已被 SignalTracer 单 pass 替代 |
| `trace/` (旧) | 旧 trace 实现 | 被 signal_tracer 替代 |

如果未来需要这些功能，应作为独立项目而非本项目的一部分。

---

## 相关文档

- `TODO.md` - 当前开发路线图
- `TEST_PLAN.md` - 测试计划
- `tests/README.md` - 测试总览
- `archive/2026-06-01_signal_tracer_only/` - 重构前的完整历史代码
- `tests/_legacy/` - 重构前的旧测试
