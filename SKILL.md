---
name: sv-trace
description: SystemVerilog 信号追踪器 (signal tracer) — 给一个 SV 信号名, 返回该信号在源码中的所有 driver (驱动) 和 load (负载), 以及完整上下文 (文件、行号、scope 源码、时钟/复位、条件栈、层次路径)。每个 trace 都带**可证伪的代码证据链 (M5.1)**: 读回实际文件验证 source_expr/signal_name 真在该行, 输出 credibility_score (0-1) 和 is_verified 标记, 让 LLM/用户能反查。基于 pyslang 语义层分析, 支持多文件项目、Interface/Modport、跨模块层次路径。Use when (1) 需要在 RTL 源码中追踪某个信号的所有驱动/读取位置, (2) 调试"这个信号在哪里被赋值"或"谁在读这个信号", (3) 自动生成信号的 driver/load 列表喂给 LLM, (4) 在大型 SV 项目 (OpenTitan 等) 中跨模块追踪信号, (5) 验证多驱动冲突 (always_ff 多次写同一信号) — 看到冲突 + 看到冲突的真凭实据, (7) 顺藤摸瓜查 driver 链 — 链上每跳都带 evidence (credibility), (8) 查谁读了某信号 (loads) — 每条 load 都带 evidence, (9) 顺藤摸瓜查 load 链 — 链上每跳都带 evidence (与 driver 链对称), (10) 一次 dump 整个链为 JSON — 含 summary, 喂 LLM 友好, (6) 需要 trace 的"可信度"量化 - 不光看 trace 还要看 trace 有没有真。
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
# 多驱动检测 (M1.5 + M5.1b) - 默认 verify=True, 自动带 evidence
multi = t.find_multi_drivers()
# → Dict[signal_name, List[TraceResult]]
# 每个 driver 的 _evidence_override 已自动填充 (看到冲突 + 真凭实据)
for sig, drivers in multi.items():
    for d in drivers:
        ctx = d.to_context()  # 立刻拿带 credibility 的 context
        d_dict = ctx.to_dict()
        print(f"  {sig} driver @ {d.file.split('/')[-1]}:{d.line}")
        print(f"    credibility={d_dict['credibility_score']}  verified={d_dict['is_verified']}")
        print(f"    snippet: {d_dict['evidence_snippet']}")
# 不需要 evidence: t.find_multi_drivers(verify=False)

# 驱动数
count = t.get_driver_count('data_out')

# 递归查上游 driver 链 (M1.5, 带 cycle detection; M5.1c 默认 verify=True 自动带 evidence)
chain = t.get_driver_chain('data_out', max_depth=10)
# 链上每跳的 _evidence_override 已自动填充, 可 d.to_context() 立刻拿到带 credibility 的 context
# 不需要 evidence: t.get_driver_chain('data_out', verify=False)

# 顺藤摸瓜查下游 load 链 (M5.1e) - 与 driver chain 完全对称
load_chain = t.get_load_chain('data_in', max_depth=10)
# 查"谁读了这个 signal, 又被谁读", 链上每条 load 也自动带 evidence
# 不需要 evidence: t.get_load_chain('data_in', verify=False)

# M5.1f: 一次 dump 整个 chain 为 dict (含 summary, LLM 友好)
dump = t.dump_driver_chain('tx_enable')  # 默认含 hops + context_window
# dump 是 1 个 dict: {signal_name, direction, hops[...], summary{avg, min, cross_files, ...}}
# summary 让 LLM 5 个数字就判断全链质量
summary_only = t.dump_driver_chain('tx_enable', summary_only=True)  # 只要 summary
# 也可 dump_load_chain (下游链)
load_dump = t.dump_load_chain('reg2hw')

# 打包成 LLM-ready 上下文 (M2)
for ctx in result.to_contexts():
    print(ctx.summary())          # 一行可读
    print(json.dumps(ctx.to_dict()))  # 完整字段 JSON

# M5.1d: trace() 默认 verify=True, drivers 和 loads 都自动带 evidence
result = t.trace('tx_enable')  # verify=True 默认
for d in result.drivers:
    d_dict = d.to_context().to_dict()
    print(f"  DRV {d.signal_name}: credibility={d_dict['credibility_score']}  snippet={d_dict['evidence_snippet']}")
for l in result.loads:
    l_dict = l.to_context().to_dict()
    print(f"  LD  {l.signal_name}: credibilidad={l_dict['credibility_score']}  snippet={l_dict['evidence_snippet']}")

# 也可单独用 trace_drivers / trace_loads (M5.1d)
drivers = t.trace_drivers('tx_enable')  # 默认 verify=True
loads = t.trace_loads('reg2hw')       # 默认 verify=True
# 不需要 evidence: t.trace_loads('reg2hw', verify=False)

# M5.1: 交叉验证 - 读回文件确认 trace 真的对
result = t.trace_verified('tx_enable')
for ctx in result.to_contexts():
    d = ctx.to_dict()
    print(f"  credibility={d['credibility_score']:.2f}  is_verified={d['is_verified']}")
    print(f"  snippet: {d['evidence_snippet']}")
    print(ctx.code_evidence.to_evidence_string())  # LLM-friendly 多行格式

# 或手动构建 evidence
from signal_tracer.models import build_evidence
ev = build_evidence(file='test.sv', line=10, source_expr='data', signal_name='q',
                    file_content=open('test.sv').read())
print(ev.to_evidence_string())
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

### 6. 代码证据链 (M5.1) - 让 trace 自证
**核心问题**: 之前 trace 只是元数据, "信不信由你"。M5.1 让每个 trace 都能"自证"。

```python
from signal_tracer import trace_signal
result = trace_signal('count', sv_code, 'counter.sv')
for ctx in result.to_contexts(file_content=sv_code):  # 传 file_content 让 evidence 读回
    d = ctx.to_dict()
    print(f"  credibility={d['credibility_score']}  is_verified={d['is_verified']}")
    print(f"  snippet: {d['evidence_snippet']}")
    # 可读输出 (含上下 2 行):
    print(ctx.code_evidence.to_evidence_string())
```

输出:
```
  credibility=1.0  is_verified=True
  snippet: if (!rst_n) count <= 8'h00;
Evidence for always_ff @(posedge clk ...) @ counter.sv:9
  file_readable: True
  snippet: if (!rst_n) count <= 8'h00;
  matches: source_expr match: ✓, signal_name match: ✓
  credibility: 1.00/1.0 (VERIFIED)
     8 |     always_ff @(posedge clk or negedge rst_n) begin
     9 > if (!rst_n) count <= 8'h00;
    10 |         else        count <= count + data_in;
    11 |     end
```

**可信度评分** (0-1):
- `file_readable` (+0.2) — 文件能读
- `snippet_present` (+0.2) — line 存在
- `matches_source_expr` (+0.4) — 文本里真找到 source_expr
- `matches_signal_name` (+0.2) — 文本里真找到 signal_name

**SignalTracer 多文件项目**: 用 `trace_verified()` 自动用 in-memory 内容填充 evidence (避免磁盘 I/O):
```python
t = SignalTracer()
t.add_file('top.sv', top_code)
t.add_file('sub.sv', sub_code)
t.build()
result = t.trace_verified('top.u_sub.signal')  # 自动用 self._files 填充
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
- M5.1 evidence 的 `matches_source_expr` 是**字面量**子串匹配 — pyslang 文本格式
  (如 `count Add data_in`) 与源码 (`count + data_in`) 不完全一致时, 命中率会降。
  反映在 credibility_score 上, 不会静默接受。

## 测试 & 开发

```bash
cd ~/my_dv_proj/sv-trace

# 跑测试 (111/111 全部通过, 含 8 M5.1 + 4 M5.1b + 4 M5.1c + 7 M5.1d + 5 M5.1e + 9 M5.1f)
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

测试计数: 当前 **111/111** (2.33s)。低于此数 → 有回归; 高于此数 → 新测试已加。

## 详细参考 (按需加载)

- 详细架构与数据流图: `STRUCTURE.md`
- 完整路线图与未做事项: `TODO.md`
- 测试计划与各阶段测试数: `TEST_PLAN.md`
- 5 个使用示例 (可运行代码 + 输出): `README.md` "使用示例" 章节
- 17+ 种 SV 表达式覆盖清单: `README.md` "M4 能力覆盖" 章节
- **代码证据链 (M5.1) 详解**: `README.md` "使用示例" 例 6 + "M5.1 能力" 章节
- OpenTitan 验证数据: `README.md` "真实项目验证 (M4)" 章节
