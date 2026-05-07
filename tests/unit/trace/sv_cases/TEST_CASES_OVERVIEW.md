# sv-trace 测试用例总览

## 测试用例库

| 文件 | 功能 | 用例数 | 说明 |
|------|------|--------|------|
| driver/driver_basic.sv | DriverTracer | 5 | 基础驱动模式 |
| driver/driver_cases_20.sv | DriverTracer | 20 | 语法组合覆盖 |
| fsm/fsm_simple.sv | FSMExtractor | 3 | 基础状态机 |
| fsm/fsm_cases_20.sv | FSMExtractor | 20 | 状态机语法组合 |
| iospec/iospec_basic.sv | IOSpecExtractor | 3 | 基础IO |
| iospec/iospec_cases_20.sv | IOSpecExtractor | 20 | IO语法组合 |
| dependency/dependency_hierarchy.sv | Dependency | 7 | 层级依赖 |
| dependency/dep_cases_20.sv | Dependency | 20 | 依赖语法组合 |
| lint/lint_issues.sv | Lint | 6 | 代码问题 |
| lint/lint_cases_20.sv | Lint | 20 | 问题语法组合 |

**总计**: 10 个文件, ~137 个测试用例

---

## DriverTracer 测试覆盖 (25个)

| # | 测试内容 | 语法特征 |
|---|---------|----------|
| 01 | assign 驱动 | `assign a = 8'hFF;` |
| 02 | 多重 assign | 链式赋值 |
| 03 | always_ff posedge | `@(posedge clk)` |
| 04 | always_ff negedge | `@(negedge clk)` |
| 05 | always_ff 多时钟沿 | `posedge clk_a or posedge clk_b` |
| 06 | always_ff 异步复位 | `or negedge rst_n` |
| 07 | always_ff 同步复位 | `if (rst)` |
| 08 | always_comb | 组合逻辑 |
| 09 | always_comb 多表达式 | 多个赋值 |
| 10 | always_latch | 锁存器 |
| 11 | if-else 嵌套 | 多层条件 |
| 12 | case 语句 | 多路复用 |
| 13 | casez 通配符 | `casez` |
| 14 | casex x/z | `casex` |
| 15 | for 循环 | 循环赋值 |
| 16 | generate if | 条件生成 |
| 17 | generate for | 循环生成 |
| 18 | 阻塞赋值 | `=` |
| 19 | 非阻塞赋值 | `<=` |
| 20 | 混合赋值 | 阻塞+非阻塞 |

---

## FSMExtractor 测试覆盖 (23个)

| # | 测试内容 | 特征 |
|---|---------|------|
| 01 | 二进制编码 | `2'b00` |
| 02 | One-Hot 编码 | `4'b0001` |
| 03 | Gray 编码 | 格雷码 |
| 04 | typedef enum | 枚举类型 |
| 05 | 单 always_ff | 无 next_state |
| 06 | 带复位状态 | 有复位路径 |
| 07 | 多输入条件 | 多个控制信号 |
| 08 | Moore 型输出 | 状态输出 |
| 09 | Mealy 型输出 | 条件输出 |
| 10 | 带计数器 | 状态机+计数器 |
| 11 | 嵌套状态机 | 多层状态 |
| 12 | 握手状态机 | req/ack |
| 13 | FIFO 接口 | full/empty |
| 14 | AXI 风格 | valid/ready |
| 15 | 优先级编码 | if-else 优先级 |
| 16 | 有 default | default 状态 |
| 17 | 无 default | 边界情况 |
| 18 | 命名状态变量 | `fsm_state` |
| 19 | 多 bit 状态 | 8bit 状态 |
| 20 | 边界检测 | 阈值比较 |

---

## IOSpecExtractor 测试覆盖 (23个)

| # | 测试内容 | 特征 |
|---|---------|------|
| 01 | 简单 input | 单输入 |
| 02 | 简单 output | 单输出 |
| 03 | input + output | 双向基础 |
| 04 | 带宽度 | `[31:0]` |
| 05 | 向量信号 | `vec [0:3]` |
| 06 | 异步复位 | `rst_n` |
| 07 | 同步复位 | `rst` |
| 08 | inout 三态 | 三态口 |
| 09 | 混合方向 | 多类型 |
| 10 | 参数化 | `#(WIDTH=8)` |
| 11 | 多参数 | 多个参数 |
| 12 | 打包结构 | byte enable |
| 13 | 握手信号 | valid/ready |
| 14 | 总线接口 | addr/data |
| 15 | 时钟门控 | clk_en |
| 16 | 多时钟 | clk_a/clk_b |
| 17 | 中断信号 | irq |
| 18 | 调试接口 | dbg_* |
| 19 | 本地参数 | localparam |
| 20 | 复杂接口 | 综合 |

---

## ModuleDependencyAnalyzer 测试覆盖 (27个)

| # | 测试内容 | 特征 |
|---|---------|------|
| 01 | 单模块 | 无依赖 |
| 02 | 两层依赖 | top->sub |
| 03 | 三层依赖 | top->mid->leaf |
| 04 | 参数化 | #(.WIDTH) |
| 05 | 多实例 | u0,u1,u2 |
| 06 | 参数传递 | #(.WIDTH(32)) |
| 07 | 数组实例化 | `u_array[0:3]` |
| 08 | 嵌套实例化 | A->leaf, B->leaf |
| 09 | generate if | 条件生成 |
| 10 | generate for | 循环生成 |
| 11 | 条件实例化 | `if (USE_EXT)` |
| 12 | 多子模块 | cpu/mem/uart |
| 13 | Diamond 依赖 | A,B->leaf |
| 14 | 全局信号 | clk/rst_n |
| 15 | 复杂层次 | 嵌套块 |
| 16 | 同层多实例 | 4个实例 |
| 17 | 带连接 | `.data_in(a)` |
| 18 | 混合层次 | 综合 |

---

## Lint 测试覆盖 (26个)

| # | 问题类型 | 状态 |
|---|---------|------|
| 01 | Case 无 default | 问题 |
| 02 | Case 有 default | OK |
| 03 | Latch 推断 | 问题 |
| 04 | 正确 always_ff | OK |
| 05 | 组合环路 | 问题 |
| 06 | 无环路 | OK |
| 07 | 未使用 wire | 问题 |
| 08 | 全部使用 | OK |
| 09 | 未连接输出 | 问题 |
| 10 | 全部连接 | OK |
| 11 | 错误复位 | 问题 |
| 12 | 正确复位 | OK |
| 13 | 多驱动 | 问题 |
| 14 | 单驱动 | OK |
| 15 | X 赋值 | 问题 |
| 16 | 正常赋值 | OK |
| 17 | Partial case | 问题 |
| 18 | Full case | OK |
| 19 | Generate 同名 | OK |
| 20 | 阻塞混用 | 问题 |

---

## 语法覆盖总结

### 覆盖的语法关键字

```
always_ff, always_comb, always_latch
assign
if, else, case, casez, casex, default
for, while, do, repeat
generate, if, for, case
parameter, localparam
input, output, inout
wire, logic, reg
posedge, negedge
blocking (=), non-blocking (<=)
```

### 未覆盖语法 (待扩展)

```
function, task
class, package
interface, modport
property, sequence
covergroup, coverpoint
constraint
fork, join
```

---

最后更新: 2026-04-20
