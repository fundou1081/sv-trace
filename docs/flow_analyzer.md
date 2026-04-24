# SignalFlowAnalyzer - 统一信号流分析器

## 概述

统一的信号流分析，结合依赖分析、定义引用和代码召回。

## 模型

### FlowNode

```python
@dataclass
class FlowNode:
    signal_name: str           # 信号名
    module: str               # 所属模块
    file: str                 # 文件
    line: int                # 行号
    drivers: List[dict]       # 驱动信息
    loads: List[dict]         # 负载信息
    controlling_signals: List[str]  # 控制信号
    has_bit_selection: bool   # 是否有位选择
    driven_bits: List[int]     # 驱动的位
```

### SignalFlow

```python
@dataclass
class SignalFlow:
    root_signal: str                    # 根信号
    path: str                          # 路径
    node: FlowNode                     # 节点信息
    upstream_signals: List[str]          # 上游信号
    downstream_signals: List[str]       # 下游信号
    code_snippets: List[dict]           # 相关代码片段
```

## 使用方法

```python
from trace.flow_analyzer import SignalFlowAnalyzer

analyzer = SignalFlowAnalyzer(parser)

# 追踪信号流
flow = analyzer.trace('data_out')

print(f"Root: {flow.root_signal}")
print(f"Upstream: {flow.upstream_signals}")
print(f"Downstream: {flow.downstream_signals}")

# 代码召回
for snippet in flow.code_snippets:
    print(f"Line {snippet['line']}: {snippet['code']}")
```

## ScopeExtractor - 代码召回

提取信号相关的代码上下文。

```python
from trace.flow_analyzer import ScopeExtractor

extractor = ScopeExtractor(parser)

# 提取信号及其上下文
snippets = extractor.extract_with_scope('data_out', max_lines=20)

for s in snippets:
    print(f"[{s['file']}:{s['line']}]")
    print(s['code'])
```

## 特性

- 双向信号追踪
- 代码片段召回
- 支持位选择
- 模块作用域分析

## 示例

```python
analyzer = SignalFlowAnalyzer(parser)
flow = analyzer.trace('clk_en')

# 获取完整信息
print(f"信号: {flow.root_signal}")
print(f"上游: {' -> '.join(flow.upstream_signals)}")
print(f"下游: {' -> '.join(flow.downstream_signals)}")

# 代码片段
for snippet in flow.code_snippets:
    print(f"\n{snippet['context']}:")
    print(snippet['code'])
```
