---
name: sv-trace
description: SystemVerilog 信号追踪器 (signal tracer) — 给一个 SV 信号名, 返回该信号在源码中的所有 driver (驱动) 和 load (负载), 以及完整上下文 (文件、行号、scope 源码、时钟/复位、条件栈、层次路径)。基于 pyslang 语义层分析, 支持多文件项目、Interface/Modport、跨模块层次路径。Use when (1) 需要在 RTL 源码中追踪某个信号的所有驱动/读取位置, (2) 调试"这个信号在哪里被赋值"或"谁在读这个信号", (3) 自动生成信号的 driver/load 列表喂给 LLM, (4) 在大型 SV 项目 (OpenTitan 等) 中跨模块追踪信号, (5) 验证多驱动冲突 (always_ff 多次写同一信号)。
---

# sv-trace — SystemVerilog 信号追踪

## 项目位置

`~/my_dv_proj/sv-trace/` (本地路径, 不是 pip 包)

依赖: `pyslang >= 10.0` (唯一外部依赖, 已在 Python 环境中)

## 核心 API

### 函数式 (单文件)

```python
import sys
sys.path.insert(0, '~/my_dv_proj/sv-trace/src')

from signal_tracer import trace_signal

result = trace_signal("count", sv_code_str, "counter.sv")
# result.drivers: List[TraceResult] — 所有驱动
# result.loads:   List[TraceResult] — 所有读取
```

### 类式 (多文件 + 层次路径)

```python
from signal_tracer import SignalTracer

t = SignalTracer()
t.add_file('top.sv', top_code)
t.add_file('sub.sv', sub_code)
t.build()

# 智能匹配 4 步: 完全 → 数组前缀 → 后缀 → cross-module
result = t.trace('top.u_mid.signal_name')   # 全路径
result = t.trace('signal_name')             # 后缀匹配
```

## TraceResult 关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `signal_name` | str | 信号名 (如 `'count'`) |
| `source_expr` | str | 完整驱动表达式 (如 `"count + 1"` 或 `"reg2hw.ctrl.tx.q"`) |
| `source_signals` | List[str] | 表达式中读到的信号 |
| `file` / `line` | str / int | 驱动所在的实际文件 + 行号 (跨文件精确, M4 plan A 修复) |
| `scope_text` | str | 完整 always_ff/always_comb/assign 块源码 |
| `scope_kind` | ScopeKind | `ALWAYS_FF` / `ALWAYS_COMB` / `CONTINUOUS_ASSIGN` |
| `clock` / `reset` | str | 提取的时钟/复位信号 (M1.5) |
| `condition_stack` | List[str] | 嵌套条件栈 (如 `['!rst_n', 'data_in[7]']`) |
| `hierarchical_path` | str | 模块实例路径 (如 `'top.u_mid'`) |

## SignalTracer 实用方法

```python
# 多驱动检测 (M1.5)
multi = t.find_multi_drivers()
# → Dict[signal_name, List[TraceResult]]

# 驱动数
count = t.get_driver_count('data_out')

# 递归查上游 driver 链 (M1.5, 带 cycle detection)
chain = t.get_driver_chain('data_out', max_depth=10)

# 打包成 LLM-ready 上下文 (M2)
for ctx in result.to_contexts():
    print(ctx.summary())          # 一行可读
    print(json.dumps(ctx.to_dict()))  # 完整字段 JSON
```

## 使用模式 (5 个常见场景)

### 1. 时序信号追踪
每个 driver trace 都带 clock/reset/condition_stack:
```python
for d in trace_signal("count", sv, "counter.sv").drivers:
    print(f"  {d.source_expr} @ line {d.line} | clock={d.clock} reset={d.reset} cond={d.condition_stack}")
```

### 2. 多驱动检测 (竞态)
```python
for sig, drivers in t.find_multi_drivers().items():
    print(f"⚠ {sig} 被 {len(drivers)} 个 scope 驱动")
```

### 3. 递归 driver_chain
```python
chain = t.get_driver_chain("out")
# out -> c -> b -> a -> a -> b -> c -> out (含 cycle detection)
```

### 4. 跨模块层次路径
```python
t.trace('top.u_mid.signal_name')  # 全路径
t.trace('signal_name')             # 后缀匹配
```

### 5. Interface/Modport 信号 (M4.1)
支持 `interface bus_if; modport master(output valid);` 这种模式:
```python
# m.valid = 1'b1 这种 modport 访问, trace('valid') 能找到
# m.data[3:0] = 4'hA 这种 modport + bit select 也能
```

## 何时使用

- **用 sv-trace**: 需要在 SV 源码中"追踪信号去向", 调试 RTL bug, 验证 LLM 写的 SV 行为
- **不要用 sv-trace**: CDC 分析、Lint、面积/功耗估算、FSM 提取、约束分析、覆盖率建议 — 这些是 lint/synthesis/verification 工具, 不在本项目范围 (见 README "不做" 章节)

## 已验证 OpenTitan 模块 (M4)

全部 0 warning + 0 empty driver:

| 模块 | 文件 | drivers | 涵盖的 SV 特性 |
|------|------|---------|---------------|
| uart | 6 | 418 | reg2hw.* 字段访问 |
| spi_device | 19 | 3,229 | Streaming concat `{<<8{...}}` |
| dma | 4 | 401 | `inside` 集合 |
| i2c | 10 | 1,235 | |
| aes | 40 | 24,065 | StructuredAssignmentPattern (大模块) |
| hmac | 4 | 870 | `assert property` (SVA 跳过) |

总计 **30,218 drivers, 0 warning, 0 empty**。

## 已知限制

- modport direction (input/output) 区分 driver/load 尚未实现 (现在都被当 driver)
- 不支持 virtual interface
- 不支持 Clocking block / Property/Sequence 内部
- 不支持 System task (`$cast`, `$readmemh`) 中的信号

## 测试 & 开发

```bash
cd ~/my_dv_proj/sv-trace

# 跑测试 (74/74 全部通过)
python -m pytest tests/unit/test_signal_tracer.py -v

# 跑 OpenTitan 验证
python3 -c "
import sys; sys.path.insert(0, 'src')
from signal_tracer import SignalTracer
t = SignalTracer()
for f in ['uart.sv', 'uart_core.sv', 'uart_tx.sv', 'uart_rx.sv', 'uart_reg_pkg.sv', 'uart_reg_top.sv']:
    t.add_file('/Users/fundou/my_dv_proj/opentitan/hw/ip/uart/rtl/' + f, open('/Users/fundou/my_dv_proj/opentitan/hw/ip/uart/rtl/' + f).read())
t.build()
print(f'uart: {sum(len(lst) for lst in t._drivers.values())} drivers')
"

# 手动测试新模块 (多文件)
python3 -c "
import sys; sys.path.insert(0, 'src')
from signal_tracer import SignalTracer
# ... 用户代码
"
```

## 调用方式 (在 agent 工作流中)

最常见的 4 种 agent 调用:

1. **静态分析 RTL 行为**: 用户给出 SV 代码片段, 问"这个信号被谁驱动", 跑 `trace_signal`
2. **调试未知代码**: 给定 OpenTitan 路径, 问"中断信号怎么来的", 跑 `SignalTracer` + `trace('intr_*')`
3. **LLM 上下文召回**: 把 SV 代码传进来, 自动生成 driver/load 列表喂给 LLM
4. **多驱动验证**: 用户问"这个信号会不会多驱动", 跑 `find_multi_drivers()`

## 维护约定

本 SKILL.md 与项目同步维护 — **每次 commit 改动 tracer.py 公共 API 或新模块时**:
1. 更新 README.md (M 进度 + 测试计数)
2. 更新本 SKILL.md (如果 API 行为变了, 或新 SV 特性覆盖)
3. 跑 `python -m pytest tests/unit/test_signal_tracer.py` 确认 74/74 通过

测试计数: 当前 **74/74** (1.98s)。低于此数 → 有回归; 高于此数 → 新测试已加。

## 详细参考 (按需加载)

- 详细架构与数据流图: `STRUCTURE.md`
- 完整路线图与未做事项: `TODO.md`
- 测试计划与各阶段测试数: `TEST_PLAN.md`
- 5 个使用示例 (可运行代码 + 输出): `README.md` "使用示例" 章节
- 17+ 种 SV 表达式覆盖清单: `README.md` "M4 能力覆盖" 章节
- OpenTitan 验证数据: `README.md` "真实项目验证 (M4)" 章节
