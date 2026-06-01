# sv-trace

> SystemVerilog signal tracer — 给一个信号名，返回它在源码里的所有 driver / load，以及完整的上下文（文件、行号、scope 源码、时钟/复位、条件栈、端口连接）。

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![pyslang](https://img.shields.io/badge/pyslang-%3E%3D10.0-orange.svg)](https://github.com/MikePopoloski/slang)
[![Status](https://img.shields.io/badge/status-alpha-yellow.svg)]()

## 目标

**只做一件事：信号追踪 + 上下文召回，做到极致。**

不做：CDC 分析、多驱动检测、面积/功耗/性能估算、Lint、FSM 提取、约束分析、覆盖率建议、TB 复杂度评分、代码质量评分、依赖图、可视化……（详见 [TODO.md](TODO.md) 的"不做"章节）

## 安装

```bash
pip install sv-trace
# 或本地开发
pip install -e .
```

唯一依赖：`pyslang >= 10.0`

## 快速开始

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

print(f"=== Drivers of 'count' ===")
for d in result.drivers:
    print(f"  {d.source_expr} @ line {d.line}")
    print(f"    condition_stack: {d.condition_stack}")
    print(f"    scope_text: {d.scope_text.strip()[:80]}...")

print(f"\n=== Loads of 'count' (谁在读它) ===")
for load in result.loads:
    print(f"  {load.source_expr} @ line {load.line}")
```

输出：

```
=== Drivers of 'count' ===
  8'h00 @ line 9
    condition_stack: ['!rst_n']
    scope_text: always_ff @(posedge clk or negedge rst_n) begin if (!rst_n) count <= 8'h00;...
  count + data_in @ line 11
    condition_stack: ['!rst_n']
    scope_text: always_ff @(posedge clk or negedge rst_n) begin if (!rst_n) count <= 8'h00;...

=== Loads of 'count' (谁在读它) ===
  count @ line 11  # count + data_in 里读到自己
```

## 公开 API

```python
# 函数式
from signal_tracer import trace_signal, trace_signal_from_file
result = trace_signal("signal_name", sv_code, "file.sv")
result = trace_signal_from_file("signal_name", "path/to/file.sv")

# 类式
from signal_tracer import SignalTracer, SignalTracerApp
tracer = SignalTracer(sv_code, "file.sv").build()
result = tracer.trace("signal_name")  # 含跨模块追踪
```

每个 `result` 是 `TraceSummary`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `signal_name` | `str` | 查询的信号名 |
| `drivers` | `List[DriverTrace]` | 驱动列表（谁在写它） |
| `loads` | `List[LoadTrace]` | 负载列表（谁在读它） |
| `.get_clock_domains()` | `List[str]` | 涉及的时钟域 |
| `.get_driver_chain(max_depth=10)` | `List[str]` | 驱动链（递归上游） |

每个 `DriverTrace` / `LoadTrace` 包含：`file / line / char_offset / scope_kind / scope_text / scope_line_start+end / clock / reset / condition / condition_stack / is_port / port_direction / hierarchical_path / confidence`

完整字段说明见 [STRUCTURE.md](STRUCTURE.md) 的"公开 API"章节。

## 状态

| 指标 | 数据 |
|------|------|
| 公开 API 测试 | **13/13 通过** |
| Benchmark 覆盖 | 11/11 (0 warning, 0 exception) |
| 追踪示例 | 71 drivers + 89 loads 跨 12 个 .sv fixture |
| 版本 | alpha |

跑测试：

```bash
python -m pytest tests/unit/test_signal_tracer.py -v
```

## 项目结构

```
sv-trace/
├── src/
│   ├── __init__.py
│   ├── sv_manager.py                  # SV 文件加载、源码定位
│   └── signal_tracer/                 # 核心
│       ├── models.py                  # TraceResult / TraceSummary
│       ├── tracer.py                  # SignalTracer: 语义层 driver/load
│       ├── port_resolver.py           # PortResolver: 语法层端口连接
│       └── signal_tracer_app.py       # SignalTracerApp: 跨模块追踪
├── benchmarks/                        # 12 个 SV fixture
├── tests/
│   ├── unit/test_signal_tracer.py     # 公开 API 测试
│   ├── unit/trace/sv_cases/           # 50+ .sv fixture 语料库
│   ├── targeted/  advanced/  testbed/ # .sv fixture
│   ├── _legacy/                       # 重构前失效测试（归档）
│   └── README.md
├── archive/                           # 旧 src/ 完整代码
├── STRUCTURE.md                       # 详细架构 / API 字段表
├── TODO.md                            # 路线图（M0-M5）
├── TEST_PLAN.md                       # 测试计划
├── pyproject.toml
└── pytest.ini
```

## 路线图

- ✅ **M0** P0 bug 修复（TimedStatement 路径处理）— 2026-06-01
- ✅ **M1** 公开 API 测试覆盖（13/13 通过）
- 🔄 **M2** 上下文召回做厚（clock/reset 提取，ContextBundle 数据结构）
- 📋 **M3** 跨模块追踪做实（单文件 → 文件树）
- 📋 **M4** 真实项目验证（OpenTitan, XiangShan）
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
- [TODO.md](TODO.md) — 当前路线图 / 历史 / 不做的功能
- [TEST_PLAN.md](TEST_PLAN.md) — 测试计划 / 状态
- [tests/README.md](tests/README.md) — 测试总览

## License

MIT
