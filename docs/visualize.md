# GraphVisualizer - 流程图可视化

## 概述

生成 Graphviz DOT 格式的流程图。

## GraphNode

```python
@dataclass
class GraphNode:
    id: str                 # 唯一ID
    label: str             # 显示标签
    shape: str = "box"     # 形状
    style: str = ""        # 样式
    color: str = ""        # 颜色
    fillcolor: str = ""   # 填充色
```

### 形状选项

| 值 | 说明 |
|---|---|
| `box` | 矩形（寄存器） |
| `oval` | 椭圆（普通信号） |
| `diamond` | 菱形（条件） |
| `parallelogram` | 平行四边形（输入/输出） |

## 使用方法

```python
from trace.visualize import GraphVisualizer, GraphNode

viz = GraphVisualizer()

# 添加节点
viz.add_node(GraphNode(
    id="reg_a",
    label="reg_a",
    shape="box",
    fillcolor="#E3F2FD"
))

# 添加边
viz.add_edge("reg_a", "reg_b", "data")

# 生成 DOT
dot = viz.to_dot("my_graph")

# 保存
viz.save("graph.dot")

# 渲染 PNG
viz.render("graph.png")
```

## DOT 输出示例

```dot
digraph dataflow {
  rankdir=LR;
  
  reg_a [label="reg_a" shape=box fillcolor=#E3F2FD];
  reg_b [label="reg_b" shape=box fillcolor=#E3F2FD];
  
  reg_a -> reg_b [label="data"];
}
```

## 预定义颜色

```python
from trace.visualize import COLORS

COLORS = {
    'register': '#BBDEFB',      # 寄存器
    'input': '#C8E6C9',          # 输入
    'output': '#FFE0B2',         # 输出
    'combinational': '#F5F5F5',  # 组合逻辑
    'clock': '#9C27B0',          # 时钟
    'reset': '#F44336',          # 复位
}
```

## 完整示例

```python
from trace.visualize import GraphVisualizer, GraphNode, COLORS

viz = GraphVisualizer()

# 流水线可视化
for i, reg in enumerate(registers):
    viz.add_node(GraphNode(
        id=reg,
        label=reg,
        shape="box",
        fillcolor=COLORS['register']
    ))
    
    if i > 0:
        viz.add_edge(prev_reg, reg, "data")

dot = viz.to_dot("pipeline")
viz.save("pipeline.dot")
```
