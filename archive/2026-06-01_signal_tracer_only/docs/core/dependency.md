# DependencyAnalyzer - 信号依赖分析器

## 概述

分析信号的双向依赖关系：
- **前向依赖** (depends_on)：驱动这个信号的信号
- **后向依赖** (influences)：受这个信号影响的信号

## 模型

### SignalDependency

```python
@dataclass
class SignalDependency:
    signal: str              # 信号名
    depends_on: List[str]    # 前向依赖
    influences: List[str]   # 后向依赖
    source_signals: List[str]  # 源头信号
    sink_signals: List[str]    # 汇信号
```

## 使用方法

```python
from trace.dependency import DependencyAnalyzer

analyzer = DependencyAnalyzer(parser)

# 分析信号依赖
dep = analyzer.analyze('data_out')

print(f"Signal: {dep.signal}")
print(f"Depends on: {dep.depends_on}")
print(f"Influences: {dep.influences}")
print(f"Source signals: {dep.source_signals}")
print(f"Sink signals: {dep.sink_signals}")
```

## 示例

```
input_a ──┐
          ├──→ reg_a ──→ reg_b ──→ output_z
input_b ──┘
```

```python
# 分析 reg_b
dep = analyzer.analyze('reg_b')

# depends_on: [reg_a]      # 驱动 reg_b 的信号
# influences: [output_z]   # reg_b 影响的信号
# source_signals: [input_a, input_b]  # 源头
# sink_signals: [output_z]           # 汇点
```

## 依赖链分析

```python
# 追溯前向依赖链
forward_chain = analyzer.find_forward_chain('output_z')

# 追溯后向依赖链
backward_chain = analyzer.find_backward_chain('input_a')

# 完整依赖树
tree = analyzer.build_dependency_tree('start_signal')
```

## 可视化

```python
# 生成依赖图 DOT
dot = analyzer.to_dot('data_out')
```
