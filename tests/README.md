# sv-trace 测试总览

> 更新时间: 2026-06-01 (M4 完成)

## 状态

**主测试 68/68 全部通过。** 2 个旧架构测试文件 (8 fail) 已迁移到 `tests/_legacy/`, 迁后 `pytest tests/` 干净通过。

```
$ python -m pytest tests/unit/test_signal_tracer.py -v
68 passed in 1.83s
```

## 主测试文件 (M0–M4)

- `tests/unit/test_signal_tracer.py` — **68 个测试全部通过**, 15 个 TestClass:
  - TestBasic (M0) — 基础 always_ff/comb/latch
  - TestControlFlow (M0) — if/else/case 条件
  - TestArrays (M0) — 1D/2D 数组索引
  - TestNoCrashes (M0) — 防护性: 不崩
  - TestTraceResultFields (M1) — 完整 TraceResult 字段
  - TestMultiDriver (M1.5) — 多驱动检测
  - TestClockResetExtraction (M1.5) — clock/reset 提取
  - TestDriverChain (M1.5) — driver_chain 递归
  - TestContextAccuracy (M2) — 上下文准确性
  - TestContextBundle (M2) — ContextBundle 数据结构
  - TestMultiFile (M3) — 多文件 + 层次路径
  - TestExpressionCoverage (M4) — 17 种 SV 表达式
  - TestContinuousAssignRobustness (M4) — InvalidExpression 防御
  - TestMultiFileLineFallback (M4) — 跨文件行号 (SourceManager)
  - TestScopeFilePath (M4) — TraceResult.file 精确
  - TestAdditionalExpressions (M4) — Streaming/Inside/MemberAccess+RangeSelect 嵌套

## 已迁移 _legacy

| 文件 | 原状态 | 迁移后位置 |
|------|--------|-----------|
| `tests/unit/test_real_projects.py` | 2 fail / 2 pass | → `tests/_legacy/unit/test_real_projects.py` |
| `tests/unit/sv_trace/test_all_tiers_extended.py` | 6 fail / 1 pass | → `tests/_legacy/unit/test_all_tiers_extended.py` |

迁移原因: 两个文件都引用 M3 重构前已删除的 `trace.DriverTracer` / `debug.constraint_parser_v2` 等旧架构模块。迁移后 `pytest tests/` 主测试 68/68 干净通过。

## 目录说明

| 路径 | 内容 | 是否维护 |
|------|------|---------|
| `tests/unit/test_signal_tracer.py` | 68 个测试 (M0–M4) | ✅ 维护 |
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

# 只跑主测试 (68 个)
python -m pytest tests/unit/test_signal_tracer.py -v

# 跑所有 (包括旧架构失败)
python -m pytest tests/ --ignore=tests/_legacy --ignore=tests/archive --ignore=tests/debug

# 跑所有 (含 _legacy, 8 fail)
python -m pytest tests/
