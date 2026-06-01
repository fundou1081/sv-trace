# 时序约束模板 (SDC格式)

**模块**: {module_name}
**版本**: v1.0
**日期**: {date}

---

## 1. 时钟定义

### 1.1 主时钟

```tcl
# 主时钟定义
create_clock -name clk -period {period} [get_ports clk]

# 如果有时钟质量要求
set_clock_uncertainty -setup {setup_uncertainty} [get_clocks clk]
set_clock_uncertainty -hold {hold_uncertainty} [get_clocks clk]

# 时钟转换时间
set_clock_transition -min {min_trans} [get_clocks clk]
set_clock_transition -max {max_trans} [get_clocks clk]
```

### 1.2 生成时钟

```tcl
# 生成时钟 - 分频
create_generated_clock -name clk_div -source [get_ports clk] \
    -divide_by {div} [get_pins u_div/counter_reg/C]

# 生成时钟 - 倍频
create_generated_clock -name clk_x2 -source [get_ports clk] \
    -multiply_by {mult} [get_pins u_pll/clk_out]
```

### 1.3 虚拟时钟

```tcl
# 用于IO约束的虚拟时钟
create_clock -name virtual_clk -period {period}
```

---

## 2. 时钟关系

### 2.1 时钟组

```tcl
# 设置不相关的时钟
set_clock_groups -asynchronous \
    -group [get_clocks clk_a] \
    -group [get_clocks clk_b] \
    -group [get_clocks clk_c]
```

### 2.2 独占时钟组

```tcl
# 互斥的时钟
set_clock_groups -physically_exclusive \
    -group [get_clocks clk_test] \
    -group [get_clocks clk_normal]
```

---

## 3. 输入延迟约束

### 3.1 同步输入

```tcl
# 基本输入延迟 (相对于主时钟)
set_input_delay -clock clk \
    -max {max_input_delay} \
    [get_ports {input_port}]

set_input_delay -clock clk \
    -min {min_input_delay} \
    [get_ports {input_port}]
```

### 3.2 多时钟域输入

```tcl
# 来自clk_a的输入
set_input_delay -clock clk_a \
    -max {max_delay} \
    [get_ports {input_port}]

# 来自clk_b的输入
set_input_delay -clock clk_b \
    -max {max_delay} \
    [get_ports {input_port}]
```

---

## 4. 输出延迟约束

### 4.1 同步输出

```tcl
# 基本输出延迟
set_output_delay -clock clk \
    -max {max_output_delay} \
    [get_ports {output_port}]

set_output_delay -clock clk \
    -min {min_output_delay} \
    [get_ports {output_port}]
```

### 4.2 DDR接口

```tcl
# DDR时钟
create_clock -name ddr_clk -period {period}

# DDR数据输出
set_output_delay -clock ddr_clk -add_delay \
    -max {max_delay} \
    [get_ports ddr_dq[*]]

set_output_delay -clock ddr_clk -add_delay \
    -min {min_delay} \
    [get_ports ddr_dq[*]]
```

---

## 5. 时序异常

### 5.1 伪路径

```tcl
# 异步复位信号
set_false_path -from [get_ports rst_n]

# 测试模式路径
set_false_path -from [get_ports test_mode]

# 异步时钟域穿越
set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b]
```

### 5.2 最大延迟

```tcl
# 关键路径约束
set_max_delay -from {from_point} -to {to_point} {delay}
```

### 5.3 最小延迟

```tcl
# 保持时间检查
set_min_delay -from {from} -to {to} {delay}
```

---

## 6. 端口约束

### 6.1 电容负载

```tcl
set_capacitance -pin_load {capacitance} [get_ports {port}]
```

### 6.2 驱动强度

```tcl
set_driving_cell -lib_cell {cell} -pin {pin} [get_ports {port}]
```

---

## 7. 时钟域交叉约束

### 7.1 CDC同步器约束

```tcl
# 2级FF同步器
set_false_path -through [get_pins -hier -filter {name =~ *sync*}]

# 握手同步器
set_false_path -from [get_clocks clk_src] -to [get_clocks clk_dst] \
    -through [get_pins u_handshake/*]
```

### 7.2 多位CDC

```tcl
# 格雷码
set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b] \
    -through [get_pins u_gray/*]

# FIFO
set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b] \
    -through [get_pins u_fifo/*]
```

---

## 8. 常用约束速查

| 约束类型 | 语法 | 示例 |
|----------|------|------|
| 主时钟 | create_clock | create_clock -name clk -period 10 |
| 生成时钟 | create_generated_clock | -divide_by 2 |
| 输入延迟 | set_input_delay | -clock clk -max 2 |
| 输出延迟 | set_output_delay | -clock clk -max 3 |
| 伪路径 | set_false_path | -from rst_n |
| 最大延迟 | set_max_delay | -from A -to B 5 |
| 时钟组 | set_clock_groups | -asynchronous |

---

## 9. 约束验证

### 9.1 检查命令

```tcl
# 检查时钟定义
report_clocks

# 检查约束覆盖率
report_constraint -all

# 检查时序违规
report_timing -max_paths 10
```

### 9.2 常见问题

| 问题 | 检查命令 | 解决方案 |
|------|----------|----------|
| Missing clock | report_clocks | 添加create_clock |
| Unconstrained | report_ignored | 添加约束 |
| Violation | report_timing | 优化逻辑 |

---

*SDC模板版本: v1.0*
