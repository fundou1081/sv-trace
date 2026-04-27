# RTL Data Path Analysis Skill

[Description]
Analyzes RTL data paths to find low-probability corner cases.

[Trigger Phrases]
- "data path分析", "datapath analysis"
- "分析数据通路", "corner case检测"

[Capabilities]
- Extract data path elements from RTL
- Build directed graph
- Probabilistic analysis (rare SCC, danger zones)
- Identify corner cases

[Usage]
sv-datapath <file.sv>

[Python API]
from parse import SVParser
from trace.data_path import analyze_data_path

parser = SVParser()
parser.parse_file('design.sv')
analyzer = analyze_data_path(parser)
print(analyzer.get_report())
