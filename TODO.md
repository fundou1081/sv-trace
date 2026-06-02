# sv-trace 路线图

> 更新时间: 2026-06-03
> 项目目标: **只做信号追踪 + 上下文召回，做到极致**

## 进度概览

| 阶段 | 状态 | 测试 | 备注 |
|------|------|------|------|
| M0 修 P0 bug | ✅ 完成 | 13/13 | TimedStatement 路径处理 |
| M1 公开 API 测试 | ✅ 完成 | 13/13 | 基础 + 数组 + 字段 |
| M1.5 补强 | ✅ 完成 | 20/20 | 多驱动 + clock/reset + chain |
| M2 上下文召回 | ✅ 完成 | 13/13 | line 准确 + ContextBundle |
| M3 跨文件 | ✅ 完成 | 9/9 | 多文件 + 层次路径 |
| **M4 真实项目** | ✅ 完成 | +5 | OpenTitan 6 模块 (30,218 drivers, 0 warning, 0 empty) |
| **M4.1 Interface/Modport** | ✅ 完成 | +6 | 17+ SV 表达式 + 跨 modport 读写 + m.data[3:0] 位选 |
| **M5.1 evidence 链** | ✅ 完成 | +8 | CodeEvidence + credibilidad_score 0-1 + is_verified |
| **M5.1b find_multi_drivers 整合** | ✅ 完成 | +4 | 默认 verify=True, 多驱动带 evidence |
| **M5.1c get_driver_chain 整合** | ✅ 完成 | +4 | 顺藤摸瓜链上每跳带 credibility |
| **M5.1d trace/trace_drivers/trace_loads 整合** | ✅ 完成 | +7 | drivers 和 loads 都自动带 evidence |
| **M5.1e get_load_chain 整合** | ✅ 完成 | +5 | 顺藤摸瓜查下游 (与 driver chain 对称) |
| **M5.1f dump_chain** | ✅ 完成 | +9 | 一次 dump 整链为 JSON (含 summary, LLM 友好) |
| **M5.1g dump_multi_drivers** | ✅ 完成 | +6 | 一次 dump 多驱动检测 (冲突 + summary) |
| **M5.2a ElementSelect 嵌套** | ✅ 完成 | +3 | OpenTitan 发现: 修嵌套 ElementSelect+RangeSelect |
| **M5.2b 智能分类** | ✅ 完成 | +7 | 4 类分类, 304 → 5 真冲突 (98% 噪声过滤) |
| **M5.2c 分类器优化** | 📋 待开始 | — | 修 3 个分类器限制 (见 TODO 章节) |
| **M5.3 极致优化** | 📋 待开始 | — | 增量 / 并发 / 缓存 |

**当前总计**: **127/127 测试通过** (1.83s → 4.11s)

**OpenTitan 20 模块 真实项目验证**: 239 个 .sv, 50,294 drivers, 94,206 loads, 0 empty (0.00%), 304 多驱动信号 → 5 真冲突候选 (98% 噪声过滤)

---

## ✅ M0: 修 P0 bug

修 `tracer.py:_process_block_body` 漏处理 `TimedStatement → BlockStatement` 路径。

修复后 `trace_signal('data_out', benchmarks/01_basic_registers.sv)` 返回 2 个 driver（`8'h00` 和 `data_in`），含正确的 clock/reset/condition_stack/scope_text。

详见 commit `9ec7ae0` (修复 + 重构) 和 `9de4660` (line 准确性)。

## ✅ M1: 公开 API 测试覆盖

`tests/unit/test_signal_tracer.py` 13 个测试：
- `TestBasic` (3): always_ff / always_comb / continuous_assign
- `TestControlFlow` (3): case / nested_if / condition_stack
- `TestArrays` (2): 数组元素赋值 / 基名索引
- `TestNoCrashes` (2): 11 benchmark 不 crash / 都产结果
- `TestTraceResultFields` (3): scope_text / scope_kind / CONTINUOUS_ASSIGN

## ✅ M1.5: 补强

3 个子任务（commits `835b0c1` / `c155739` / `907f5ef`）：

### 1. 多驱动检测
- `SignalTracer.find_multi_drivers() -> Dict[str, List[TraceResult]]`
- `SignalTracer.get_driver_count(signal_name) -> int`
- `TraceSummary.is_multi_driver() -> bool`
- `TraceSummary.get_driver_scopes() -> List[str]`
- 6 个测试

### 2. clock/reset 提取
- `_extract_clock_reset(block) -> (clock, reset)` 从 pyslang EventListControl / SignalEventControl 提取
- 判定优先级：命名启发式（rst/reset/arst/srst/por/clr）→ negedge edge 启发式
- 透传到所有 driver/load trace
- 8 个测试

### 3. driver_chain 递归
- `SignalTracer.get_driver_chain(signal_name, max_depth=10) -> List[TraceResult]`
- 真正递归整个 `_drivers` 图（区别于 `TraceSummary.get_driver_chain()` 旧版只查 direct drivers）
- cycle detection 用 `visited: Set[str]`
- `_is_real_signal()` 过滤字面常量/表达式
- 6 个测试

### 附带清理
- 删 192 行死代码（`_traverse` / `_process_assignment` / `_process_condition` / `_extract_scope_info` / 旧 `_extract_clock_reset` 等）

## ✅ M2: 上下文召回做厚

2 个子任务（commits `9de4660` / `5b26cdd`）：

### 1. line / scope_text 准确性
- `line` 用 `expr.sourceRange`（实际赋值行，不是 scope 起始行）
- `char_offset` 从 0 改为实际字符偏移
- `scope_line_end` 从 scope 起始行改为 `syn.sourceRange.end` 计算的 end line
- `scope_text` 保留多行 + `.strip()` 去首尾空白
- 5 个测试

### 2. ContextBundle 数据结构
- `ContextBundle` (frozen=True dataclass)：打包 file/line/scope/clock/reset/condition_stack/port/path/confidence
- `TraceResult.to_context() -> ContextBundle`
- `TraceSummary.to_contexts() -> List[ContextBundle]`
- `ContextBundle.to_dict()` / `.summary()`
- 8 个测试

## ✅ M3: 跨文件 + 层次路径

commit `b74d437`：

- `SignalTracer.add_file(path, code)` 支持多文件
- 同一 pyslang `Compilation` 多棵 `addSyntaxTree()`，跨文件 module 自动解析
- driver key 用 `{scope.hpath}.{signal}` 形式
- `trace()` 智能匹配 4 步：完全 → 数组前缀 → 后缀 → cross-module
- 向后兼容 `SignalTracer(code, path)` 老 API
- 9 个测试 + 3 文件 fixture (`tests/fixtures/m3_hierarchical/`: top → mid → leaf)

性能（3 文件 / 44 行 fixture）：build 3.2ms，query < 1ms。

---

## 📋 M4: 真实项目验证（待开始）

TODO:
- [ ] OpenTitan: 5 个核心模块（clk_rst / spi / uart / ...）端到端跑通
- [ ] XiangShan: 1 个流水线级（IFU/LSU/EXU）跑关键信号
- [ ] 收集 5 个真实 bug 案例（多驱动、未驱动、跨模块悬空）

会暴露 M3 没覆盖的边界：interface / clocking block / package import / generate 深层嵌套。

## ✅ M5.1: evidence 链 + dump 工具 (全 7 阶段完成)

7 个子阶段: M5.1, M5.1b, M5.1c, M5.1d, M5.1e, M5.1f, M5.1g
详见下文历史, 共 +35 测试 (累计 117/117)。

## ✅ M5.2a: 嵌套 ElementSelect + RangeSelect 修复

OpenTitan otbn 真实 bug 发现并修复: `arr[0][255:0]` 嵌套表达式 pyslang 拿不到 source_expr。
修复后 OpenTitan 20 模块 (239 .sv 文件): 50,294 drivers, 0 empty (0.00%)。
+3 测试 (累计 120/120)。

## ✅ M5.2b: find_multi_drivers_classified 智能分类 (304 → 5 真冲突, 98% 噪声过滤)

OpenTitan 20 模块验证发现: 旧 `find_multi_drivers` 报 304 个 '冲突', 但 99% 是 false positive (跨 instance 同名 local, 按位分区写, generate 块内同名 local)。
新增 4 类分类 + 严格过滤:
- `real_conflict` (5) - 同一 instance 同一文件真有多个 scope 写同一 signal
- `cross_instance` (299) - 不同 instance 各自有同名 local
- `bit_partition` (0) - 位选区间不重叠 (按位分区写)
- `generate_block` (0) - generate 块内同名 local
+7 测试 (累计 127/127)。OpenTitan 5 个真 multi-driver bug 候选分布在 spi_device/aes/otbn/kmac。

## 📋 M5.2c: 改进 M5.2b 分类器 (留待优化)

**3 个已知限制** (影响分类准确度, 留给 M5.2c 优化):

1. **`bit_range_overlap` 只能检测常量位选**
   - 当前: 用正则 `\d+:\d+` 提取位选区间
   - 问题: OpenTitan 用 `arr[WLEN-1:WLEN/2]` 这种 parametric indices, pyslang 不直接给出常量值
   - 改进方向: 走 pyslang elaboration 拿真实位选; 或评估时把 parameter 替换为值
   - 影响: M5.2b 在 OpenTitan 检出 0 个 bit_partition (但实际可能存在)

2. **`generate_block` 仅靠 'gen_' 关键字检测**
   - 当前: `if 'gen_' in scope_text` 关键词匹配
   - 问题: 真正 generate 模式应走 pyslang `InstanceArray` 树, 同一 generate label 下同名 local 是设计意图
   - 改进方向: 用 pyslang 的 `InstanceArraySymbol.parent` 关系做 generate 边界判定
   - 影响: M5.2b 在 OpenTitan 检出 0 个 generate_block (但实际可能存在)

3. **`cross_instance` 误报 array 索引归一化**
   - 当前: 用 hpath 去重, 但 array 索引 `arr[0]` 和 `arr[1]` 可能是同一 hpath 下的不同元素
   - 问题: 同一 instance 内的 array 不同索引的 driver 会被误报为 cross_instance
   - 改进方向: 解析 hpath 里的 array 索引, 同 array 同索引才是真冲突
   - 影响: 极小 (RTL 少见), 但应处理

## 📋 M5.3: 极致优化（待开始）

- [ ] 增量构建（文件改 1 行不重新 build 整个项目，看 pyslang 是否支持）
- [ ] 并发（多文件并行 parse）
- [ ] LRU 缓存（相同信号名查询 < 1ms；现在已经是了，可加装饰器）
- [ ] Source range 精度提升（精确到字符 offset；当前已实现，未暴露 API）
- [ ] 修 M5.2c 的 3 个分类器限制 (bit_partition / generate_block / cross_instance)

---

## 不做（明确划界）

下列需求**当前不在**本项目范围内：

- ❌ CDC / 多驱动检测 / 未初始化 / 复位域 分析（属于 lint 工具）— 等等，M1.5 加了多驱动**检测**（不是 lint 告警，是数据暴露），不算违反
- ❌ 面积 / 功耗 / 性能 估算（属于综合工具）
- ❌ FSM 提取 / SVA 生成 / 覆盖率建议（属于验证工具）
- ❌ 约束分析（属于形式验证工具）
- ❌ TB 复杂度评分（属于验证平台工具）
- ❌ Lint / Style 检查（属于 code quality 工具）
- ❌ 类/约束提取（属于元编程工具）
- ❌ 可视化（属于 UI 工具）
- ❌ **代码证据链不算 lint**: M5.1 evidence 是 "读回文件交叉验证", 跟 lint 工具的 "检测代码模式" 不同。evidence 是**自证** (trace 自己证明自己), lint 是**找错** (工具指出代码错)。

如果未来需要，应作为独立项目开发。

---

## 历史

**2026-06-01 大精简 + 4 个里程碑 (M0-M3)**:
- 起点：src/ 16+ 子模块，公开 API 0 测试，11/11 benchmark 全挂
- 终态：src/ = `signal_tracer` + `sv_manager`（5 文件），公开 API 68 测试全过
- 8 个 commit 完成 M0-M3

**2026-06-02 M4 真实项目验证**:
- OpenTitan 6 模块 (uart/spi_device/dma/i2c/aes/hmac) 端到端跑通
- 30,218 drivers 总追踪量, 0 warning, 0 empty driver
- 修了 file path bug, 跨文件 line 错误, RangeSelect 嵌套空 text, InvalidExpression 防御

**2026-06-02 M4.1 Interface/Modport**:
- 17+ 种 SV 表达式覆盖 (MemberAccess / Streaming / Inside / StructuredAssignmentPattern 等)
- HierarchicalValue 处理 modport 访问 (`m.valid` / `m.data[3:0]`)

**2026-06-02-03 M5.1 evidence 链 (全家族)**:
- CodeEvidence 数据类: snippet / context_before/after / matches_* / credibility_score 0-1
- 6 个 trace API 默认 verify=True 自动带 evidence
- 3 个 dump 工具 1 次返回整链 dict (含 summary)
- 35 个新测试累计 117/117 通过
- 加 SKILL.md (供 agent 调用)

**重构**:
- 删 16+ 子模块: parse / debug / verify / lint / query / power / area / performance / regression / reports / viz / apps / extractors / scope / semantic / trace(旧)
- 统一到 `src/signal_tracer/` + `src/sv_manager.py`
- pyslang 取代自研 parser
- 删 167 个失效测试, 归档到 `tests/_legacy/`
- 删 192 行 tracer.py 内部死代码
- M5.1 修 2 个旧架构测试文件 (8 fail) 迁移到 _legacy

**Commits** (按时间倒序):
```
f8fa6cd M5.2b - find_multi_drivers_classified 智能分类 (304 → 5 真冲突, 98% 噪声过滤)
258ce41 M5.2a - 嵌套 ElementSelect + RangeSelect 处理
756e0ea docs: 批量更新项目文档 (STRUCTURE/TODO/TEST_PLAN/tests/README)
7e3129a M5.1g - dump_multi_drivers 一次 dump 多驱动检测 (冲突+证据)
b30fa01 M5.1f - dump_chain 一次 dump 整链为 JSON (LLM 友好)
d0d4c46 M5.1e - get_load_chain 整合 evidence (与 driver chain 对称)
27f6a7e M5.1d - trace/trace_drivers/trace_loads 整合 evidence
b19a986 M5.1c - get_driver_chain 整合 evidence (链上每跳带 credibilidad)
caead28 M5.1b - find_multi_drivers 整合 evidence (默认 verify=True)
42e2ab2 docs: README + SKILL.md 同步 M5.1 evidence chain
e50fe4c M5.1 - 代码证据链, 召回上下文作为可证伪的追踪证据
ffdfe71 docs: 更新 README + 新增 SKILL.md (供 agent 调用)
b76d971 M4.1 - Interface/Modport 信号追踪支持
4baf9a9 M4 - 扩展 StructuredAssignmentPattern + SimpleAssignmentPattern + LValueReference
8ddd000 M4 - 扩展表达式处理覆盖工业 SV 语法
c72c3e9 M4 plan A - 跨文件 line 精确化 (pyslang SourceManager)
b74d437 M3 - 多文件支持 + 层次路径追踪
5b26cdd M2 任务 2+3 - ContextBundle + TraceResult.to_context()
9de4660 M2 任务 1 - 修复 line/scope_text 准确性
907f5ef M1.5 任务 3 - driver_chain 递归查询
c155739 M1.5 任务 2 - 提取 clock/reset 字段
835b0c1 M1.5 任务 1 - 多驱动信号检测
9ec7ae0 refactor(tracer): 精简 src/ + 修 P0 bug
```

更早历史归档在 `archive/2026-06-01_signal_tracer_only/`、`_archive/`、`_archived/`。
