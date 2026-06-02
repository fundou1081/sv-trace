# sv-trace 测试总览

> 更新时间: 2026-06-03 (M5.1g 完成)

## 状态

**主测试 117/117 全部通过** (2.39s)。2 个旧架构测试文件 (8 fail) 已迁移到 `tests/_legacy/`, 主测试 117/117 干净通过。

```
$ python -m pytest tests/unit/test_signal_tracer.py -v
117 passed in 2.39s
```

## 主测试文件 (M0–M5.1g)

- `tests/unit/test_signal_tracer.py` — **117 个测试全部通过**, 23 个 TestClass:

### M0 (基础)
- TestBasic — 基础 always_ff/comb/latch
- TestControlFlow — if/else/case 条件
- TestArrays — 1D/2D 数组索引
- TestNoCrashes — 防护性: 不崩

### M1 (字段)
- TestTraceResultFields — 完整 TraceResult 字段

### M1.5 (补强)
- TestMultiDriver — 多驱动检测
- TestClockResetExtraction — clock/reset 提取
- TestDriverChain — driver_chain 递归

### M2 (上下文)
- TestContextAccuracy — 上下文准确性
- TestContextBundle — ContextBundle 数据结构

### M3 (多文件)
- TestMultiFile — 多文件 + 层次路径

### M4 (真实项目, 17+ SV 表达式)
- TestExpressionCoverage — 17 种 SV 表达式
- TestContinuousAssignRobustness — InvalidExpression 防御
- TestMultiFileLineFallback — 跨文件行号 (SourceManager)
- TestScopeFilePath — TraceResult.file 精确
- TestAdditionalExpressions — Streaming/Inside/MemberAccess+RangeSelect 嵌套

### M4.1 (Interface/Modport)
- TestInterfaceModport (+6) — Interface/Modport 信号追踪 (HierarchicalValue)

### M5.1 (代码证据链)
- TestCodeEvidence (+8) — CodeEvidence + credibility_score 0-1 + is_verified + trace_verified()
- TestMultiDriverEvidence (+4) — find_multi_drivers(verify=True) 默认带 evidence
- TestDriverChainEvidence (+4) — get_driver_chain 链上每跳带 credibility
- TestTraceLoadsEvidence (+7) — trace/trace_drivers/trace_loads 默认 verify=True
- TestLoadChainEvidence (+5) — get_load_chain 顺下游
- TestDumpChain (+9) — dump_driver_chain/dump_load_chain 1 次 dump 整链
- TestDumpMultiDrivers (+6) — dump_multi_drivers 1 次 dump 多驱动检测

## 已迁移 _legacy

| 文件 | 原状态 | 迁移后位置 |
|------|--------|-----------|
| `tests/unit/test_real_projects.py` | 2 fail / 2 pass | → `tests/_legacy/unit/test_real_projects.py` |
| `tests/unit/sv_trace/test_all_tiers_extended.py` | 6 fail / 1 pass | → `tests/_legacy/unit/test_all_tiers_extended.py` |

迁移原因: 两个文件都引用 M3 重构前已删除的 `trace.DriverTracer` / `debug.constraint_parser_v2` 等旧架构模块。**主测试 117/117 干净通过**。

## 目录说明

| 路径 | 内容 | 是否维护 |
|------|------|---------|
| `tests/unit/test_signal_tracer.py` | **117 个测试 (M0–M5.1g)** | ✅ 维护 |
| `tests/_legacy/unit/test_real_projects.py` | 11 个 test (8 fail, 已迁移) | 🗄️ 归档 |
| `tests/_legacy/unit/test_all_tiers_extended.py` | 7 个 test (已迁移) | 🗄️ 归档 |
| `tests/targeted/` | 40 个 .sv fixture | 📦 保留 |
| `tests/unit/trace/sv_cases/` | 50+ 个 .sv fixture | 📦 保留 |
| `tests/advanced/test.sv` | 1 个 .sv | 📦 保留 |
| `tests/testbed/cpu.sv` | 1 个 .sv | 📦 保留 |
| `tests/_legacy/` | 167 个失效 .py | 🗄️ 归档 |
| `tests/archive/` | 19 个早期失效 .py | 🗄️ 归档 |
| `tests/fixtures/m3_hierarchical/` | 3 文件 / 3 层 instance fixture | ✅ 维护 |
| `benchmarks/` | 12 个精心设计的 .sv | ✅ 手动验证 |

## 跑测试

```bash
cd ~/my_dv_proj/sv-trace

# 只跑主测试 (117 个)
python -m pytest tests/unit/test_signal_tracer.py -v

# 跑所有 (排除 _legacy/archive)
python -m pytest tests/ --ignore=tests/_legacy --ignore=tests/archive --ignore=tests/debug

# 跑所有 (含 _legacy 内 8 fail - 已知, 不影响主测试)
python -m pytest tests/
```

## OpenTitan 真实项目烟测

```python
import sys, io, contextlib
sys.path.insert(0, 'src')
from signal_tracer import SignalTracer

uart_dir = '/Users/fundou/my_dv_proj/opentitan/hw/ip/uart/rtl/'
files = {n: open(uart_dir + n).read() for n in
         ['uart.sv', 'uart_core.sv', 'uart_tx.sv', 'uart_rx.sv', 'uart_reg_pkg.sv', 'uart_reg_top.sv']}
t = SignalTracer()
for n, c in files.items():
    t.add_file(uart_dir + n, c)
with contextlib.redirect_stderr(io.StringIO()):
    t.build()

# 全部 6 模块总计 30,218 drivers, 0 warning, 0 empty
dump = t.dump_multi_drivers()
print(f"conflicts: {dump['summary']['total_conflict_signals']}")
print(f"avg_credibility: {dump['summary']['avg_credibility']}")
print(f"cross_files: {dump['summary']['cross_files']}")

# 拿整链
chain_dump = t.dump_driver_chain('allzero_cnt_q')
print(f"driver chain: {chain_dump['summary']['total_hops']} hops, "
      f"avg_credibility={chain_dump['summary']['avg_credibility']}")
```

## 测试基线

**测试计数 117/117** (2.39s)。低于此数 → 有回归; 高于此数 → 新测试已加。

## 详细参考

- [TEST_PLAN.md](../TEST_PLAN.md) — 测试计划 (顶层, 含 M0–M5.1 详情)
- [STRUCTURE.md](../STRUCTURE.md) — 项目结构 + evidence 架构图
- [TODO.md](../TODO.md) — 路线图 (M0–M5.1 全部 ✅)
- [SKILL.md](../SKILL.md) — Agent 集成指南
