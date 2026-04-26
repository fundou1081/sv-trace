---
name: code-quality-checker
description: 代码质量检查工具，检测多驱动、死代码、未使用信号、latch推断等问题。
---

# Code Quality Checker Skill

代码质量检查

## CLI

```bash
sv-quality check design.sv
sv-quality check design.sv --output quality_report.txt
sv-quality multi-driver design.sv
sv-quality unused design.sv
```

## Python API

```python
from lint.code_quality import CodeQualityChecker
from parse import SVParser

parser = SVParser()
parser.parse_file('design.sv')

checker = CodeQualityChecker(parser)
report = checker.analyze()

print(f"Total issues: {report.total_count}")
print(f"Critical: {report.critical_count}")
print(f"High: {report.high_count}")

output = checker.generate_report(report)
print(output)
```

## 检测的问题类型

- **multi_driver**: 多驱动冲突
- **dead_code**: 死代码
- **unused_signal**: 未使用信号
- **latch_inference**: Latch推断
- **combinational_loop**: 组合逻辑环
