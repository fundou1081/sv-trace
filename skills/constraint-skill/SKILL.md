# Constraint Analysis Skill

[Description]
Provides comprehensive constraint analysis for SystemVerilog.

[Trigger Phrases]
- "constraint分析", "constraint analysis"
- "分析constraint", "帮我分析constraint"

[Capabilities]
- Parse 8 constraint types
- Conflict detection (z3)
- Probabilistic analysis
- Visualization

[Usage]
sv-constraint <file.sv>
sv-constraint-prob <file.sv>

[Python API]
from parse import SVParser
from debug.constraint_parser_v2 import parse_constraints
cp = parse_constraints(parser)
print(cp.get_report())
