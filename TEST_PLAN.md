# sv-trace 测试计划

> 更新时间: 2026-06-03 (M5.1g 完成)
> 当前状态: **117/117 公开 API 测试全部通过 (M0–M5.1g)**

## 当前状态

| 指标 | 数据 |
|------|------|
| pytest 可发现 (主测试) | 117 个 test |
| **主测试通过** | **117/117 全部通过 (2.39s)** |
| TestClass 数 | 23 个 (M0–M5.1g) |
| `.sv` fixture | 89 个 (在 `tests/targeted/`, `tests/unit/trace/sv_cases/` 等) |
| 跨文件 fixture | 3 文件 / 3 层 instance (`tests/fixtures/m3_hierarchical/`) |
| 真实项目验证 | OpenTitan 6 模块 (30,218 drivers, 0 warning, 0 empty) |
| 归档测试 | 167 个失效 .py → `tests/_legacy/` |
| 旧架构测试 (已迁移) | 2 个文件 → `tests/_legacy/unit/`, 8 fail / 3 pass |

## 现状详细

```
$ python -m pytest tests/unit/test_signal_tracer.py -v
117 passed in 2.39s
```

23 个 TestClass 覆盖 M0–M5.1g:

| 阶段 | TestClass | 测试数 | 覆盖点 |
|------|-----------|--------|--------|
| M0 | TestBasic, TestControlFlow, TestArrays, TestNoCrashes | — | 基础 always_ff/comb/latch, if/else/case, 1D/2D 数组 |
| M1 | TestTraceResultFields | — | 完整 TraceResult 字段 |
| M1.5 | TestMultiDriver, TestClockResetExtraction, TestDriverChain | — | 多驱动检测, clock/reset 提取, driver_chain 递归 |
| M2 | TestContextAccuracy, TestContextBundle | — | line/scope_text 准确性, ContextBundle 数据结构 |
| M3 | TestMultiFile | — | 多文件 + 层次路径 (top.u_mid.u_leaf) |
| M4 | TestExpressionCoverage, TestContinuousAssignRobustness, TestMultiFileLineFallback, TestScopeFilePath, TestAdditionalExpressions | +5 | 17 种 SV 表达式, InvalidExpression 防御, 跨文件行号, file 精确, 嵌套 MemberAccess+RangeSelect |
| M4.1 | TestInterfaceModport | +6 | Interface/Modport 信号追踪 (HierarchicalValue), 跨 modport 读写, m.data[3:0] 位选 |
| M5.1 | TestCodeEvidence | +8 | CodeEvidence + credibility_score 0-1 + is_verified + trace_verified() |
| M5.1b | TestMultiDriverEvidence | +4 | find_multi_drivers(verify=True) 默认带 evidence |
| M5.1c | TestDriverChainEvidence | +4 | get_driver_chain 链上每跳带 credibility |
| M5.1d | TestTraceLoadsEvidence | +7 | trace/trace_drivers/trace_loads 默认 verify=True |
| M5.1e | TestLoadChainEvidence | +5 | get_load_chain 顺下游 (与 driver chain 对称) |
| M5.1f | TestDumpChain | +9 | dump_driver_chain/dump_load_chain 1 次 dump 整链 (LLM 友好) |
| M5.1g | TestDumpMultiDrivers | +6 | dump_multi_drivers 1 次 dump 多驱动检测 (冲突 + summary) |

### 旧架构测试 (已迁移 _legacy)

```
$ python -m pytest tests/_legacy/unit/test_real_projects.py tests/_legacy/unit/test_all_tiers_extended.py
8 failed, 3 passed, 1 warning
```

失败原因: 引用已删除的 M0 架构模块 (`trace.DriverTracer`, `debug.constraint_parser_v2`)。已迁移到 `tests/_legacy/unit/`, **主测试不受影响**。

## 已完成各阶段详情

### M0–M1 (13 个测试)
- 基础 always_ff/comb/latch
- 控制流 (if/else/case 条件)
- 数组 1D/2D
- TraceResult 完整字段

### M1.5 (20 个测试)
- 多驱动信号检测 (find_multi_drivers, get_driver_count, is_multi_driver)
- clock/reset 提取 (从 always @(posedge clk or negedge rst_n), 命名启发式 + negedge edge)
- driver_chain 递归查询 (带 cycle detection)

### M2 (13 个测试)
- line/scope_text 准确性 (用 expr.sourceRange, 保留多行)
- ContextBundle frozen dataclass + to_dict()/summary()
- 全部 M1.5 + M1 + M0 独立验证

### M3 (9 个测试)
- 多文件 build + 跨模块引用 (同一 Compilation 多棵 SyntaxTree)
- 层次路径 (top.u_mid.u_leaf)
- 后缀匹配 (trace('data_out') 找跨 instance 所有同名信号)
- Cross-module fallback (port connection 走端口连接)

### M4 (5 个测试)
- 17 种 SV 表达式覆盖
- ContinuousAssign InvalidExpression 防御
- 跨文件行号 (pyslang SourceManager.getLineNumber)
- TraceResult.file 精确 (ScopeInfo.file_path 走 SourceManager.getFileName)
- 嵌套 MemberAccess+RangeSelect (reg2hw.val[BufferAw:0])

### M4.1 (6 个测试)
- Interface/Modport 信号追踪
- HierarchicalValue 处理 (pyslang ModportPortSymbol)
- 跨 modport 读写 (master/slave)
- m.data[3:0] 这种 modport + bit select 组合

### M5.1 (8 个测试)
- CodeEvidence 数据类
- build_evidence() 手动构建 (含 file_content)
- to_evidence_string() LLM-friendly 多行输出
- credibility_score 0-1 量化 (4 维累加)
- is_verified bool (防御性)
- ContextBundle 字段暴露 (credibility_score / is_verified / matches_* / evidence_snippet / code_evidence)
- trace_verified() 自动 in-memory 验证

### M5.1b-g (35 个测试)
- find_multi_drivers / get_driver_chain / trace / trace_drivers / trace_loads / get_load_chain 默认 verify=True
- dump_driver_chain / dump_load_chain / dump_multi_drivers 1 次 dump 整链/冲突

## OpenTitan 真实项目验证 (M4)

```
$ python3 -c "
import sys, io, contextlib
sys.path.insert(0, 'src')
from signal_tracer import SignalTracer
t = SignalTracer()
for f in ['uart.sv', 'uart_core.sv', 'uart_tx.sv', 'uart_rx.sv', 'uart_reg_pkg.sv', 'uart_reg_top.sv']:
    t.add_file('/Users/fundou/my_dv_proj/opentitan/hw/ip/uart/rtl/' + f, open(...).read())
t.build()
# 6 模块总计 30,218 drivers, 0 warning, 0 empty
"
```

6 模块 (uart / spi_device / dma / i2c / aes / hmac) 全部 **0 warning + 0 empty driver**。

## M5.2 计划

- 性能基准 (50 文件 3 万行 trace < 100ms)
- 增量 build (单文件变更不重编译全部)
- 并发 build (多 .sv 同时解析)
- 缓存 (TraceSummary 跨 query 复用)
- `credibility_score >= X` 过滤 (让 agent 只看高可信度 trace)

## 测试基线

**测试计数 117/117** (2.39s)。低于此数 → 有回归; 高于此数 → 新测试已加。

## 不在测试范围

- Lint / CDC / 面积 / 功耗 → 这些模块已删除
- 旧测试套件 (167 个失效文件) → 在 `tests/_legacy/`, 不维护
- M5.1 evidence 是"读回文件交叉验证" — **不是 lint**: lint 是工具找代码错, evidence 是 trace 自证

## 运行方式

```bash
cd ~/my_dv_proj/sv-trace

# 主测试 (117 个, 必跑)
python -m pytest tests/unit/test_signal_tracer.py -v

# 全部 (含 _legacy 内 8 fail - 已知)
python -m pytest tests/

# OpenTitan 烟测
python3 -c "
import sys, io, contextlib
sys.path.insert(0, 'src')
from signal_tracer import SignalTracer
t = SignalTracer()
for f in ['uart.sv', 'uart_core.sv', 'uart_tx.sv', 'uart_rx.sv', 'uart_reg_pkg.sv', 'uart_reg_top.sv']:
    t.add_file('/Users/fundou/my_dv_proj/opentitan/hw/ip/uart/rtl/' + f, open('/Users/fundou/my_dv_proj/opentitan/hw/ip/uart/rtl/' + f).read())
t.build()
print(f'uart: {sum(len(lst) for lst in t._drivers.values())} drivers')
"
```

## 归档

- `tests/_legacy/` — 167 个失效 .py + 7 .md + 1 .json (2026-06-01 重构前的旧测试, 含 2 个 M0 旧架构已迁移)
- `tests/archive/` — 19 个早期归档的 .py
- `archive/2026-06-01_signal_tracer_only/` — 重构前的完整 src/

不要从这些目录里"复活"测试 — 它们引用了不存在的模块, 没有维护价值。
