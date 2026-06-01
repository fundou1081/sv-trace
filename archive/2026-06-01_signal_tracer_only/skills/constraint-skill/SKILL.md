# Constraint Analysis Skill

[Description]
Comprehensive SystemVerilog constraint analysis using pyslang parser and z3 solver. Supports 8 constraint types with conflict detection.

[Trigger Phrases]
- "constraint分析", "constraint analysis"
- "分析constraint", "分析约束"
- "约束冲突", "constraint conflict"
- "z3检测"

[Capabilities]

### Constraint Types (8 types)
1. simple - Basic range constraints
2. soft - Soft constraints (can be overridden)
3. conditional - if/else constraints
4. implication - -> constraints
5. loop - foreach constraints
6. dist - distribution constraints
7. unique - unique constraints
8. solve_before - ordering constraints

### Analysis Features
- Parse constraint expressions using pyslang AST
- Extract variable-constraint relationships
- Build dependency graph between constraints
- Detect conflicts using z3 SMT solver
- Visualize relationships with graphviz

### Conflict Detection
Uses z3-solver to verify if constraints are mutually satisfiable.
Returns:
- Conflict pairs (constraint A ∩ constraint B = ∅)
- Unsatisfiable core
- Suggested fixes

[Usage]

### CLI
sv-constraint <file.sv>
sv-constraint-prob <file.sv>  # with probability analysis

### Python API
from parse import SVParser
from debug.constraint_parser_v2 import parse_constraints
from debug.probabilistic_constraint import ProbabilisticConstraintAnalyzer

# Parse file
parser = SVParser()
parser.parse_file('testbench.sv')

# Analyze constraints
cp = parse_constraints(parser)
print(cp.get_report())

# Probability analysis
analyzer = ProbabilisticConstraintAnalyzer(
    cp.constraints, 
    cp.dependencies
)
print(analyzer.get_report())

[Output Format]

Text Report:
```
======================================================================
CONSTRAINT ANALYSIS REPORT (V2 - Enhanced)
======================================================================

[Constraint Types Summary]
  simple: 24
  conditional: 4
  implication: 3
  soft: 3

[Conflicts]
  No conflicts detected
```

JSON Output:
{
  "constraint_types": {"simple": 24, ...},
  "classes": {
    "class_name": {
      "constraints": [...],
      "variables": [...]
    }
  },
  "dependencies": [...],
  "conflicts": []
}

[Constraint Class Structure]
{
  "name": "constraint_name",
  "type": "simple|soft|conditional|...",
  "variables": ["var1", "var2"],
  "expression": "raw constraint expression"
}

[Examples]

1. Basic constraint analysis:
cp = parse_constraints(parser)
for cls_name, constraints in cp.constraints.items():
    print(f"{cls_name}: {len(constraints)} constraints")

2. Check for conflicts:
if cp.detect_conflicts():
    print("Conflicts found!")

3. Probability analysis:
analyzer = ProbabilisticConstraintAnalyzer(constraints, deps)
rare = analyzer.find_rare_combinations()
print(f"Found {len(rare)} rare combinations")

[Files]
- CLI: bin/sv-constraint, bin/sv-constraint-prob
- Module: src/debug/constraint_parser_v2.py
- Probability: src/debug/probabilistic_constraint.py
- Skill: skills/constraint-skill/
