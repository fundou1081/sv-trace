# 寄存器定义模板 (RDL格式)

## 使用说明
本模板定义了标准的寄存器描述格式，可导出为SystemRDL、UVM寄存器模型等。

---

## 寄存器定义

### CTRL - 控制寄存器
```
// Address: 0x00
// Reset: 0x00000000
// Description: {description}

// Field: EN - 使能位
//   [0] - EN: 模块使能
//   [1] - MODE: 工作模式
//   [7:2] - Reserved
//   [15:8] - DIV: 分频系数
//   [31:16] - Reserved
```

| 字段名 | 位宽 | 复位值 | 访问类型 | 描述 |
|--------|------|--------|----------|------|
| EN | 1 | 0 | RW | 模块使能 |
| MODE | 1 | 0 | RW | 工作模式 |
| DIV | 8 | 0 | RW | 分频系数 |
| Reserved | 22 | 0 | RO | 保留 |

---

### STAT - 状态寄存器
```
// Address: 0x04
// Reset: 0x00000000
// Description: {description}

// Field: BUSY - 忙标志
//   [0] - BUSY: 忙标志
//   [1] - DONE: 完成标志
//   [2] - ERR: 错误标志
//   [31:16] - Reserved
```

| 字段名 | 位宽 | 复位值 | 访问类型 | 描述 |
|--------|------|--------|----------|------|
| BUSY | 1 | 0 | RO | 忙标志 |
| DONE | 1 | 0 | RO | 完成标志 |
| ERR | 1 | 0 | RO | 错误标志 |
| ERR_CODE | 8 | 0 | RO | 错误码 |
| Reserved | 21 | 0 | RO | 保留 |

---

### DATA - 数据寄存器
```
// Address: 0x08
// Reset: 0x00000000
// Description: {description}
```

| 字段名 | 位宽 | 复位值 | 访问类型 | 描述 |
|--------|------|--------|----------|------|
| DATA | 32 | 0 | RW | 数据 |

---

## 寄存器映射表

| 地址 | 名称 | 访问 | 描述 |
|------|------|------|------|
| 0x00 | CTRL | RW | 控制寄存器 |
| 0x04 | STAT | RO | 状态寄存器 |
| 0x08 | DATA | RW | 数据寄存器 |
| 0x0C | INT_EN | RW | 中断使能 |
| 0x10 | INT_STAT | RW1C | 中断状态 |

---

## 访问规则

### 访问类型说明
- **RO**: 只读
- **WO**: 只写
- **RW**: 读写
- **RW1C**: 写1清零
- **RW1S**: 写1置位
- **WO1**: 只写1

### 注意事项
1. 保留位读取返回0
2. 写入保留位无效
3. 上电后所有寄存器复位

---

## 寄存器字段定义

### 详细字段描述

#### EN - 模块使能
```
Range: 0-1
Default: 0

0 = 模块禁用
1 = 模块使能
```

#### MODE - 工作模式
```
Range: 0-3
Default: 0

0 = Normal mode
1 = Test mode
2 = Low power mode
3 = Reserved
```

#### DIV - 分频系数
```
Range: 1-255
Default: 1

分频系数 = DIV + 1
示例: DIV=9 → 10分频
```

---

## UVM寄存器模型生成

```systemverilog
// UVM寄存器定义示例
class {module}_reg_model extends uvm_reg_block;
    rand uvm_reg_field ctrl_en;
    rand uvm_reg_field ctrl_mode;
    rand uvm_reg_field ctrl_div;
    rand uvm_reg_field stat_busy;
    rand uvm_reg_field stat_done;
    // ...
endclass
```

---

*RDL模板版本: v1.0*
