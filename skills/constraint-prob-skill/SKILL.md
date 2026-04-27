# Constraint Probabilistic Analysis Skill

[Description]
Probabilistic constraint analysis to find low-probability × high-impact combinations.

[Trigger Phrases]
- "概率分析", "probability analysis"
- "低概率组合", "rare combinations"

[Capabilities]
- Estimate activation probability per constraint type
- Find rare dependencies (joint prob < 0.1)
- Find danger zones (high indegree × low probability)
- Find rare propagation paths

[Usage]
sv-constraint-prob <file.sv>

[Python API]
from parse import SVParser
from debug.constraint_parser_v2 import parse_constraints
from debug.probabilistic_constraint import ProbabilisticConstraintAnalyzer

cp = parse_constraints(parser)
analyzer = ProbabilisticConstraintAnalyzer(cp.constraints, cp.dependencies)
print(analyzer.get_report())
