# sv-trace 路线图

> 更新时间: 2026-06-01
> 项目目标: **只做信号追踪 + 上下文召回，做到极致**

## 当前状态

- ✅ 完成 2026-06-01 大幅精简：删除 16+ 子模块，src/ 仅剩 `signal_tracer` + `sv_manager`
- ✅ 文档同步：`STRUCTURE.md` / `TEST_PLAN.md` / `tests/README.md` 已重写
- ✅ 测试归档：167 个失效 .py 测试 + 7 .md + 1 .json 移到 `tests/_legacy/`
- ✅ stale egg-info 清理
- ❌ **核心 bug 已知**：`SignalTracer` 在最简 `always_ff` benchmark 上拿不到 driver（见下方 P0）
- ❌ 公开 API 暂无 pytest 覆盖（仅 2 个测试在跑，但都是间接用例）

## 关键 bug (P0)

**`src/signal_tracer/tracer.py:_process_block_body`** 漏处理 `TimedStatement → BlockStatement` 路径。

实测：在 `benchmarks/01_basic_registers.sv` 上：

```sv
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        data_out <= 8'h00;
    else
        data_out <= data_in;
end
```

调用 `trace_signal('data_out', code, '01.sv')` 返回 0 个 driver。控制台还输出 `WARNING: Unknown statement kind in _process_statement: List (StatementList)`。

pyslang 实际的语义树结构：

```
ProceduralBlock (AlwaysFF)
  └─ body: TimedStatement
       └─ stmt: BlockStatement          ← 当前代码跳过了这层
            └─ body: ConditionalStatement
                 └─ conditions[0].stmt: ExpressionStatement (assignment)
```

**根因**：`tracer.py` 中 `body_type == 'TimedStatement'` 分支试图直接拿 `.expr`，但 BlockStatement 没有 `.expr`，要走 `.stmt.body` 才是 ConditionalStatement。

**修复估计**：1-2 小时（外加 12 个 benchmark 回归 + 1-2 个新测试覆盖此场景）。

---

## 路线图

### M0: 让基础能用 ✅ 已规划

- [ ] **修 P0 bug**（`_process_block_body` 中 `TimedStatement → BlockStatement → ConditionalStatement` 路径）
- [ ] 跑通 `benchmarks/01_basic_registers.sv` 的 `data_out` driver 追踪
- [ ] 12 个 benchmark 全部跑一遍，记录通过率

### M1: 公开 API 测试覆盖

- [ ] 写 10 个 `tests/unit/` 测试覆盖 `trace_signal` 公开 API
  - [ ] 基础 always_ff 寄存器
  - [ ] 基础 always_comb 组合逻辑
  - [ ] continuous assign
  - [ ] 嵌套 if 条件栈
  - [ ] case 语句
  - [ ] 数组位选 `data[7:0]`
  - [ ] 多驱动检测（"驱动列表"是否完整）
  - [ ] load 追踪（`data_in` 被谁读）
  - [ ] 时钟/复位提取
  - [ ] driver_chain 递归（`get_driver_chain()`）

### M2: 上下文召回做厚

当前 `TraceResult` 字段齐全，但实际填充率不高。M2 目标：

- [ ] `scope_text` 真正带回整个 scope 源码（不是空字符串或单行）
- [ ] `condition_stack` 在嵌套 if 中正确填充（当前实现里有但未调用）
- [ ] `clock` / `reset` 提取率提升（识别 `posedge clk` / `negedge rst_n` 等变体）
- [ ] 设计 `ContextBundle` 数据结构（不可变 dataclass），把 `file:line + scope_text + cond_stack + port_connection` 打包
- [ ] `TraceResult.context: ContextBundle` 字段，让 agent 一次拿到所有上下文

### M3: 跨模块追踪做实

- [ ] 升级 API：支持传入"文件树 / include 列表"，而不是单个 sv_code 字符串
- [ ] 解析跨文件 `import` / `include`
- [ ] 端到端测试：3-4 文件的层级 SV（top → sub1 → sub2），追踪 `top.signal` 能穿过两层 instance
- [ ] 性能：处理 50 个 SV 文件、3 万行代码的回归，trace() 单次 < 100ms

### M4: 在真实项目上跑通

- [ ] OpenTitan: 至少 5 个核心模块（clk_rst / spi / uart / ...）的 `data_out` trace 全通
- [ ] XiangShan: 至少 1 个流水线级（IFU/LSU/EXU）的关键信号 trace 全通
- [ ] 收集 5 个真实 bug 案例（用 sv-trace 找出"多驱动"或"未驱动"等典型问题）

### M5: 极致（可选）

- [ ] 增量构建：文件改 1 行不重新 build 整个文件
- [ ] 并发：多文件并行 parse
- [ ] LRU 缓存：相同信号名查询 < 1ms
- [ ] Source range 精度提升（精确到字符 offset，而不是只到行）

---

## 不做（明确划界）

下列需求**当前不在**本项目范围内：

- ❌ CDC / 多驱动 / 未初始化 / 复位域 分析（属于 lint 工具）
- ❌ 面积 / 功耗 / 性能 估算（属于综合工具）
- ❌ FSM 提取 / SVA 生成 / 覆盖率建议（属于验证工具）
- ❌ 约束分析（属于形式验证工具）
- ❌ TB 复杂度评分（属于验证平台工具）
- ❌ Lint / Style 检查（属于 code quality 工具）
- ❌ 类/约束提取（属于元编程工具）
- ❌ 可视化（属于 UI 工具）

如果未来需要，应作为独立项目开发。

---

## 进度跟踪

| 阶段 | 状态 | 备注 |
|------|------|------|
| M0 P0 bug | ✅ 已完成 | 2026-06-01 |
| M0 benchmark 跑通 | ✅ 已完成 | 11/11, 0 warning |
| M1 公开 API 测试 | ✅ 已完成 | 13/13 |
| M2 上下文召回 | ❌ | 字段有值空 |
| M3 跨模块 | ❌ | 当前只支持单文件 |
| M4 真实项目 | ❌ | 0 验证 |
| M5 极致优化 | ❌ | |

---

## 历史（仅保留近一次重构的摘要）

**2026-06-01 大幅精简**（本路线图起点）：
- 删除 16+ 子模块：parse / debug / verify / lint / query / power / area / performance / regression / reports / viz / apps / extractors / scope / semantic / trace(旧)
- 统一到 `src/signal_tracer/`（4 文件）+ `src/sv_manager.py`
- pyslang 取代自研 parser
- 删除 167 个失效测试，归档到 `tests/_legacy/`
- 文档全部重写对齐

更早的历史归档在 `archive/2026-06-01_signal_tracer_only/`、`_archive/`、`_archived/`。
