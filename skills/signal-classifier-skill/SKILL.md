---
name: signal-classifier
description: 信号分类工具，将RTL信号分类为clock/reset/data/control/status等类别，用于快速理解设计结构。
---

# Signal Classifier Skill

信号分类工具

## CLI

```bash
sv-signal classify design.sv
sv-signal list design.sv --category clock
sv-signal report design.sv --output report.txt
```

## Python API

```python
from trace.signal_classifier import SignalClassifier
from parse import SVParser

parser = SVParser()
parser.parse_file('design.sv')

classifier = SignalClassifier()
result = classifier.classify_from_parser(parser)

print(f"Clocks: {len(result.clocks)}")
print(f"Resets: {len(result.resets)}")
print(f"Data: {len(result.data_signals)}")

report = classifier.generate_report(result, "design")
print(report)
```

## 分类规则

- **Clock**: clk, clock, *_clk
- **Reset**: rst, reset, *_rst_n
- **Data**: data, din, dout, *_data
- **Control**: en, enable, valid, ready
- **Status**: flag, status, busy, error
