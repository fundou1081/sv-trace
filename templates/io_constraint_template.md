# IO约束模板

**模块**: {module_name}
**版本**: v1.0
**日期**: {date}

---

## 1. IO规划总览

### 1.1 引脚分配原则

```
1. 高速信号靠近芯片边缘
2. 电源/地引脚均匀分布
3. 模拟/数字引脚分离
4. 同组信号相邻排列
```

### 1.2 IO类型分类

| 类型 | 说明 | 示例 |
|------|------|------|
|时钟输入 | 高频时钟 | sys_clk, ref_clk |
|高速数据 | DDR, SerDes | data_*, tx_*, rx_* |
|普通IO | 标准接口 | gpio_*, ctrl_* |
|电源 | 电源/地 | vdd, vss, avdd |
|模拟 | 模拟信号 | adc_in, dac_out |

---

## 2. 时钟输入约束

### 2.1 单端时钟

```tcl
# 主时钟输入
create_clock -name sys_clk -period {period} [get_ports sys_clk]

# 约束
set_input_delay -clock sys_clk -max {max_delay} [get_ports sys_clk]
set_input_delay -clock sys_clk -min {min_delay} [get_ports sys_clk]
```

### 2.2 差分时钟

```tcl
# 差分时钟输入
create_clock -name ref_clk_p -period {period}
create_clock -name ref_clk_n -period {period}

# 差分约束
set_input_delay -clock ref_clk_p -max {max} [get_ports ref_clk_p]
```

---

## 3. 高速接口约束

### 3.1 DDR接口

```tcl
# DDR时钟
create_clock -name ddr_clk -period {period}

# 数据输出
set_output_delay -clock ddr_clk -max {max} [get_ports ddr_dq[*]]
set_output_delay -clock ddr_clk -min {min} [get_ports ddr_dq[*]]

# DQS约束
create_clock -name ddr_dqs -period {period}
set_output_delay -clock ddr_dqs -max {max} [get_ports ddr_dqs_p[*]]
```

### 3.2 SerDes接口

```tcl
# SerDes时钟
create_clock -name serdes_clk -period {period}

# TX约束
set_output_delay -clock serdes_clk -max {max} [get_ports tx_data[*]]
```

---

## 4. 普通IO约束

### 4.1 输入约束

```tcl
# 同步输入
set_input_delay -clock clk -max {max} [get_ports ctrl_*]
set_input_delay -clock clk -min {min} [get_ports ctrl_*]

# 异步输入 (需要约束setup/hold)
set_max_delay -from [get_ports async_in*] -to [all_registers] {delay}
```

### 4.2 输出约束

```tcl
# 同步输出
set_output_delay -clock clk -max {max} [get_ports data_out*]
set_output_delay -clock clk -min {min} [get_ports data_out*]
```

---

## 5. 三态信号约束

### 5.1 Bidirectional

```tcl
# 双向信号
set_direction -bidirectional [get_ports bidir_data[*]]

# 使能信号约束
set_output_delay -clock clk -max {max} [get_ports bidir_en*]
```

### 5.2 OE延迟

```tcl
# Output Enable时序
set_output_delay -clock clk -max {max_oe} [get_ports oe_n]
```

---

## 6. 引脚电气特性

### 6.1 IO标准

| 信号组 | IO标准 | 驱动强度 | 备注 |
|--------|--------|----------|------|
| 高速时钟 | LVDS_25 | 4mA | 差分 |
| DDR数据 | SSTL15 | 8mA | 匹配阻抗 |
| 普通IO | LVCMOS25 | 4mA | 默认 |
| 测试接口 | LVCMOS18 | 2mA | 低功耗 |

### 6.2 引脚属性

```tcl
# 设置IO标准
set_io_standard -standard {standard} [get_ports {port}]

# 设置驱动强度
set_drive -drive {strength} [get_ports {port}]

# 设置负载
set_load -pin_load {load} [get_ports {port}]
```

---

## 7. 信号完整性

### 7.1 阻抗匹配

```tcl
# 目标阻抗
set_impedance -target {z0} [get_nets {net}]

# 端接电阻
set_termination -term {value} [get_ports {port}]
```

### 7.2 串扰约束

```tcl
# 保持足够间距
set_crosstalk_delta -delta {delta} -clock clk [get_nets {net}]
```

---

## 8. 引脚分配表

### 8.1 详细分配

| 引脚名 | 类型 | IO标准 | 方向 | 功能 |
|--------|------|--------|------|------|
| A1 | CLK | LVDS25 | Input | 系统时钟 |
| A2 | GND | - | - | 地 |
| B1 | DATA0 | SSTL15 | Bidir | DDR数据0 |
| B2 | DATA1 | SSTL15 | Bidir | DDR数据1 |

---

## 9. 约束速查

```tcl
# IO标准设置
set_io_standard -standard LVCMOS25 [get_ports *]

# 驱动强度
set_drive 4 [get_ports {ports}]

# 引脚位置
set_location -pin {loc} [get_ports {port}]

# 负载
set_load 2.5 [get_ports {ports}]
```

---

## 10. 验证检查

```tcl
# 检查IO约束完整性
report_port -verbose

# 检查时序
report_timing -from [get_ports *] -to [all_registers]

# 检查约束覆盖率
report_constraint -all
```

---

*IO约束模板版本: v1.0*
