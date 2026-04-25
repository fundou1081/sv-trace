# CDCAnalyzer - 跨时钟域分析器 v5

## 功能

检测设计中的跨时钟域(CDC)问题

## 支持的问题类型

| 类型 | 严重性 | 说明 |
|------|--------|------|
| MULTI_CLOCK_DOMAIN | CRITICAL | 不同时钟域always_ff驱动 |
| LATCH_FF_MIX | CRITICAL | Latch与FF混用 |
| MULTI_DRIVER_CONFLICT | HIGH/MEDIUM | 多驱动冲突 |
| SAME_CLOCK_MULTI_DRIVER | HIGH | 同时钟域多驱动 |
| MULTI_DRIVER_CONFLICT | LOW/INFO | 同块内case分支 |

## 严重性等级

- **CRITICAL**: 必须立即修复
- **HIGH**: 需要审查
- **MEDIUM**: 建议修复
- **LOW**: 可忽略
- **INFO**: 信息级(通常正常)

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

# 获取问题
issues = cdc.detect_issues()

# 检查特定信号
drivers = cdc.check_multi_driver('signal_name')
```

## 检测逻辑

1. **多always_ff驱动** → 检查是否同一块
   - 不同块 → CRITICAL (跨时钟域)
   - 同块内 → INFO (可能是case分支)

2. **always_latch + always_ff** → CRITICAL
   - Latch与FF混用是危险模式

3. **多always_comb驱动**
   - 不同块 → HIGH
   - 同块内 → LOW

## 已知限制

| 限制 | 说明 | 解决方案 |
|------|------|----------|
| 行号不可靠 | Parser返回内部行号 | ADR-019 |
| 同块检测 | 依赖行间距判断 | 需要Parser支持 |

## 测试结果

| 测试 | 结果 |
|------|------|
| 双时钟always_ff | ✅ CRITICAL |
| 三时钟always_ff | ✅ CRITICAL |
| Latch+FF混合 | ✅ CRITICAL |
| 双always_comb | ✅ HIGH |
| 单驱动 | ✅ 无问题 |
| 条件驱动 | ✅ 无问题 |
| 多信号无交叉 | ✅ 无问题 |

**通过率: 6/7 (85%)**

## ADR

- ADR-019: CDCAnalyzer边界检测改进
