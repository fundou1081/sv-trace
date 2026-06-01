# TimingReportGenerator - 时序报告生成器

## 概述

生成时序分析报告，支持 HTML 和 JSON 格式。

## 使用方法

```python
from parse.parser import SVParser
from trace.reports import generate_report, TimingReportGenerator, ReportConfig

parser = SVParser()
parser.parse_file('design.sv')

# 方式1: 便捷函数
generate_report(parser, 'report.html', format='html', title='My Report')

# 方式2: 配置类
config = ReportConfig(
    title='Custom Report',
    output_format='html',
    include_details=True,
    max_paths=100
)
generator = TimingReportGenerator(parser, config)
html = generator.generate()
```

## 配置选项

```python
@dataclass
class ReportConfig:
    title: str = "Timing Report"
    output_format: str = "html"  # html 或 json
    include_details: bool = True
    max_paths: int = 50          # 最大显示路径数
    show_all_paths: bool = False
```

## HTML 报告

生成的 HTML 报告包含：

### 1. 摘要统计
- 寄存器数量
- 时序路径总数
- 时钟域数量
- 最大时序深度

### 2. Critical Path
红色高亮显示最深时序路径

### 3. 时钟域表格
| 域 | 时钟信号 | 寄存器数 |
|---|---|---|
| domain_a | clk_a | 5 |
| domain_b | clk_b | 3 |

### 4. 所有路径表格
| 起点 | 终点 | 时序深度 | 逻辑深度 | 路径 |
|---|---|---|---|---|
| reg_a | reg_c | 2 | 1 | reg_a → reg_b → reg_c |

### 5. CDC 分析（多时钟域）

## JSON 报告结构

```json
{
  "metadata": {
    "title": "Timing Report",
    "module": "top_module",
    "generated": "2026-04-22T16:00:00"
  },
  "summary": {
    "registers": 10,
    "timing_paths": 15,
    "clock_domains": 2,
    "max_timing_depth": 4,
    "max_logic_depth": 3
  },
  "domains": {
    "clk_a": {
      "clock": "clk_a",
      "registers": ["reg_a1", "reg_a2"]
    }
  },
  "paths": [
    {
      "start": "reg_a",
      "end": "reg_c",
      "timing_depth": 2,
      "logic_depth": 1,
      "signals": ["reg_a", "reg_b", "reg_c"]
    }
  ],
  "critical_path": {...},
  "worst_logic_path": {...},
  "cdc_analysis": [...]
}
```

## 便捷函数

```python
# 生成 HTML
generate_report(parser, 'out.html', format='html')

# 生成 JSON
generate_report(parser, 'out.json', format='json')

# 不保存，直接获取内容
html = generate_report(parser, format='html')
```
