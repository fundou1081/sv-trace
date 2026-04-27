# Code Quality Analysis Skill

[Description]
Evaluates SystemVerilog code quality metrics and coding standards compliance.

[Trigger Phrases]
- "代码质量", "code quality"
- "质量分析", "quality analysis"
- "lint检查", "linting"

[Capabilities]

### Quality Metrics
- Line counts (total, code, comment, blank)
- Comment ratio
- Naming convention checks
- Module complexity scoring

### Standards Compliance
- Clock naming (clk_, clock)
- Reset naming (rst_, reset_, rst_n)
- Signal naming conventions
- Module naming conventions

### Complexity Analysis
- Module size (lines per module)
- Port count
- Nesting depth
- Parameter usage

### Issue Detection
- Unused signals
- Unconnected ports
- Incomplete case statements
- Unreachable code

[Usage]

### CLI
sv-quality <file.sv>

### Python API
from parse import SVParser
from debug.complexity import ComplexityAnalyzer

parser = SVParser()
parser.parse_file('design.sv')

analyzer = ComplexityAnalyzer(parser)
report = analyzer.analyze()
print(report)

[Output Format]

Text:
```
CODE QUALITY REPORT
==================
Total lines:     1000
Code lines:      750
Comments:        150
Comment ratio:   0.20

Quality Score:   85/100
Grade:          B (Good)
```

[Files]
- CLI: bin/svquality
- Module: src/debug/complexity.py
- Skill: skills/code-quality-skill/
