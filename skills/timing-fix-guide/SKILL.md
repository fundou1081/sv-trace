---
name: timing-fix-guide
description: 时序修复指南，根据STA报告中的violation类型，提供优化建议和解决方案。
---

# Timing Fix Guide

时序修复指南

## 功能

根据时序violation类型，提供优化建议和解决方案。

## Violation类型

### 1. Setup Violation

**原因**: 数据路径延迟 > 时钟周期 - 建立时间

**症状**: WNS < 0 (Setup)

**优化策略**:

```
优先级1: 减少数据路径延迟
├── 流水线插入
│   └─ 在长组合路径中间加寄存器
├── 逻辑优化
│   ├─ 重写表达式减少逻辑级数
│   ├─资源共享
│   └─ 重新排序操作
├── 路径优化
│   ├─ 重定时(Retiming)
│   └─ 布局优化
└── 时钟调整
    ├─ 时钟 skew
    └─ 降低频率

优先级2: 增加时钟周期
├── 降低频率
└─ 改变时钟约束
```

### 2. Hold Violation

**原因**: 时钟偏斜 + 最短路径延迟

**症状**: WNS < 0 (Hold)

**优化策略**:

```
优先级1: 增加数据路径延迟
├── 延迟链
│   └─ 添加buffer
├── 物理优化
│   ├─ 增加路径长度
│   └─ 远离时钟线

优先级2: 减少时钟路径延迟
├── 时钟树优化
└─ 减少时钟 skew
```

### 3. Transition Violation

**原因**: 信号边沿太慢

**优化策略**:

```
├── 增加驱动强度
│   └─ 使用更大cell
├── 减少负载
│   ├─ 减少fanout
│   └─ 分割网络
└─ 减少线长度
```

## 常见violation修复

### Case 1: 长组合逻辑链

**问题**:
```
A → AND → OR → AND → OR → MUX → OUT
     (5级逻辑)
```

**解决方案**:
```
// 插入流水线
A → AND → [REG] → OR → [REG] → AND → OUT
                 (2级 + 2级)
```

### Case 2: 高扇出

**问题**:
```
信号 → [扇出=50] → 多处负载
```

**解决方案**:
```
// 方案1: Buffer树
signal → [BUF x 8] → [BUF x 8] → loads

// 方案2: 寄存器复制
+ 复制寄存器降低fanout
```

### Case 3: 多路复用器延迟

**问题**:
```
MUX选择延迟大
```

**解决方案**:
```
// 方案1: 早选择
选择信号先到 → 减少MUX延迟

// 方案2: 树形MUX
MUX → MUX
  ↓     ↓
A   B C   D
```

### Case 4: 进位链

**问题**:
```
加法器进位链太长
```

**解决方案**:
```
// 方案1: Carry Save加法器
// 方案2: 提前进位生成
// 方案3: 分级加法
```

## 决策树

```
时序violation类型?
    │
    ├─── Setup?
    │       ├─── 数据路径长? → 流水线/逻辑优化
    │       ├─── fanout高? → buffer/复制
    │       └─── 单元延迟大? → 替换cell
    │
    ├─── Hold?
    │       ├─── skew大? → 时钟优化
    │       └─── 数据太快? → 添加delay
    │
    └─── Transition?
            ├─── 驱动弱? → 增大cell
            └─── fanout高? → 减少fanout
```

## 修复优先级

| 方案 | 效果 | 代价 | 优先级 |
|------|------|------|--------|
| 流水线 | 高 | 增加latency | 1 |
| 逻辑优化 | 中 | 设计修改 | 2 |
| 物理优化 | 中 | P&R重跑 | 3 |
| 时钟调整 | 低 | 性能损失 | 4 |

## 示例

### Input
```
Path: reg_A → adder → mux → reg_B
Delay: 8.5ns
Clock: 10ns
Slack: -1.5ns (Setup violation)

逻辑分析:
- adder: 4级逻辑 (3.0ns)
- mux: 2级逻辑 (1.5ns)
- 线延迟: 4.0ns
```

### Output
```
# 时序修复报告

## Violation: Setup -1.5ns

## 瓶颈分析
1. adder延迟3.0ns (关键路径)
2. 线延迟4.0ns (过高)
3. mux延迟1.5ns

## 建议修复 (按优先级)

### 1. 流水线 (推荐)
位置: adder输出
效果: -2.0ns (假设2级分割)
代价: +1 cycle latency

```systemverilog
// 插入寄存器
reg [7:0] adder_out;
always @(posedge clk)
    adder_out <= adder_result;
```

### 2. 逻辑优化
位置: adder
效果: -0.5ns
代价: 设计修改

### 3. 替换高速单元
位置: adder
效果: -0.3ns
代价: 面积增加

## 预计结果
修复后: Slack +0.5ns (MET)
```

## 检查清单

- [ ] Violation类型已确定
- [ ] 瓶颈已识别
- [ ] 修复方案已排序
- [ ] 代价已评估
- [ ] 验证方案已计划
