# LoadTracer - 负载追踪器

## 概述

追踪信号的加载点（Load），即信号被使用的地方。

## Load 模型

```python
@dataclass
class Load:
    signal: str           # 负载信号名
    kind: str            # 负载类型
    line: int           # 行号
    context: str        # 上下文
```

## 使用方法

```python
from trace.load import LoadTracer

tracer = LoadTracer(parser)

# 查找信号的负载
loads = tracer.find_load('data_in')

for load in loads:
    print(f"{load.signal} at line {load.line}")
    print(f"  Context: {load.context}")
```

## 示例

```systemverilog
always_ff @(posedge clk) begin
    reg_a <= data_in;      // Load: data_in 被使用
    reg_b <= data_in + 1;   // Load: data_in 被使用
end
```

解析结果：

```python
loads = tracer.find_load('data_in')
# [
#     Load(signal='data_in', kind='NonblockingAssign', line=2),
#     Load(signal='data_in', kind='NonblockingAssign', line=3)
# ]
```

## 负载类型

| 类型 | 说明 |
|---|---|
| `NonblockingAssign` | 非阻塞赋值 RHS |
| `BlockingAssign` | 阻塞赋值 RHS |
| `ContinuousAssign` | assign 语句 |
| `PortConnection` | 端口连接 |
