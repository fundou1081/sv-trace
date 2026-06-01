# Signal Classification Skill

[Description]
Classifies SystemVerilog signals into categories for analysis and documentation.

[Trigger Phrases]
- "信号分类", "signal classification"
- "分析信号", "classify signals"
- "信号类型"

[Capabilities]

### Signal Types
- **Data signals**: data_* , din, dout, payload
- **Control signals**: valid, ready, enable, start
- **Address signals**: addr_*, address
- **Clock signals**: clk, clock
- **Reset signals**: rst, reset, rst_n
- **Status signals**: status, flag, busy
- **Configuration**: config_*, mode, sel

### Analysis
- Count signals per category
- Identify signal relationships
- Extract bit widths
- Find register signals

[Usage]

### CLI
sv-signal <file.sv>

### Python API
from parse import SVParser
from debug.signal_classifier import SignalClassifier

parser = SVParser()
parser.parse_file('design.sv')

classifier = SignalClassifier(parser)
results = classifier.classify()

for category, signals in results.items():
    print(f"{category}: {len(signals)} signals")

[Output Format]

Text:
```
SIGNAL CLASSIFICATION
====================
Data signals:    12
Control signals:  8
Address signals: 4
Clock signals:    2
Reset signals:    2
```

JSON:
{
  "data": ["data_in", "data_out", ...],
  "control": ["valid", "ready", ...],
  "clock": ["clk"],
  ...
}

[Files]
- CLI: bin/sv-signal
- Module: src/debug/signal_classifier.py
- Skill: skills/signal-classifier-skill/
