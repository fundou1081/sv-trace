# BitSelect - 位选分析器

## 概述

分析 SystemVerilog 中的位选择信号，支持：
- 固定位选择：`signal[3]`
- 位范围：`signal[7:0]`
- 索引变量：`signal[idx]`

## BitSelect 类

```python
@dataclass
class BitSelect:
    signal_name: str      # 信号名
    select_expr: str       # 选择表达式
    msb: int              # 最高位
    lsb: int              # 最低位
    is_single_bit: bool   # 单bit
    is_range: bool        # 范围选择
    is_index: bool        # 索引变量
```

## 方法

```python
# 获取宽度
width = bit_select.get_width()

# 字符串表示
print(bit_select)  # signal[3:0]
```

## 使用方法

```python
from trace.bitselect import BitSelectExtractor

extractor = BitSelectExtractor(parser)

# 提取表达式中的所有位选
selects = extractor.extract("data[7:0] & mask[3:2]")

for bs in selects:
    print(f"{bs.signal_name}[{bs.msb}:{bs.lsb}]")
    print(f"  width: {bs.get_width()}")
```

## 示例

```python
# 输入
expr = "packet[15:8]"

# 解析结果
select = BitSelect(
    signal_name="packet",
    select_expr="15:8",
    msb=15,
    lsb=8,
    is_range=True
)

print(select)  # packet[15:8]
print(select.get_width())  # 8
```
