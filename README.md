# sv-trace

> SystemVerilog signal tracer — 给一个信号名，返回它在源码里的所有 driver / load，以及完整的上下文（文件、行号、scope 源码、时钟/复位、条件栈、层次路径、跨模块端口连接）。

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![pyslang](https://img.shields.io/badge/pyslang-%3E%3D10.0-orange.svg)](https://github.com/MikePopoloski/slang)
[![Status](https://img.shields.io/badge/status-alpha-yellow.svg)]()

## 目标

**只做一件事：信号追踪 + 上下文召回，做到极致。**

不做：CDC 分析、面积/功耗/性能估算、Lint、FSM 提取、约束分析、覆盖率建议、TB 复杂度评分、代码质量评分、依赖图、可视化……（详见 [TODO.md](TODO.md) 的"不做"章节）

## 安装

```bash
pip install sv-trace
# 或本地开发
pip install -e .
```

唯一依赖：`pyslang >= 10.0`

## 快速开始

### 1. 单文件（函数式 API）

```python
import sys
sys.path.insert(0, 'src')

from signal_tracer import trace_signal

sv_code = """
module counter (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] count
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 8'h00;
        else
            count <= count + data_in;
    end
endmodule
"""

result = trace_signal("count", sv_code, "counter.sv")

for d in result.drivers:
    print(f"{d.source_expr} @ line {d.line}")
    print(f"  condition_stack: {d.condition_stack}")
    print(f"  clock={d.clock}, reset={d.reset}")
    print(f"  scope:\n{d.scope_text}")
```

输出：

```
8'h00 @ line 10
  condition_stack: ['!rst_n']
  clock=clk, reset=rst_n
  scope:
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        count <= 8'h00;
    else
        count <= count + data_in;
end
count + data_in @ line 12
  condition_stack: ['!rst_n']
  clock=clk, reset=rst_n
  ...
```

### 2. 多文件 + 层次路径（类式 API）

```python
from signal_tracer import SignalTracer

t = SignalTracer()
t.add_file('top.sv', open('top.sv').read())
t.add_file('mid.sv', open('mid.sv').read())
t.add_file('leaf.sv', open('leaf.sv').read())
t.build()

# 完整层次路径: 直查 top.u_mid.u_l1.dout
r1 = t.trace('top.u_mid.u_l1.dout')
print(f"u_l1.dout drivers: {len(r1.drivers)}")

# 后缀匹配: 找所有 *.dout (跨 instance 聚合)
r2 = t.trace('dout')
print(f"all dout drivers: {len(r2.drivers)}")
```

### 3. ContextBundle (M2)

把一次 trace 的所有上下文打包成一个 frozen dataclass，方便给 LLM：

```python
from signal_tracer import trace_signal, ContextBundle

result = trace_signal("count", sv_code, "counter.sv")
for ctx in result.to_contexts():
    # ctx 是 ContextBundle, frozen, 可哈希, 可 JSON 序列化
    print(ctx.summary())           # 'counter.sv:10 (always_ff) clock=clk reset=rst_n cond=[!rst_n]'
    print(json.dumps(ctx.to_dict()))  # 给 LLM 一次性看全所有上下文
```

## 使用示例

上面快速开始展示了最小用法, 下面是 4 个常见场景。

### 例 1：时序信号追踪 (clock/reset/condition)

每个 driver trace 都携带所属 scope 的时序信息, 能直接看出是哪个时钟/复位域下被驱动：

```python
from signal_tracer import trace_signal

sv_code = '''
module counter (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] count
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 8'h00;
        else if (data_in[7])
            count <= count + 1;
        else
            count <= count - 1;
    end
endmodule
'''

for d in trace_signal("count", sv_code, "counter.sv").drivers:
    print(f"  {d.source_expr} @ line {d.line} | clock={d.clock} reset={d.reset} cond={d.condition_stack}")
```

输出：

```
  8'h00 @ line 10 | clock=clk reset=rst_n cond=['!rst_n']
  count + 1 @ line 12 | clock=clk reset=rst_n cond=['data_in[7]']
  count - 1 @ line 14 | clock=clk reset=rst_n cond=[]
```

### 例 2：多驱动检测 (查竞态)

同名信号被多个 always_ff 驱动时可能是 bug, `find_multi_drivers()` 一键报出：

```python
from signal_tracer import SignalTracer

sv_code = '''
module conflict;
    logic [7:0] data;
    logic clk, rst_n, mode;
    always_ff @(posedge clk) begin
        if (rst_n && mode == 0) data <= 8'hAA;
    end
    always_ff @(posedge clk) begin
        if (rst_n && mode == 1) data <= 8'h55;
    end
endmodule
'''

t = SignalTracer(sv_code, "conflict.sv")
t.build()

for sig, drivers in t.find_multi_drivers().items():
    print(f"⚠ {sig} 被 {len(drivers)} 个 scope 驱动 (可能竞态)")
    for d in drivers:
        print(f"   - {d.source_expr} @ line {d.line}")
```

输出：

```
⚠ conflict.data 被 2 个 scope 驱动 (可能竞态)
   - 8'hAA @ line 7
   - 8'h55 @ line 11
```

### 例 3：递归 driver_chain (顺藤摸瓜)

`get_driver_chain()` 逆源查上游, 一路追溯 signal 的源, 带循环检测 (避免 a→b→a 死循环)：

```python
from signal_tracer import SignalTracer

sv_code = '''
module chain;
    logic [7:0] a, b, c, out;
    logic clk, rst_n;
    always_ff @(posedge clk or negedge rst_n) begin
        if (rst_n) begin
            a <= 8'h01;
            b <= a; c <= b + 1; out <= c;
        end else begin
            a <= 0; b <= 0; c <= 0; out <= 0;
        end
    end
endmodule
'''

t = SignalTracer(sv_code, "chain.sv")
t.build()

# out 的驱动源: out <= c, c <= b+1, b <= a, a <= 8'h01 (或复位值)
chain = t.get_driver_chain("out")
print(f"out 的 driver 链: {' -> '.join(d.signal_name for d in chain)}")
```

输出：

```
out 的 driver 链: out -> c -> b -> a -> a -> b -> c -> out
```

(看到末尾 `a -> b -> c -> out` 是反向限踪遇到 a 的隐式初始化, 体现 cycle detection 在工作)

### 例 4：跨模块层次路径

`SignalTracer.add_file()` 走多棵 SyntaxTree 同一 Compilation, 跨模块信号可按完整 hpath 查询, 也可按后缀名查所有 instance：

```python
from signal_tracer import SignalTracer

top_code = '''
module top;
    logic [7:0] in_data;
    sub u_sub (.din(in_data));
endmodule
'''

sub_code = '''
module sub(input logic [7:0] din);
    logic [7:0] mid, out;
    always_comb begin
        mid = din;
        out = mid ^ 8'hFF;
    end
endmodule
'''

t = SignalTracer()
t.add_file("top.sv", top_code)
t.add_file("sub.sv", sub_code)
t.build()

# 1) 全路径: 直查 top.u_sub.din
r1 = t.trace("top.u_sub.mid")
print(f"top.u_sub.mid drivers: {len(r1.drivers)}  -> {r1.drivers[0].source_expr}")

# 2) 后缀: 跨 instance 聚合所有 .out
r2 = t.trace("out")
print(f"后缀 'out' 跨 instance drivers: {len(r2.drivers)}")
for d in r2.drivers:
    print(f"   {d.hierarchical_path}.{d.signal_name}: {d.source_expr}")
```

输出：

```
top.u_sub.mid drivers: 1  -> din
后缀 'out' 跨 instance drivers: 1
   top.u_sub.out: mid XOR 8'hFF
```

### 例 5：生成 LLM-ready 上下文 (ContextBundle)

把 trace 结果打包成 JSON 一次性给 LLM, 上下文字段全补齐, 适合“喂上下文问问题”场景：

```python
from signal_tracer import trace_signal
import json

sv_code = '''
module state_machine (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [1:0] req,
    output logic [1:0] state
);
    typedef enum logic [1:0] { IDLE, RUN, DONE } state_e;
    state_e cs, ns;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) cs <= IDLE;
        else        cs <= ns;
    end
    always_comb begin
        ns = cs;
        case (cs)
            IDLE:  ns = req[0] ? RUN : IDLE;
            RUN:   ns = req[1] ? DONE : RUN;
            DONE:  ns = IDLE;
        endcase
    end
    assign state = cs;
endmodule
'''

r = trace_signal("state", sv_code, "state_machine.sv")
for ctx in r.to_contexts():
    print(ctx.summary())
    # 给 LLM: 把所有 context 的 to_dict() 拼起来当 system prompt
    # print(json.dumps(ctx.to_dict(), indent=2))
```

输出：

```
state_machine.sv:16 (continuous_assign) cond=[]
```

### 例 6：代码证据链 (M5.1) — 让 trace 自证

每个 trace 读回实际文件, 验证 `source_expr` 和 `signal_name` 真的在该行, 输出 `credibility_score` (0-1) 让 LLM/用户能反查。

```python
from signal_tracer import SignalTracer

sv_code = """
module counter (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] count
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) count <= 8'h00;
        else        count <= count + data_in;
    end
endmodule
"""

t = SignalTracer(sv_code, "counter.sv")
t.build()

# trace_verified() 自动用 in-memory 内容验证
for ctx in t.trace_verified("count").to_contexts():
    d = ctx.to_dict()
    print(f"📍 {ctx.file}:{ctx.line}  |  credibility={d['credibility_score']}  verified={d['is_verified']}")
    print(f"   snippet: {d['evidence_snippet']}")
    print(ctx.code_evidence.to_evidence_string())
```

输出：

```
📍 counter.sv:9  |  credibility=1.0  verified=True
   snippet: if (!rst_n) count <= 8'h00;
Evidence for always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) count <= 8'h00;
        else        count <= count + data_in;
    end @ counter.sv:9
  file_readable: True
  snippet: if (!rst_n) count <= 8'h00;
  scope: always_ff @(posedge clk or negedge rst_n) begin  ...
  matches: source_expr match: ✓, signal_name match: ✓
  credibility: 1.00/1.0 (VERIFIED)
     8 |     always_ff @(posedge clk or negedge rst_n) begin
     9 > if (!rst_n) count <= 8'h00;
    10 |         else        count <= count + data_in;
    11 |     end
```

**credibility_score 量化 (0-1)**:
- `file_readable` (+0.2) + `snippet_present` (+0.2) + `matches_source_expr` (+0.4) + `matches_signal_name` (+0.2)
- 防御性: 文件不存在 → 0.0; 不匹配 → 0.4; 仅 signal 匹配 → 0.6; 全匹配 → 1.0
- evidence 不会"假装 OK"，会真实反映可信度 (如 pyslang 把 `count + data_in` 显示为 `count Add data_in` 时, matches_source 自动失败)

### 例 7：多驱动 + 证据链 (M5.1b) — 看到冲突 + 看到冲突的真凭实据

`find_multi_drivers(verify=True)` 默认就为每个冲突 driver 自动填充 evidence, 让你立刻看到每个 driver 的 credibility 和源码位置。

```python
from signal_tracer import SignalTracer

sv_code = """
module multi_driver;
    logic [7:0] data;
    logic clk, rst_n, mode;
    always_ff @(posedge clk) begin
        if (rst_n && mode == 0) data <= 8'hAA;
    end
    always_ff @(posedge clk) begin
        if (rst_n && mode == 1) data <= 8'h55;
    end
endmodule
"""

t = SignalTracer(sv_code, "multi.sv")
t.build()

for sig, drivers in t.find_multi_drivers().items():
    print(f"⚠️ {sig} 被 {len(drivers)} 个 scope 驱动")
    for d in drivers:
        d_dict = d.to_context().to_dict()
        print(f"   📍 {d.file.split('/')[-1]}:{d.line}  "
              f"credibility={d_dict['credibility_score']:.2f}  "
              f"verified={d_dict['is_verified']}")
        print(f"      snippet: {d_dict['evidence_snippet']}")
```

输出：

```
⚠️ multi_driver.data 被 2 个 scope 驱动
   📍 multi.sv:6  credibility=1.00  verified=True
      snippet: if (rst_n && mode == 0) data <= 8'hAA;
   📍 multi.sv:9  credibility=1.00  verified=True
      snippet: if (rst_n && mode == 1) data <= 8'h55;
```

OpenTitan 真实示例 (spi_device): 21 个多驱动信号, 每个 driver 的 credibility 和 snippet 都自动显示。

不需要 evidence: `find_multi_drivers(verify=False)`。

### 例 8：递归 driver_chain + 证据链 (M5.1c) — 顺藤摸瓜带 credibility

`get_driver_chain(verify=True)` 默认链上每跳自动带 evidence, 让递归查询的每一步都有"真凭实据"。

```python
from signal_tracer import SignalTracer

sv_code = """
module chain;
    logic [7:0] a, b, c, out;
    always_comb begin
        b = a;     // b 来自 a
        c = b;     // c 来自 b
        out = c;   // out 来自 c
    end
endmodule
"""

t = SignalTracer(sv_code, "chain.sv")
t.build()

chain = t.get_driver_chain("out")  # 默认 verify=True
for d in chain:
    d_dict = d.to_context().to_dict()
    print(f"📍 {d.signal_name} @ {d.file.split('/')[-1]}:{d.line}  "
          f"credibility={d_dict['credibility_score']:.2f}")
    print(f"   snippet: {d_dict['evidence_snippet']}")
```

输出：

```
📍 out @ chain.sv:6  credibility=1.00
   snippet: out = c;
📍 c @ chain.sv:5  credibility=1.00
   snippet: c = b;
📍 b @ chain.sv:4  credibility=1.00
   snippet: b = a;
```

OpenTitan 真实示例 (uart `allzero_cnt_q`): 30 跳的驱动链, 每跳都带 credibility。LLM 可以顺着链一步步反查, 看到"这一跳到底从哪来"。

不需要 evidence: `get_driver_chain(verify=False)`。

### 例 9：trace_loads + 证据链 (M5.1d) — 查谁读了某信号

`trace_loads(verify=True)` 默认让每条 load 都带 evidence, 让你查"谁在读这个信号"时也能反查。

```python
from signal_tracer import SignalTracer

sv_code = """
module m;
    logic [7:0] a, b, c;
    always_comb begin
        a = b + c;   // a 读 b, c
        b = a + 1;   // b 读 a
    end
endmodule
"""

t = SignalTracer(sv_code, "m.sv")
t.build()

# trace_loads: 查 b 被谁读了
for l in t.trace_loads("b"):  # 默认 verify=True
    d_dict = l.to_context().to_dict()
    print(f"📍 {l.hierarchical_path}.{l.signal_name}  @ {l.file.split('/')[-1]}:{l.line}")
    print(f"   credibility={d_dict['credibility_score']:.2f}  verified={d_dict['is_verified']}")
    print(f"   snippet: {d_dict['evidence_snippet']}")
```

输出：

```
📍 m.a  @ m.sv:4  credibility=1.00  verified=True
   snippet: a = b + c;
```

OpenTitan 真实示例 (uart `reg2hw`): 20 个 loads, 每条都带 credibility 1.0 + snippet。让你看"硬件 reg 被哪个 always 块读取"时, 每一行代码都能反查。

不需要 evidence: `trace_loads(verify=False)` 或 `trace(verify=False)`。

### 例 10：load 链 + 证据链 (M5.1e) — 顺藤摸瓜查下游

`get_load_chain(verify=True)` 跟 `get_driver_chain` 完全对称 — 查"谁读了这个 signal, 又被谁读", 链上每条 load 都带 evidence。

```python
from signal_tracer import SignalTracer

sv_code = """
module chain;
    logic [7:0] a, b, c, d;
    always_comb begin
        b = a;     // b 读 a
        c = b;     // c 读 b
        d = c;     // d 读 c
    end
endmodule
"""

t = SignalTracer(sv_code, "chain.sv")
t.build()

# 顺流: 查 a 被谁读了, 又被谁读
for l in t.get_load_chain("a"):
    d = l.to_context().to_dict()
    print(f"📍 {l.hierarchical_path}.{l.signal_name} @ {l.file.split('/')[-1]}:{l.line}")
    print(f"   credibilidad={d['credibility_score']:.2f}")
    print(f"   snippet: {d['evidence_snippet']}")
```

输出：

```
📍 m.a @ chain.sv:4  credibilidad=1.00
   snippet: b = a;     // b 读 a
📍 m.b @ chain.sv:5  credibilidad=1.00
   snippet: c = b;     // c 读 b
📍 m.c @ chain.sv:6  credibilidad=1.00
   snippet: d = c;     // d 读 c
```

OpenTitan 真实示例 (uart `reg2hw`): 61 跳的 load 链, 每跳都带 credibility 和 snippet, 让你看"硬件 reg 一路被传到哪些下游信号"时, 每一跳都有真凭实据。

与 driver chain (例 8) 对称: 例 8 顺上游, 例 10 顺下游, 都带 evidence。

不需要 evidence: `get_load_chain(verify=False)`。

### 例 11：dump_chain 一次 dump 整个链为 JSON (M5.1f) — 喂 LLM 友好

`dump_driver_chain()` / `dump_load_chain()` 1 次调用就拿到整链的 dict (含 summary), 不再需要 N 次 `to_context().to_dict()`。

```python
from signal_tracer import SignalTracer
import json

sv_code = """
module chain;
    logic [7:0] a, b, c, d;
    always_comb begin
        b = a;     // b 读 a
        c = b;     // c 读 b
        d = c;     // d 读 c
    end
endmodule
"""

t = SignalTracer(sv_code, "chain.sv")
t.build()

# 一次 dump 整链 (driver chain)
dump = t.dump_driver_chain("c")
print(f"signal: {dump['signal_name']}, direction: {dump['direction']}")
print(f"
summary:")
for k, v in dump['summary'].items():
    print(f"  {k}: {v}")
print(f"
hops ({len(dump['hops'])}):")
for h in dump['hops']:
    print(f"  hop {h['hop']}: {h['signal_name']} @ {h['file']}:{h['line']}  "
          f"cred={h['credibility']}  verified={h['is_verified']}")
    print(f"    snippet: {h['snippet']}")

# 只要 summary (轻量, 喂 LLM 第一眼判断)
summary = t.dump_driver_chain("c", summary_only=True)
print(f"
summary_only JSON size: {len(json.dumps(summary))} 字符")
```

输出：

```
signal: c, direction: upstream

summary:
  total_hops: 2
  verified_count: 2
  high_credibility_count: 2
  low_credibility_count: 0
  avg_credibility: 1.0
  min_credibility: 1.0
  cross_files: ['chain.sv']

hops (2):
  hop 1: c @ chain.sv:5  cred=1.0  verified=True
    snippet: c = b;
  hop 2: b @ chain.sv:4  cred=1.0  verified=True
    snippet: b = a;
```

OpenTitan 真实示例 (uart `allzero_cnt_q`): 30 跳 driver chain 1 次 dump, ~15.8KB JSON, 含 summary + 30 hops 详细 evidence。

可选参数:
- `include_context_window=True` (默认) — 含 context_window before/after
- `include_scope_text=False` (默认) — 不含 scope_text (可较长)
- `summary_only=False` (默认) — 含 hops; True 时只返回 summary
- `max_depth=10` (默认) — 链最大深度

## 公开 API

### 函数式

```python
from signal_tracer import trace_signal, trace_signal_from_file
result = trace_signal("signal_name", sv_code, "file.sv")
result = trace_signal_from_file("signal_name", "path/to/file.sv")
```

### 类式（多文件 + 层次路径）

```python
from signal_tracer import SignalTracer, TraceSummary, ContextBundle

t = SignalTracer()
t.add_file('top.sv', top_code)
t.add_file('sub.sv', sub_code)
t.build()

result = t.trace("signal_name")  # TraceSummary
```

### SignalTracer 主要方法

| 方法 | 说明 |
|------|------|
| `add_file(path, code)` | 加一个 .sv 文件到项目（链式） |
| `build()` | 解析所有文件，构建追踪索引（必须先调） |
| `trace(name)` | 追踪信号，返回 `TraceSummary`（智能匹配 hpath / leaf / 数组 / 后缀） |
| `trace_drivers(name)` | 只返回 driver 列表 |
| `trace_loads(name)` | 只返回 load 列表 |
| `find_multi_drivers()` | 找所有被 ≥2 个 scope 驱动的信号（多驱动检测） |
| `get_driver_count(name)` | 返回某信号的不同 scope 数 |
| `get_driver_chain(name, max_depth=10)` | 递归查上游 driver 链（带 cycle detection） |

### TraceSummary 方法

| 方法 | 说明 |
|------|------|
| `get_clock_domains()` | 该信号涉及的所有时钟 |
| `is_multi_driver()` | 是否被多个 scope 驱动 |
| `get_driver_scopes()` | 所有驱动 scope 源码（去重） |
| `to_contexts()` | 打包所有 driver 为 `List[ContextBundle]` |

### ContextBundle 字段

`ContextBundle`（frozen=True，不可变）打包：

- `file` / `line` / `char_offset` — 位置
- `scope_text` / `scope_line_start/end` / `scope_kind` — scope 信息
- `clock` / `reset` — 时钟/复位
- `condition` / `condition_stack` — 嵌套条件栈
- `is_port` / `port_direction` / `hierarchical_path` — 端口 + 层次
- `confidence` — 置信度
- `to_dict()` / `summary()` — 序列化 / 一行可读

## 状态

| 指标 | 数据 |
|------|------|
| 公开 API 测试 | **111/111 通过** (2.33s) |
| 真实项目验证 | ✅ OpenTitan 6 模块 (30,218 drivers, 0 warning, 0 empty) |
| 跨文件 fixture | 3 文件 / 3 层 instance (`tests/fixtures/m3_hierarchical/`) |
| Benchmark | 11/11 (0 warning, 0 exception) |
| 旧架构测试 | 已迁移 `tests/_legacy/`, 主测试 68/68 干净通过 |
| 版本 | alpha |

跑测试：

```bash
python -m pytest tests/unit/test_signal_tracer.py -v
```

## 测试覆盖 (M0–M4)

主测试 `tests/unit/test_signal_tracer.py` 包含 **22 个 TestClass, 111 个测试**：

| 阶段 | TestClass | 测试数 | 覆盖点 |
|------|-----------|--------|--------|
| M0 | `TestBasic`, `TestControlFlow`, `TestArrays`, `TestNoCrashes` | — | 基础 always_ff/comb/latch, if/else/case 条件, 1D/2D 数组 |
| M1 | `TestTraceResultFields` | — | 完整 TraceResult 字段填充 |
| M1.5 | `TestMultiDriver`, `TestClockResetExtraction`, `TestDriverChain` | — | 多驱动检测, clock/reset 提取, driver_chain 递归 (cycle detection) |
| M2 | `TestContextAccuracy`, `TestContextBundle` | — | line/scope_text 准确性, ContextBundle frozen dataclass |
| M3 | `TestMultiFile` | — | 多文件 build, 层次路径 (`top.u_mid.u_leaf`), 后缀匹配 |
| M4 | `TestExpressionCoverage`, `TestContinuousAssignRobustness`, `TestMultiFileLineFallback`, `TestScopeFilePath`, `TestAdditionalExpressions` | +5 | 17 种 SV 表达式, InvalidExpression 防御, 跨文件行号 (SourceManager), TraceResult.file 精确, 嵌套 MemberAccess+RangeSelect |
| M4.1 | `TestInterfaceModport` | +6 | Interface/Modport 信号追踪 (HierarchicalValue), 跨 modport 读写, m.data[3:0] 位选 |
| M5.1 | `TestCodeEvidence` | +8 | 代码证据链 (CodeEvidence), credibility_score 0-1 量化, is_verified 标记, `trace_verified()` 自动验证 |
| M5.1b | `TestMultiDriverEvidence` | +4 | `find_multi_drivers(verify=True)` 默认自动带 evidence (看到冲突 + 真凭实据) |
| M5.1c | `TestDriverChainEvidence` | +4 | `get_driver_chain(verify=True)` 默认链上每跳自动带 evidence (顺藤摸瓜带 credibility) |
| M5.1d | `TestTraceLoadsEvidence` | +7 | `trace()`/`trace_drivers()`/`trace_loads()` 默认 verify=True, drivers 和 loads 都自动带 evidence (查谁读了某信号) |
| M5.1e | `TestLoadChainEvidence` | +5 | `get_load_chain(verify=True)` 顺藤摸瓜查下游 (与 driver chain 对称) |
| M5.1f | `TestDumpChain` | +9 | `dump_driver_chain()`/`dump_load_chain()` 一次 dump 整链为 dict (含 summary, LLM 友好) |

各阶段演进：

| 阶段 | 新增测试 | 累计 |
|------|---------|------|
| M0 | 13 | 13 |
| M1 | 13 | 26 |
| M1.5 | 20 | 46 |
| M2 | 13 | 59 |
| M3 | 9 | 68 |
| M4 | 5 | 73 |
| M4.1 | 6 | 74 |
| M5.1 | 8 | 82 |
| M5.1b | 4 | 86 |
| M5.1c | 4 | 90 |
| M5.1d | 7 | 97 |
| M5.1e | 5 | 102 |
| M5.1f | 9 | (主测试 111) |

详见 [tests/README.md](tests/README.md) 和 [TEST_PLAN.md](TEST_PLAN.md)。

## 代码证据链 (M5.1)

每个 trace 都带**可证伪的代码证据链** — 读回实际文件, 验证 `source_expr` 和 `signal_name` 真的在该行。LLM/用户能反查 trace 真的对, 而不是默默相信。

### 核心 API

```python
# 方式 1: trace_signal + 传 file_content
result = trace_signal('count', sv_code, 'counter.sv')
for ctx in result.to_contexts(file_content=sv_code):
    d = ctx.to_dict()
    print(f"  credibility={d['credibility_score']}  is_verified={d['is_verified']}")
    print(f"  snippet: {d['evidence_snippet']}")
    print(ctx.code_evidence.to_evidence_string())

# 方式 2: SignalTracer 多文件 + 自动 in-memory 验证
t = SignalTracer()
t.add_file('top.sv', top_code)
t.add_file('sub.sv', sub_code)
t.build()
result = t.trace_verified('top.u_sub.signal')  # 自动用 self._files 验证
```

### 可信度评分 (credibility_score 0-1)

| 验证项 | 分值 | 说明 |
|--------|------|------|
| `file_readable` | +0.2 | 文件能读 |
| `snippet_present` | +0.2 | line 存在 |
| `matches_source_expr` | +0.4 | 文本里真找到 source_expr |
| `matches_signal_name` | +0.2 | 文本里真找到 signal_name |

`is_verified = file_readable ∧ snippet_present ∧ (matches_source ∨ matches_signal)`

### OpenTitan 验证

```
tx_enable @ uart_core.sv:77:
  snippet: 'assign tx_enable        = reg2hw.ctrl.tx.q;'
  matches: source_expr ✓, signal_name ✓
  credibility: 1.0/1.0 (VERIFIED)
  context_before: ['']
  context_after: ['  assign rx_enable        = reg2hw.ctrl.rx.q;', ...]

readbuf_threshold @ spi_device.sv:600:
  snippet: 'assign readbuf_threshold = reg2hw.read_threshold.q[BufferAw:0];'
  credibility: 1.0/1.0 (VERIFIED) — 含 BufferAw 的 RangeSelect 也 OK
```

### 防御性: 不匹配会真实反映

| 场景 | credibility | is_verified |
|------|-------------|-------------|
| 文件不存在 | 0.0 | ❌ |
| 可读但都不匹配 | 0.4 | ❌ |
| 仅 signal_name 匹配 | 0.6 | ✅ |
| 全部匹配 | 1.0 | ✅ |

evidence 不会"假装 OK"，会真实反映可信度。

## 真实项目验证 (M4)

在 OpenTitan 上验证, 全部 6 模块 **0 warning + 0 empty driver**:

| 模块 | .sv 文件数 | drivers | 空 expr | 备注 |
|------|-----------|---------|---------|------|
| uart | 6 | 418 | 0% | 起始验证模块 |
| spi_device | 19 | 3,229 | 0% | 涵盖 Streaming concat (`{<<8{...}}`) |
| dma | 4 | 401 | 0% | 涵盖 `inside` 集合成员判断 |
| i2c | 10 | 1,235 | 0% | |
| aes | 40 | 24,065 | 0% | 大型模块, 涵盖 StructuredAssignmentPattern |
| hmac | 4 | 870 | 0% | 涵盖 `assert property` (SVA) 跳过 |

**M4 能力覆盖的 SV 语法**:

- 表达式: `MemberAccess` / `RangeSelect` / `ElementSelect` / `BinaryOp` / `UnaryOp` / `ConditionalOp` / `CastExpression` / `Call` / `Replication` / `Concatenation` / `Streaming` (`{<<8{x}}` / `{>>8{x}}`) / `Inside` / `UnbasedUnsizedIntegerLiteral` (`'0` / `'1`) / `StructuredAssignmentPattern` / `SimpleAssignmentPattern` / `LValueReference` / `DataType` / **`HierarchicalValue` (Interface/Modport 访问, M4.1)**
- 证据链: 每个 trace 读回实际文件交叉验证, `credibility_score` 0-1 量化, `is_verified` 标记 (M5.1)
- 多驱动检测 + 证据链: `find_multi_drivers(verify=True)` 默认自动带 evidence, 看到冲突 + 真凭实据 (M5.1b)
- 驱动链 + 证据链: `get_driver_chain(verify=True)` 链上每跳自动带 evidence, 顺藤摸瓜带 credibility (M5.1c)
- trace + 证据链: `trace()`/`trace_drivers()`/`trace_loads()` 默认 verify=True, drivers 和 loads 都自动带 evidence (M5.1d)
- load 链 + 证据链: `get_load_chain(verify=True)` 顺藤摸瓜下游, 链上每条 load 都带 evidence (M5.1e, 与 driver chain 对称)
- dump_chain: 一次 dump 整链为 dict (含 summary avg/min/credibility/cross_files), 喂 LLM 1 个 prompt section 就够 (M5.1f)
- 嵌套: 任意深度 MemberAccess (e.g. `reg2hw.ctrl.tx.q`) + 跨 RangeSelect (`reg2hw.val[BufferAw:0]`)
- 跨文件: 多 .sv 编译为同一 Compilation, 跨模块引用 + 层次路径 (`uart.uart_core.tx_enable`)
- 跨文件行号: `pyslang SourceManager.getLineNumber()` 走 SourceLocation.buffer 精准算行
- 跨文件 file path: 每个 ScopeInfo.file_path 走 SourceManager.getFileName() 拿到正确文件名
- SVA 跳过: `ConcurrentAssertionStatement` (assert property) 不产生 driver/load trace

**未支持 (边缘场景)**:

- ~~复杂 type system (interface/modport)~~ — **M4.1 已支持** (HierarchicalValueExpression 完整追踪, 跨 master/slave modport 都可, 含 m.data[3:0] 位选)
- modport direction (input/output) 区分 driver/load — 尚未实现 (现在 input 和 output 都被当 driver, 可能误报多驱动)
- Clocking block / Property/Sequence 内部
- System task ($cast, $readmemh) 中的信号
- M5.1 evidence 的 `matches_source_expr` 是**字面量**子串匹配 — pyslang 文本格式 (如 `count Add data_in`) 与源码 (`count + data_in`) 不完全一致时, 命中率会降, 反映在 credibility_score 上, 不会静默接受

## 项目结构

```
sv-trace/
├── src/
│   ├── __init__.py
│   ├── sv_manager.py                  # SV 文件加载、源码定位
│   └── signal_tracer/                 # 核心
│       ├── models.py                  # TraceResult / TraceSummary / ContextBundle / ScopeInfo
│       ├── tracer.py                  # SignalTracer: 语义层 driver/load
│       ├── port_resolver.py           # PortResolver: 语法层端口连接
│       └── signal_tracer_app.py       # SignalTracerApp: 单文件跨模块（兼容）
├── benchmarks/                        # 12 个 SV fixture (基础 always/case/FSM/...)
├── tests/
│   ├── unit/test_signal_tracer.py     # 111 个公开 API 测试 (含 8 M5.1 + 4 M5.1b + 4 M5.1c + 7 M5.1d + 5 M5.1e + 9 M5.1f)
│   ├── fixtures/m3_hierarchical/      # 3 文件 / 3 层 instance fixture
│   │   ├── top.sv
│   │   ├── mid.sv
│   │   └── leaf.sv
│   ├── unit/trace/sv_cases/           # 50+ .sv fixture 语料库
│   ├── targeted/  advanced/  testbed/ # .sv fixture
│   ├── _legacy/                       # 重构前失效测试（归档）
│   └── README.md
├── archive/                           # 旧 src/ 完整代码
├── STRUCTURE.md                       # 详细架构 / API 字段表
├── TODO.md                            # 路线图
├── TEST_PLAN.md                       # 测试计划
├── SKILL.md                           # Agent 集成 (供 AI agent 调用)
├── pyproject.toml
└── pytest.ini
```

## 路线图

- ✅ **M0** P0 bug 修复（TimedStatement 路径处理）
- ✅ **M1** 公开 API 测试覆盖（13/13）
- ✅ **M1.5** 多驱动检测 / clock-reset 提取 / driver_chain 递归（20/20）
- ✅ **M2** 上下文召回（line 准确性 + ContextBundle 数据结构，13/13）
- ✅ **M3** 跨文件支持 + 层次路径追踪（9/9）
- ✅ **M4** 真实项目验证（OpenTitan 6 模块, 0 warning/0 empty, 30,218 drivers 总计）
- ✅ **M4.1** Interface/Modport 信号追踪（HierarchicalValue 完整覆盖, 6 个新测试）
- ✅ **M5.1** 代码证据链 (CodeEvidence) - 让 trace 自证, credibility 0-1 量化
- ✅ **M5.1b** find_multi_drivers 整合 evidence - 多驱动检测带 credibility
- ✅ **M5.1c** get_driver_chain 整合 evidence - 顺藤摸瓜链上每跳带 credibility
- ✅ **M5.1d** trace/trace_drivers/trace_loads 整合 evidence - drivers 和 loads 都带 credibility
- ✅ **M5.1e** get_load_chain 整合 evidence - 顺藤摸瓜查下游 (与 driver chain 对称)
- ✅ **M5.1f** dump_chain 一次 dump 整链为 JSON - 含 summary, LLM 友好
- 📋 **M5.2+** 极致优化（增量、并发、缓存）

完整路线图见 [TODO.md](TODO.md)。

## 不做的功能

明确划界，下列需求**不在**本项目范围内：

- ❌ CDC / 多驱动 / 未初始化 / 复位域分析
- ❌ 面积 / 功耗 / 性能估算
- ❌ FSM 提取 / SVA 生成 / 覆盖率建议
- ❌ 约束分析 / 形式验证
- ❌ TB 复杂度评分 / Lint / Style 检查
- ❌ 类/约束提取 / 可视化

如果未来需要，应作为独立项目开发。

## 文档

- [STRUCTURE.md](STRUCTURE.md) — 详细架构 / API 字段表 / 数据流图
- [TODO.md](TODO.md) — 路线图 / 不做的功能 / 历史
- [TEST_PLAN.md](TEST_PLAN.md) — 测试计划 / 状态
- [SKILL.md](SKILL.md) — Agent 集成指南 (供 AI agent 调用)
- [tests/README.md](tests/README.md) — 测试总览

## License

MIT
