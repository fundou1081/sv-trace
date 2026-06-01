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
| 公开 API 测试 | **68/68 通过** |
| Benchmark 覆盖 | 11/11 (0 warning, 0 exception) |
| 跨文件 fixture | 3 文件 / 3 层 instance (`tests/fixtures/m3_hierarchical/`) |
| 真实项目验证 | ✅ OpenTitan 6 模块 (uart/spi_device/dma/i2c/aes/hmac) 0 warning 0 empty |
| 版本 | alpha |

跑测试：

```bash
python -m pytest tests/unit/test_signal_tracer.py -v
```

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

- 表达式: `MemberAccess` / `RangeSelect` / `ElementSelect` / `BinaryOp` / `UnaryOp` / `ConditionalOp` / `CastExpression` / `Call` / `Replication` / `Concatenation` / `Streaming` (`{<<8{x}}` / `{>>8{x}}`) / `Inside` / `UnbasedUnsizedIntegerLiteral` (`'0` / `'1`) / `StructuredAssignmentPattern` / `SimpleAssignmentPattern` / `LValueReference` / `DataType`
- 嵌套: 任意深度 MemberAccess (e.g. `reg2hw.ctrl.tx.q`) + 跨 RangeSelect (`reg2hw.val[BufferAw:0]`)
- 跨文件: 多 .sv 编译为同一 Compilation, 跨模块引用 + 层次路径 (`uart.uart_core.tx_enable`)
- 跨文件行号: `pyslang SourceManager.getLineNumber()` 走 SourceLocation.buffer 精准算行
- 跨文件 file path: 每个 ScopeInfo.file_path 走 SourceManager.getFileName() 拿到正确文件名
- SVA 跳过: `ConcurrentAssertionStatement` (assert property) 不产生 driver/load trace

**未支持 (边缘场景)**:

- 复杂 type system (interface/modport) — port_resolver 独立模块已实现语法层
- Clocking block / Property/Sequence 内部
- System task ($cast, $readmemh) 中的信号

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
│   ├── unit/test_signal_tracer.py     # 68 个公开 API 测试
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
- 📋 **M5** 极致优化（增量、并发、缓存）

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
- [tests/README.md](tests/README.md) — 测试总览

## License

MIT
