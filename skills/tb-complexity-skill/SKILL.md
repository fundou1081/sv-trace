# TB Complexity Analysis Skill

[Description]
Analyzes UVM testbench complexity with 40+ objective metrics. Evaluates quality, performance, maintainability and testability.

[Trigger Phrases]
- "TB复杂度", "testbench complexity"
- "分析TB", "analyze testbench"
- "TB质量", "TB quality"
- "testbench评估", "验证质量"

[Capabilities]

### Code Metrics
- LOC统计 (total, code, comment, blank)
- Parameter usage (parameter, localparam)
- Comment ratio calculation

### UVM Components
- Agents, Drivers, Monitors, Sequencers
- Scoreboards, Reference Models, Subscribers
- Constraints, Covergroups, Sequences

### Class Analysis
- Class count, hierarchy depth
- Inheritance relationships
- Class reference graph

### Random Variables
- rand/randc count and names
- Constraint-variable mapping
- Variable relationship pairs

### Sequence Analysis
- Hierarchy depth
- Nested sequence starts
- Sequence macros (`uvm_do, etc)

### Quality Metrics
- comment_ratio: comments / code_lines
- assertion_density: per 1000 LOC
- covergroup_density: per 1000 LOC
- constraint_per_rand: constraints / rand_vars

### Performance Metrics
- memory_bits_total: total memory in bits
- large_memory_warning: >1MB threshold
- deep_loop_count: nested loops

### Maintainability
- avg_class_size: lines per class
- max_class_size: largest class

### Testability
- coverpoint_count: coverage points
- transition_bins: state transition bins

### Other Metrics
- Packages (count, names, import graph)
- Functions/Tasks count
- Assertion types (property, sequence, static)
- Force/Release statements
- Macros (`define, `ifdef)
- FSM state count
- Interface/Port count

[Usage]

### CLI
sv-tb-complexity <tb_file.sv>

### Python API
from verify.tb_analyzer import TBComplexityAnalyzer

# From file
analyzer = TBComplexityAnalyzer(filepath='tb.sv')

# From code string
analyzer = TBComplexityAnalyzer(code=code_string)

# Get report
print(analyzer.get_report())

# Get JSON for programmatic use
import json
data = analyzer.get_json()
print(json.dumps(data, indent=2))

[Output Format]

Text Report:
```
======================================================================
TB COMPLEXITY ANALYSIS REPORT (Comprehensive)
======================================================================

[Code Metrics]
  Total lines:         500
  Code lines:          350

[UVM Components]
  Agents:               3
  Drivers:              3
  Monitors:             3

[Quality]
  comment_ratio:       0.18
  assertion_density:   45.20

[Complexity]
  Score:              35.0
  Grade:            B (Moderate)
```

JSON Output:
{
  "code_metrics": {...},
  "uvm_components": {...},
  "quality": {...},
  "performance": {...},
  "complexity": {
    "score": 35.0,
    "grade": "B"
  }
}

[Complexity Grades]
- A: <20 (Simple)
- B: 20-40 (Moderate)
- C: 40-60 (Complex)
- D: 60-80 (Very Complex)
- F: >80 (Too Complex)

[Examples]

1. Basic analysis:
analyzer = TBComplexityAnalyzer(filepath='testbench.sv')
print(analyzer.get_report())

2. Extract specific metrics:
data = analyzer.get_json()
print(f"Grade: {data['complexity']['grade']}")
print(f"Agent count: {data['uvm_components']['agents']}")

3. Check quality warnings:
if data['quality']['comment_ratio'] < 0.1:
    print("Warning: Low comment ratio")

[Files]
- CLI: bin/sv-tb-complexity
- Module: src/verify/tb_analyzer/complexity.py
- Skill: skills/tb-complexity-skill/
