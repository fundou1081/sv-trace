# DriverCollector - 驱动收集器

## 概述

DriverCollector 遍历 SystemVerilog 代码的 pyslang AST，收集所有信号驱动信息。

## 功能

- 区分阻塞赋值 (`=`) 和非阻塞赋值 (`<=`)
- 提取时钟信号
- 计算逻辑深度（运算符数量）
- 支持多种语法结构

## 使用方法

```python
from parse.parser import SVParser
from trace.driver import DriverCollector

# 解析
parser = SVParser()
parser.parse_file('design.sv')

# 收集驱动
collector = DriverCollector(parser)

# 访问驱动信息
for signal, drivers in collector.drivers.items():
    for driver in drivers:
        print(f"{signal}:")
        print(f"  kind: {driver.kind}")        # AlwaysFF, AlwaysComb, Continuous
        print(f"  assign_kind: {driver.assign_kind}")  # Blocking, Nonblocking
        print(f"  sources: {driver.sources}")  # 上游信号
        print(f"  clock: {driver.clock}")      # 时钟信号
        print(f"  operator_count: {driver.operator_count}")  # 运算符数量
```

## 模型定义

### DriverKind

| 值 | 说明 |
|---|---|
| `Continuous` | assign 语句 |
| `AlwaysComb` | always_comb 块 |
| `AlwaysFF` | always_ff 块 |
| `AlwaysLatch` | always_latch 块 |
| `Always` | always 块 |

### AssignKind

| 值 | 说明 |
|---|---|
| `Blocking` | 阻塞赋值 `=` |
| `Nonblocking` | 非阻塞赋值 `<=` |

### Driver 属性

| 属性 | 类型 | 说明 |
|---|---|---|
| `signal` | str | 信号名 |
| `kind` | DriverKind | 驱动类型 |
| `assign_kind` | AssignKind | 赋值类型 |
| `module` | str | 所属模块 |
| `sources` | List[str] | 上游信号列表 |
| `clock` | str | 时钟信号 |
| `operator_count` | int | 运算符数量 |

## 时钟提取

支持以下格式：

```systemverilog
always_ff @(posedge clk)           // clk
always_ff @(negedge clk)          // clk
always_ff @(posedge clk or negedge rst_n)  // clk (跳过复位)
always_ff @(clk)                  // clk
```

## 示例

```python
# 统计非阻塞赋值
nb_count = sum(
    1 for drivers in collector.drivers.values()
    for d in drivers 
    if d.assign_kind == AssignKind.Nonblocking
)
```
