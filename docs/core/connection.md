# ConnectionTracer - 连接追踪器

## 概述

追踪模块实例化和接口连接关系。

## 模型

### Instance

```python
@dataclass
class Instance:
    name: str                    # 实例名
    module_type: str             # 模块类型
    connections: List[Connection]  # 连接列表
    parameters: Dict[str, str]   # 参数
```

### Connection

```python
@dataclass
class Connection:
    source: str    # 源信号
    dest: str      # 目的信号
    signal: str    # 连接信号
```

## 使用方法

```python
from trace.connection import ConnectionTracer

tracer = ConnectionTracer(parser)

# 所有实例
for name, inst in tracer.instances.items():
    print(f"Instance: {inst.name}")
    print(f"  Type: {inst.module_type}")
    print(f"  Parameters: {inst.parameters}")
    
    # 连接
    for conn in inst.connections:
        print(f"  {conn.source} -> {conn.dest}")
```

## 示例

```systemverilog
// 实例化
my_fifo #(
    .DEPTH(32),
    .WIDTH(8)
) u_fifo (
    .clk(clk),
    .rst_n(rst_n),
    .din(data_in),
    .dout(data_out)
);
```

解析结果：

```python
Instance(
    name="u_fifo",
    module_type="my_fifo",
    parameters={"DEPTH": "32", "WIDTH": "8"},
    connections=[
        Connection(source="clk", dest="clk"),
        Connection(source="data_in", dest="din"),
        Connection(source="data_out", dest="dout")
    ]
)
```

## 支持的语法

- 模块实例化
- 参数化模块
- 接口连接
- 命名端口连接
