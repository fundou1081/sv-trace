# Constraint Probabilistic Analysis Skill

[Description]
Probabilistic analysis of SystemVerilog constraints to find low-probability × high-impact combinations that may be under-tested.

[Trigger Phrases]
- "概率分析", "probability analysis"
- "低概率组合", "rare combinations"
- "约束概率", "constraint probability"

[Capabilities]

### Probability Analysis
- Estimate activation probability per constraint type
- Calculate joint probability for constraint combinations
- Find rare dependencies (P < 0.1)
- Identify danger zones (high indegree × low probability)

### Rare Path Analysis
- Trace variable-constraint relationships
- Find paths where low-probability constraints affect critical signals
- Calculate path probability

### Metrics
- Activation probability per constraint type
- Joint probability for constraint pairs
- Danger zone scores
- Rare path rankings

[Usage]

### CLI
sv-constraint-prob <file.sv>

### Python API
from parse import SVParser
from debug.constraint_parser_v2 import parse_constraints
from debug.probabilistic_constraint import ProbabilisticConstraintAnalyzer

parser = SVParser()
parser.parse_file('testbench.sv')

cp = parse_constraints(parser)
analyzer = ProbabilisticConstraintAnalyzer(
    cp.constraints,
    cp.dependencies
)

print(analyzer.get_report())

# Get JSON
data = analyzer.get_json()

[Output Format]

Text:
```
============================================================
PROBABILISTIC CONSTRAINT ANALYSIS
============================================================

[1] Rare Dependencies (p < 0.1)
----------------------------------------
  soft_override.c_hard_range -> dyn_array.c_size: P=0.0032

[2] Danger Zones
----------------------------------------
  bit_select.c_bits: in_deg=39, P=0.40
```

JSON:
{
  "rare_dependencies": [
    {"from": "c1", "to": "c2", "probability": 0.0032}
  ],
  "danger_zones": [
    {"constraint": "c_bits", "indegree": 39, "probability": 0.40}
  ]
}

[Examples]

1. Find rare combinations:
rare = analyzer.find_rare_combinations(threshold=0.1)
for r in rare:
    print(f"{r['path']}: P={r['probability']}")

2. Get danger zones:
zones = analyzer.find_danger_zones()
for z in zones:
    print(f"Zone: {z['name']}, Risk: {z['score']}")

3. Full analysis:
data = analyzer.get_json()
print(f"Rare paths: {len(data['rare_paths'])}")
print(f"Danger zones: {len(data['danger_zones'])}")

[Files]
- CLI: bin/sv-constraint-prob
- Module: src/debug/probabilistic_constraint.py
- Skill: skills/constraint-prob-skill/
