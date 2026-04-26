---
name: clock-gating-advisor
description: 时钟门控建议工具，分析模块功耗特性，建议可添加时钟门控的位置和方式。
---

# Clock Gating Advisor

时钟门控建议

## 功能

分析RTL设计，建议时钟门控的位置和策略，降低动态功耗。

## 分析流程

```
1. 识别时钟树结构
2. 分析数据使能模式
3. 识别空闲条件
4. 建议门控策略
5. 评估功耗节省
```

## 门控类型

### 1. 全局门控
适用于整个模块长时间不使用

```systemverilog
// 当模块完全idle时关闭时钟
if (!module_busy) begin
    clk_gate.uclk <= 1'b0;
end
```

### 2. 局部门控
适用于模块内部子单元

```systemverilog
// 只有关心FIFO时才打开其时钟
always_ff @(posedge clk) begin
    if (fifo_en)
        fifo_clk_en <= 1'b1;
    else
        fifo_clk_en <= 1'b0;
end
```

### 3. 寄存器级门控
集成在寄存器中

```systemverilog
// 使用ICG单元
ICG u_icg (
    .CK(clk),
    .E(gating_en),
    .Q(gated_clk)
);
```

## 识别规则

### 可门控条件

| 条件 | 模块示例 | 门控信号 |
|------|----------|----------|
| idle标志 | FSM处于IDLE | idle |
| 空FIFO | FIFO无数据 | fifo_empty |
| 禁止输入 | rx_en=0 | rx_en |
| 复位状态 | soft_rst | rst_n |
| 配置禁用 | cfg_en=0 | cfg_en |

### 门控候选识别

```
模式1: 空闲等待
always_ff @(posedge clk) begin
    if (state == IDLE)
        reg <= reg;  // idle时保持，可门控
end

模式2: 常数保持
always_ff @(posedge clk) begin
    if (en)
        reg <= data;
    else
        reg <= reg;  // 不使用时保持
end
```

## 输入分析

```systemverilog
module uart_controller (
    input clk,
    input rst_n,
    input rx_en,
    input [7:0] rx_data,
    output reg [7:0] tx_data
);

reg [7:0] tx_buf;
reg tx_busy;
reg [3:0] bit_cnt;

// 当tx_busy=1时持续工作
// 当tx_busy=0时idle
endmodule
```

## 输出建议

```markdown
# 时钟门控分析报告

## 模块: uart_controller

## 当前功耗: ~5mW

## 建议门控

### 1. TX路径门控 (高优先级)
位置: uart_tx模块
条件: tx_busy == 0
估计节省: 1.5mW (30%)
建议: 添加ICG单元

```systemverilog
ICG tx_clk_gate (
    .CK(clk),
    .E(tx_busy),
    .Q(gated_tx_clk)
);
```

### 2. 波特率生成器门控
位置: baud_gen模块
条件: rx_en==0 && tx_busy==0
估计节省: 2mW (40%)
建议: 组合门控

### 3. RX路径门控
位置: uart_rx模块
条件: rx_en == 0
估计节省: 0.5mW (10%)
建议: 直接门控输入使能

## 总计
- 当前功耗: 5mW
- 建议节省: 4mW
- 目标功耗: 1mW
- 节省比例: 80%

## 注意事项

1. 门控信号需要同步
2. 避免门控引入glitch
3. 验证门控后功能正确
```

## 决策树

```
模块是否长时间idle?
    YES → 全局门控
    NO
        ├─── 内部有独立子单元?
        │       YES → 局部门控
        │       NO
        │           ├─── 寄存器保持值不变?
        │           │       YES → 寄存器级门控
        │           │       NO → 不建议门控
```

## 门控检查清单

- [ ] 时钟路径已识别
- [ ] 门控候选已列出
- [ ] 门控条件已定义
- [ ] 无glitch风险
- [ ] 功能验证通过
- [ ] 功耗节省已评估
