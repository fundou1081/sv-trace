# DataFlowTracer - 数据流分析器

## 概述

连接 Driver 和 Load，构建完整的数据流图。

## 模型

### DataFlow

```python
@dataclass
class DataFlow:
    signal_name: str           # 信号名
    drivers: List[Driver]      # 驱动点
    loads: List[Load]         # 加载点
    paths: List[Dict]          # 路径信息
```

## 方法

### find_flow

```python
flow = tracer.find_flow('data_out')
print(f"Signal: {flow.signal_name}")
print(f"Drivers: {len(flow.drivers)}")
print(f"Loads: {len(flow.loads)}")
```

### find_flow_chain

```python
# 递归追踪数据流
chain = tracer.find_flow_chain('data_out', max_depth=10)

for step in chain:
    print(f"{step['from']} -> {step['to']} ({step['driver']})")
```

## 示例

```python
from trace.dataflow import DataFlowTracer

tracer = DataFlowTracer(parser)

# 单信号追踪
flow = tracer.find_flow('data_out')

# 完整链
chain = tracer.find_flow_chain('data_out')

# 输出
for step in chain:
    print(f"{step['from']} → {step['to']}")
```

## 数据流可视化

```python
flow = tracer.find_flow('clk_en')
print(f"Drivers:")
for d in flow.drivers:
    print(f"  {d.signal} ({d.driver_kind})")
print(f"Loads:")
for l in flow.loads:
    print(f"  {l.signal}")
```
