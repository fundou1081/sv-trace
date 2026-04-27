# SV-Trace Project Index

## Overview
SV-Trace is a SystemVerilog static analysis library for RTL design analysis, testbench quality evaluation, and constraint conflict detection.

## Quick Access

### Constraint Analysis
- [constraint-skill](constraint-skill/SKILL.md) - Constraint parsing + z3 conflict detection
- [constraint-prob-skill](constraint-prob-skill/SKILL.md) - Probability analysis for constraints

### Testbench Analysis
- [tb-complexity-skill](tb-complexity-skill/SKILL.md) - TB complexity with 40+ metrics
- [verify-suite-skill](verify-suite-skill/SKILL.md) - Verification suite analyzer

### RTL Analysis
- [datapath-skill](datapath-skill/SKILL.md) - RTL data path extraction + corner case
- [signal-classifier-skill](signal-classifier-skill/SKILL.md) - Signal classification
- [code-quality-skill](codequality-skill/SKILL.md) - Code quality metrics

### CDC Analysis
- [cdc-doc-skill](cdc-doc-skill/SKILL.md) - Clock domain crossing documentation

### Timing
- [timing-equivalence](timing-equivalence/SKILL.md) - Timing equivalence checking
- [timing-fix-guide](timing-fix-guide/SKILL.md) - Timing issue fixes

### Other Tools
- [bug-tracker-skill](bug-tracker-skill/SKILL.md) - Bug tracking
- [rtl-2-assertion](rtl-2-assertion/SKILL.md) - RTL to assertion conversion
- [spec-checker](spec-checker/SKILL.md) - Specification checking

## CLI Tools

| CLI | Description | Skill |
|-----|-------------|-------|
| sv-constraint | Constraint analysis | constraint-skill |
| sv-constraint-prob | Constraint probability | constraint-prob-skill |
| sv-datapath | Data path analysis | datapath-skill |
| sv-tb-complexity | TB complexity | tb-complexity-skill |
| sv-quality | Code quality | codequality-skill |
| sv-signal | Signal classification | signal-classifier-skill |

## Installation

```bash
pip install pyslang>=10.0 z3-solver>=4.16 graphviz
```

## Usage Example

```python
from parse import SVParser
from verify.tb_analyzer import TBComplexityAnalyzer

analyzer = TBComplexityAnalyzer(filepath='testbench.sv')
print(analyzer.get_report())
```
