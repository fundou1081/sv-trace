# DataPathAnalyzer - 数据路径分析器

## 概述

深度追踪数据流，支持：
- assign 语句
- always_comb / always_ff 块
- if / case 语句
- 循环
- 流水线

## 模型

### DataPathNode

```python
@dataclass
class DataPathNode:
    signal: str              # 信号名
    drivers: List[str]       # 上游驱动信号
    exprs: List[str]        # 驱动表达式
    driver_kinds: List[str]  # 驱动类型
```

### PipelineStage

```python
@dataclass
class PipelineStage:
    name: str
    signals: List[str]       # 阶段内信号
    clock: Optional[str]     # 时钟
    enable: Optional[str]    # 使能
    reset: Optional[str]      # 复位
```

### DataPath

```python
@dataclass
class DataPath:
    nodes: Dict[str, DataPathNode]  # 节点字典
    chain: List[str]               # 数据流链
    stages: List[PipelineStage]    # 流水线阶段
```

## 使用方法

```python
from trace.datapath import DataPathAnalyzer

analyzer = DataPathAnalyzer(parser)

# 分析
result = analyzer.analyze('module_name')

# 可视化
print(result.visualize())
```

## 示例输出

```
=== Data Path Analysis ===

[Pipeline Stages]
  Stage 1: stage0, clk=clk, en=valid
  Stage 2: stage1, clk=clk
  Stage 3: stage2, clk=clk

[Data Flow] input → stage0 → stage1 → stage2 → output

[Dependencies]
  input ← [input]
  stage0 ← NB input + 8'h1
  stage1 ← NB stage0 * 8'h2
  stage2 ← NB stage1 + stage0
```

## 方法

### analyze

```python
result = analyzer.analyze(module_name)
```

### get_node

```python
node = analyzer.get_node('stage0')
print(node.drivers)      # ['input']
print(node.exprs)        # ['input + 8\'h1']
print(node.driver_kinds)  # ['NB']
```

### get_chain

```python
chain = analyzer.get_chain('output')
print(' → '.join(chain))  # input → stage0 → stage1 → output
```

## 支持的语法

| 语法 | 驱动类型 |
|---|---|
| assign | `CA` (Continuous Assign) |
| always_comb | `B` (Blocking) |
| always_ff | `NB` (Nonblocking) |
| always_latch | `L` (Latch) |
| if/case | `B`/`NB` |
