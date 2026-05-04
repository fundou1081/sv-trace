# OpenTitan uart_core.sv 信号分析对比报告

**日期**: 2026-05-04
**分析对象**: `opentitan/hw/ip/uart/rtl/uart_core.sv`
**分析方法**: 人工源码阅读 vs 工具自动分析

---

## 分析摘要

| 指标 | 值 |
|------|-----|
| 模块行数 | 525 |
| 发现信号数 | 62 |
| 解析状态 | ✅ 成功 |
| RHS提取准确率 | ⚠️ 低 (大部分为空) |
| 时钟/复位分类 | ✅ 正确 |

---

## 信号分析对比

### 1. nco_sum_q (NCO 累加器寄存器)

| 维度 | 人工分析 | 工具分析 |
|------|----------|----------|
| **类型** | 时序逻辑寄存器 | ✅ 检测到 |
| **驱动** | `reg2hw.ctrl.nco.q` (累加) | ⚠️ sources=[] |
| **负载** | `tick_baud_x16` | ⚠️ 检测到但不完整 |
| **时钟** | `clk_i` | ✅ clk_i |
| **复位** | `rst_ni` | ✅ rst_ni |

**结论**: 驱动源提取失败 (涉及位拼接 `{1'b0, nco_sum_q[NcoWidth-1:0]}`)

---

### 2. tick_baud_x16 (波特率 tick 信号)

| 维度 | 人工分析 | 工具分析 |
|------|----------|----------|
| **类型** | 组合逻辑输出 | ✅ 检测到 |
| **驱动** | `nco_sum_q[16]` | ⚠️ sources=[] |
| **负载** | `uart_tx`, `uart_rx` 实例 | ❌ 未检测到 |

**结论**: 驱动源和负载均未正确提取

---

### 3. rx_fifo_wvalid (RX FIFO 写有效)

| 维度 | 人工分析 | 工具分析 |
|------|----------|----------|
| **类型** | 组合逻辑 | ✅ 检测到 |
| **驱动** | `rx_valid & ~event_rx_frame_err & ...` | ⚠️ sources=[] |
| **负载** | `rx_fifo` 实例的 `wvalid_i` | ⚠️ 检测到但不完整 |

**结论**: 复杂表达式 RHS 提取失败

---

### 4. rx_val_q (RX 移位寄存器)

| 维度 | 人工分析 | 工具分析 |
|------|----------|----------|
| **类型** | 时序逻辑移位寄存器 | ✅ 检测到 |
| **驱动** | `rx_in`, `rx_val_q` (移位) | ⚠️ sources=[] |
| **负载** | 多个 always 块中作为条件 | ⚠️ 检测到1个 |

**结论**: 驱动源提取失败

---

## 已知问题

### 1. RHS 提取不完整 (严重)

**问题**: 大部分信号的 `sources` 为空

**原因**:
- 位拼接表达式 `{a, b}` 提取失败
- 条件表达式 `a ? b : c` 提取失败
- 嵌套表达式提取失败

**示例**:
```systemverilog
// 工具无法提取 sources
nco_sum_q <= {1'b0, nco_sum_q[NcoWidth-1:0]} + {1'b0, reg2hw.ctrl.nco.q};
```

### 2. 负载检测不完整 (中等)

**问题**: 反向查找 (`reverse_lookup`) 返回的结果不完整

**原因**: LoadTracerExt 的 `_build_reverse_index` 可能未正确填充所有映射

### 3. 重复负载计数 (轻微)

**问题**: 同一信号出现多次

**示例**:
```
loads=['event_rx_overflow', 'event_rx_overflow']
```

---

## 改进建议

### 高优先级

1. **完善 RHS 提取逻辑**
   - 支持位拼接表达式 `{a, b}`
   - 支持条件表达式 `a ? b : c`
   - 支持多层嵌套表达式

2. **完善反向索引构建**
   - 确保 LoadTracerExt 能正确建立 `src → dst` 映射
   - 添加调试输出，验证索引构建过程

### 中优先级

3. **添加复杂表达式测试用例**
   - 覆盖位拼接、条件表达式、嵌套表达式
   - 按照铁律13 添加金标准验证

4. **优化负载去重**
   - 在 `_collect_loads` 中使用 set 替代 list 去重

---

## 代码位置

| 文件 | 功能 |
|------|------|
| `src/trace/driver.py` | `_extract_sources()` - RHS 提取 |
| `src/trace/load.py` | `_extract_signals()` - 信号提取 |
| `src/trace/load_ext.py` | `_build_reverse_index()` - 反向索引 |

---

## 参考

- RTL 源码: `opentitan/hw/ip/uart/rtl/uart_core.sv`
- 工具: SignalChainQuery (sv-trace)
