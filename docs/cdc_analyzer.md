# CDCAnalyzer - 跨时钟域分析器

## 功能

检测设计中的跨时钟域(CDC)问题

## 支持的问题类型

| 类型 | 严重性 | 说明 |
|------|--------|------|
| MULTI_DRIVER_CONFLICT | CRITICAL/HIGH | 多驱动冲突 |
| MULTI_CLOCK_DOMAIN | HIGH | 跨时钟域驱动 |
| MULTI_BIT_CROSSING | MEDIUM |多位信号跨域 |
| METASTABILITY_RISK | MEDIUM | 亚稳态风险 |

## 使用方法

```python
from parse import SVParser
from debug.analyzers.cdc import CDCAnalyzer

parser = SVParser()
parser.parse_file('design.sv')

cdc = CDCAnalyzer(parser)
report = cdc.analyze()

# 打印报告
cdc.print_report(report)

# 获取问题列表
issues = cdc.detect_issues()

# 检查特定信号
drivers = cdc.check_multi_driver('signal_name')
```

## 检测逻辑

1. **always_ff多驱动** → CRITICAL
   - 同一信号被多个always_ff块驱动
   - 建议: 使用MUX或generate逻辑合并驱动

2. **always_comb多驱动** → HIGH
   - 同一信号被多个always_comb块驱动
   - 建议: 使用单个always_comb或移至always_ff

3. **always_ff + always_comb混合** → HIGH
   - 建议: 确保时钟域隔离或统一使用一种风格

## 输出示例

```
CDC Analysis Report
============================================================

Statistics:
  total_signals_analyzed: 5
  multi_driver_signals: 1
  total_issues: 1
  critical_issues: 1
  high_issues: 0

Issues (1):
  [CRITICAL] data_out
    Signal 'data_out' driven by 2 always_ff blocks
    Type: multi_driver_conflict
    Drivers: 2
    Fix: Use MUX or generate logic to combine drivers from different clock domains
    Lines: [92, 148]

Recommendations:
  • CRITICAL: Fix 1 signals with multiple always_ff drivers
```

## 测试用例

| 用例 | 预期结果 |
|------|----------|
| 两个always_ff驱动同一信号 | CRITICAL |
| 两个always_comb驱动同一信号 | HIGH |
| 单个驱动 | 无问题 |

## 限制

- 暂不支持assign语句的多驱动检测
- 暂不支持generate语句内的驱动
- 需要实际运行解析器获取准确的时钟信息
