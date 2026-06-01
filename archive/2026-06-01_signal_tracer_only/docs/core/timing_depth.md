# TimingDepthAnalyzer - 时序深度分析器

## 概述

基于 DriverCollector 的结果，分析寄存器间的时序路径和深度。

## 核心概念

### 时序深度 (Timing Depth)

寄存器到寄存器之间的**时钟周期数**。

```
path: reg_a → reg_b → reg_c → reg_d
      ↑_________3 个寄存器___________↑
      
时序深度 = 3
```

### 逻辑深度 (Logic Depth)

路径上组合逻辑**运算符的总数**。

```
reg_a <= data_in + 8'h1     // +1
reg_b <= reg_a * 8'h2       // +1
reg_c <= reg_b + reg_a       // +1

reg_c → reg_b → reg_a 路径的逻辑深度 = 3
```

## 使用方法

```python
from parse.parser import SVParser
from trace.timing_depth import TimingDepthAnalyzer

parser = SVParser()
parser.parse_file('design.sv')

analyzer = TimingDepthAnalyzer(parser)

# 获取所有时序路径
paths = analyzer.analyze()

# 最深时序路径
critical = analyzer.find_critical_path()

# 最深逻辑路径
worst_logic = analyzer.find_worst_logic_path()

# 按域分析
paths_in_domain = analyzer.analyze(domain='clk_a')
```

## TimingPath 对象

```python
@dataclass
class TimingPath:
    start_reg: str      # 起始寄存器
    end_reg: str        # 终止寄存器
    timing_depth: int   # 时序深度
    logic_depth: int    # 逻辑深度
    signals: List[str]  # 完整路径
    domains: List[str]  # 经过的时钟域
```

## 示例

```python
# 分析结果
for path in analyzer.analyze():
    print(f"{path.start_reg} → {path.end_reg}")
    print(f"  时序深度: {path.timing_depth}")
    print(f"  逻辑深度: {path.logic_depth}")
    print(f"  路径: {' → '.join(path.signals)}")

# 关键路径
critical = analyzer.find_critical_path()
print(f"Critical: {critical.start_reg} → {critical.end_reg}")
print(f"时序深度: {critical.timing_depth}, 逻辑深度: {critical.logic_depth}")
```

## 数据结构

### flow_graph

数据流图，表示 `signal ← sources` 的依赖关系：

```python
flow_graph = {
    'reg_a': [],              # 无上游依赖
    'reg_b': ['reg_a'],       # reg_b 依赖 reg_a
    'reg_c': ['reg_b', 'reg_a'],  # reg_c 依赖 reg_b 和 reg_a
}
```

### edge_ops

边的运算符数量 `(src, dest) → count`：

```python
edge_ops = {
    ('data_in', 'reg_a'): 1,   # reg_a <= data_in + ...
    ('reg_a', 'reg_b'): 1,      # reg_b <= reg_a * ...
}
```

## 时钟域

```python
# 访问时钟域信息
for domain_name, domain in analyzer.domains.items():
    print(f"域: {domain_name}")
    print(f"  时钟: {domain.clock}")
    print(f"  寄存器: {domain.registers}")
```
