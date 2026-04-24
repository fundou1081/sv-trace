# CDCAnalyzer - 跨时钟域分析器

## 概述

检测并分析跨时钟域（Clock Domain Crossing）路径，识别潜在风险。

## 什么是 CDC？

CDC 是数据从一个时钟域传递到另一个时钟域的现象。

```systemverilog
// 时钟域 A
always_ff @(posedge clk_a) begin
    data_a <= input_data;
    cdc_data <= data_a;  // CDC 起点
end

// 时钟域 B  
always_ff @(posedge clk_b) begin
    data_b <= cdc_data;  // CDC 终点
end
```

## 使用方法

```python
from parse.parser import SVParser
from trace.reports.cdc_analyzer import CDCAnalyzer, analyze_cdc

parser = SVParser()
parser.parse_file('multi_clock.sv')

# 方式1: 函数
report = analyze_cdc(parser)

# 方式2: 类
analyzer = CDCAnalyzer(parser)
report = analyzer.analyze()

# 生成文本报告
print(analyzer.generate_cdc_report_text())
```

## 报告结构

```python
@dataclass
class CDCReport:
    cdc_paths: List[CDCPath]       # CDC 路径列表
    safe_paths: List[CDCPath]       # 安全路径
    feedback_paths: List[CDCPath]   # 反馈路径
    domain_count: int              # 时钟域数量
    risky_paths: int               # 风险路径数量
```

```python
@dataclass
class CDCPath:
    source_domain: str      # 源时钟域
    dest_domain: str        # 目的时钟域
    start_reg: str           # 起始寄存器
    end_reg: str             # 终止寄存器
    signals: List[str]       # 路径信号
    timing_depth: int        # 时序深度
    path_type: str           # cdc / feedback / safe
    issues: List[str]        # 问题列表
```

## 路径类型

| 类型 | 说明 |
|---|---|
| `cdc` | 跨时钟域路径 |
| `feedback` | 跨域反馈路径 |
| `safe` | 安全路径 |

## 风险检测

CDCAnalyzer 自动检测以下风险：

1. **多周期路径** - `timing_depth > 1`
2. **组合逻辑** - CDC 路径中包含组合逻辑
3. **反馈路径** - 跨越时钟域的反馈环路

## 示例

```python
analyzer = CDCAnalyzer(parser)
report = analyzer.analyze()

print(f"时钟域数: {report.domain_count}")
print(f"CDC 路径: {len(report.cdc_paths)}")
print(f"风险路径: {report.risky_paths}")

for path in report.cdc_paths:
    print(f"\n{path.source_domain} → {path.dest_domain}")
    print(f"  路径: {' → '.join(path.signals)}")
    print(f"  时序深度: {path.timing_depth}")
    if path.issues:
        print("  ⚠️ 问题:")
        for issue in path.issues:
            print(f"    - {issue}")
```

## 文本报告格式

```
================================================================
CDC Analysis Report
================================================================

Clock Domains: 2
CDC Paths: 1
Risky Paths: 1
Feedback Paths: 0

------------------------------------------------------------
Cross-Clock Domain Paths:
------------------------------------------------------------

[1] clk_a → clk_b
    Path: cdc_data → data_b → data_out
    Timing Depth: 1
    ⚠️  Issues:
       - Combinational logic in CDC path
```

## 注意事项

- 需要正确提取时钟信号
- 支持 `posedge` 和 `negedge`
- 自动过滤 reset 信号
