# sv-trace 测试计划

> 更新时间: 2026-06-01 (M4 完成)
> 当前状态: **68/68 公开 API 测试全部通过 (M0–M4)**

## 当前状态

| 指标 | 数据 |
|------|------|
| pytest 可发现 (主测试) | 68 个 test |
| **主测试通过** | **68/68 全部通过** |
| `.sv` fixture | 89 个 (在 `tests/targeted/`, `tests/unit/trace/sv_cases/` 等) |
| 跨文件 fixture | 3 文件 / 3 层 instance (`tests/fixtures/m3_hierarchical/`) |
| 真实项目验证 | OpenTitan 6 模块 (30,218 drivers 总计, 0 warning, 0 empty) |
| 归档测试 | 167 个失效 .py → `tests/_legacy/` |
| 旧架构测试 (需迁移) | 2 个文件, 8 fail / 3 pass |

## 现状详细

```
$ python -m pytest tests/unit/test_signal_tracer.py -v
68 passed in 1.83s
```

15 个 TestClass 覆盖 M0–M4:
- M0: TestBasic, TestControlFlow, TestArrays, TestNoCrashes
- M1: TestTraceResultFields
- M1.5: TestMultiDriver, TestClockResetExtraction, TestDriverChain
- M2: TestContextAccuracy, TestContextBundle
- M3: TestMultiFile
- M4: TestExpressionCoverage, TestContinuousAssignRobustness, TestMultiFileLineFallback, TestScopeFilePath, TestAdditionalExpressions

### 旧架构测试 (待迁移 _legacy)

```
$ python -m pytest tests/unit/test_real_projects.py tests/unit/sv_trace/test_all_tiers_extended.py
2 failed, 2 passed, 1 warning
```

失败原因: 引用已删除的 M0 架构模块 (`trace.DriverTracer`, `debug.constraint_parser_v2`)。**不影响主测试**。建议下一步迁移到 `tests/_legacy/`。

## 已完成各阶段

### M0–M1 (13 个测试)
- 基础 always_ff/comb/latch
- 控制流 (if/else/case 条件)
- 数组 1D/2D
- TraceResult 完整字段

### M1.5 (20 个测试)
- 多驱动信号检测
- clock/reset 提取 (从 always @(posedge clk or negedge rst_n))
- driver_chain 递归查询 (带 cycle detection)

### M2 (13 个测试)
- line/scope_text 准确性
- ContextBundle frozen dataclass + to_dict()/summary()
- 全部 M1.5 + M1 + M0 独立验证

### M3 (9 个测试)
- 多文件 build + 跨模块引用
- 层次路径 (top.u_mid.u_leaf)
- 后缀匹配 (trace('data_out') 找跨 instance 所有同名信号)

### M4 (5 个测试)
- 表达式覆盖 (MemberAccess / RangeSelect / Replication / UnbasedUnsized / StructuredAssignmentPattern / Streaming / Inside / LValueReference)
- ContinuousAssign InvalidExpression 防御
- 跨文件行号 (SourceManager)
- TraceResult.file 精确 (ScopeInfo.file_path)
- 嵌套 MemberAccess+RangeSelect (reg2hw.val[BufferAw:0])

## M5 计划

- 性能基准 (50 文件 3 万行 trace < 100ms)
- 增量 build (单文件变更不重编译全部)
- 并发 build (多 .sv 同时解析)
- 缓存 (TraceSummary 跨 query 复用)

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
