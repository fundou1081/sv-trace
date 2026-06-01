# TimingPathExtractor - 时序路径提取器

## 概述

提取关键时序路径，基于数据流图分析。

## 模型

### TimingPath

```python
@dataclass
class TimingPath:
    start: str              # 起点信号
    end: str                # 终点信号
    depth: int              # 深度
    signals: List[str]       # 路径信号列表
```

### TimingInfo

```python
@dataclass
class TimingInfo:
    module: str             # 模块名
    paths: List[TimingPath]  # 所有路径
    max_depth: int          # 最大深度
    total: int             # 路径总数
    critical: str           # 关键路径描述
```

## 使用方法

```python
from trace.timing_path import TimingPathExtractor, extract_timing_paths

# 方式1: 类
extractor = TimingPathExtractor(parser)
info = extractor.analyze('module_name')

# 方式2: 函数
info = extract_timing_paths(parser, 'module_name')

print(f"Total paths: {info.total}")
print(f"Max depth: {info.max_depth}")
print(f"Critical: {info.critical}")

# 所有路径
for path in info.paths:
    print(f"  {path.start} -> {path.end} (depth={path.depth})")
```

## 算法

1. 构建数据流图 `graph[dest] = (sources, expr)`
2. 从每个终点追溯到起点
3. 计算深度（路径上的运算符数）
4. 识别关键路径

## 示例

```systemverilog
assign c = a + b;
assign d = c + e;
assign f = d + g;
```

路径：
- `a -> c -> d -> f` (depth=3)

## 注意

- 此提取器基于代码解析（非 AST），用于快速分析
- 完整分析请使用 `TimingDepthAnalyzer`
