# sv-trace 测试计划

> 更新时间: 2026-06-01
> 当前真实状态: **2 个测试文件，11 个 test 函数，0 个有意义通过**

## 当前状态

| 指标 | 数据 |
|------|------|
| pytest 可发现 | 11 个 test |
| 真正通过 | 0 个（3 个无关纯 parse 测试，1 个 warning，7 个 fail） |
| 失败原因 | 全部是 `ModuleNotFoundError: No module named 'debug' / 'extractors' / ...`，因为它们还在调用 2026-06-01 已删除的旧模块 |
| `.sv` fixture | 89 个（在 `tests/targeted/`, `tests/unit/trace/sv_cases/` 等） |
| 归档测试 | 167 个失效 .py → `tests/_legacy/` |

## 现状详细

```
$ python -m pytest tests/ -v --collect-only
ERROR tests/unit/test_real_projects.py::TestTinyGPU::test_drive_load_tracing
ERROR tests/unit/test_real_projects.py::TestConstraintAnalysis::test_constraint_parsing
... (7 errors total)
collected 11 items

$ python -m pytest tests/ -v
8 failed, 3 passed, 1 warning
```

3 个"通过"里：
- 1 个返回 `True` 而非 assert → pytest warning
- 2 个纯 parse 烟测（`test_parse_all_files` / `test_parse_verilog`），不验证追踪功能

**结论**：当前**公开 API `trace_signal` 没有任何测试覆盖**。

## 测试目标（M1 阶段）

10 个 pytest 覆盖 `trace_signal` 公开 API：

| # | 场景 | 关键断言 |
|---|------|---------|
| 1 | 基础 always_ff 寄存器 | `data_out` 至少 1 个 driver；line 在 always_ff 内 |
| 2 | 基础 always_comb | `result` 至少 1 个 driver |
| 3 | continuous assign | `wire x` 至少 1 个 driver，scope_kind == CONTINUOUS_ASSIGN |
| 4 | 嵌套 if 条件栈 | `data_out` driver 的 `condition_stack` 含 `['!rst_n', 'enable']`（或类似） |
| 5 | case 语句 | `state` 在 case(...) 表达式里出现，作为 load |
| 6 | 数组位选 | `data[7:0]` 通过 prefix 匹配或结构化识别找到 driver |
| 7 | 跨 scope 的 load | `data_in` 在多个 always 块中被读取，每个都返回 1 个 load |
| 8 | 时钟/复位提取 | `always_ff @(posedge clk or negedge rst_n)` → driver 的 `clock == 'clk'`, `reset == 'rst_n'` |
| 9 | driver_chain 递归 | `get_driver_chain('data_out')` 至少包含 `data_in` |
| 10 | 端到端 fixture | 用 `benchmarks/01_basic_registers.sv`，跑 `trace_signal('data_out')` 不抛异常 |

## 后续阶段（M2-M4）

- **M2**：context bundle 字段填充率测试（每行代码每个字段不能是空字符串）
- **M3**：跨模块 fixture（3-4 文件层级 SV）
- **M4**：真实项目烟测（OpenTitan 5 模块、XiangShan 1 模块）
- **M5**：性能基准（50 文件 3 万行 trace < 100ms）

## 不在测试范围

- Lint / CDC / 多驱动 / 面积 / 功耗 → 这些模块已删除
- 旧测试套件（167 个失效文件）→ 在 `tests/_legacy/`，不维护

## 运行方式

```bash
# 当前（2026-06-01 后）
python -m pytest tests/                    # 0 个真通过
python -m pytest tests/unit/sv_trace/      # 跑 test_all_tiers_extended.py (也基本 fail)

# M1 后（目标）
python -m pytest tests/unit/               # 10 个真通过
python -m pytest --tb=short                # 失败时只显示关键栈
```

## 归档

- `tests/_legacy/` — 167 个失效 .py + 7 .md + 1 .json（2026-06-01 重构前的旧测试）
- `tests/archive/` — 19 个早期归档的 .py
- `archive/2026-06-01_signal_tracer_only/` — 重构前的完整 src/

不要从这些目录里"复活"测试 — 它们引用了不存在的模块，没有维护价值。
