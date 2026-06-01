# RTL Data Path Analysis Skill

[Description]
Analyzes RTL data paths to extract data flow, detect corner cases, and perform probabilistic analysis on paths.

[Trigger Phrases]
- "data path分析", "datapath analysis"
- "分析数据通路", "数据流"
- "corner case检测", "数据通路分析"

[Capabilities]

### Data Path Extraction
- Extract operation units (ADD, MUL, MUX, REG, FIFO)
- Build directed graph of data flow
- Identify data path boundaries

### Graph Analysis
- Node: Operation unit with type and name
- Edge: Data flow direction with conditions
- SCC: Strongly Connected Components (loops/feedback)

### Probability Analysis
- Estimate activation probability per path
- Find rare paths (low probability × high impact)
- Detect danger zones (high indegree × low probability)

### Corner Case Detection
- Long combinational paths
- Feedback loops
- Starvation risks in arbitration

[Usage]

### CLI
sv-datapath <file.sv>

### Python API
from parse import SVParser
from trace.data_path import analyze_data_path

# Parse and analyze
parser = SVParser()
parser.parse_file('design.sv')

analyzer = analyze_data_path(parser)
print(analyzer.get_report())

# Get graph data
graph_data = analyzer.get_graph_data()

# Visualize
analyzer.visualize('output.png')

[Output Format]

Text Report:
```
==================================================
RTL DATA PATH ANALYSIS
==================================================

Nodes: 17
Edges: 46
SCCs: 0

[Critical Paths]
  path_1: 5 stages

[Danger Zones]
  module.reg_file [P=0.12]
```

JSON Output:
{
  "nodes": [...],
  "edges": [...],
  "sccs": [...],
  "metrics": {
    "node_count": 17,
    "edge_count": 46,
    "max_depth": 5
  }
}

[Node Structure]
{
  "id": "node_1",
  "type": "ADD|MUL|MUX|REG|FIFO",
  "name": "module.signal",
  "module": "module_name"
}

[Edge Structure]
{
  "from": "node_1",
  "to": "node_2", 
  "condition": "enable",
  "probability": 0.85
}

[Examples]

1. Basic data path analysis:
analyzer = analyze_data_path(parser)
print(analyzer.get_report())

2. Find critical paths:
critical = analyzer.find_critical_paths()
for path in critical:
    print(f"Path: {' -> '.join(path)}")

3. Visualize data flow:
analyzer.visualize('datapath.png')

4. Get probability metrics:
data = analyzer.get_graph_data()
rare_paths = [n for n in data['nodes'] if n.get('prob', 1) < 0.1]

[Files]
- CLI: bin/sv-datapath
- Module: src/trace/data_path/
  - extractor.py: Data path extraction
  - graph.py: Graph construction
  - analyzer.py: Probability analysis
- Skill: skills/datapath-skill/
