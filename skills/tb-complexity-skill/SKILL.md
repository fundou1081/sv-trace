# TB Complexity Analysis Skill

[Description]
Analyzes UVM testbench complexity to identify potential issues.

[Trigger Phrases]
- "TB复杂度", "testbench complexity"
- "分析TB", "analyze testbench"
- "TB质量", "TB quality"

[Capabilities]
- Count lines of code (LOC)
- Analyze nesting depth
- Count UVM components (agents, sequences, etc)
- Identify complexity issues
- Calculate complexity score and grade

[Usage]
sv-tb-complexity <tb_file.sv>

[Python API]
from verify.tb_analyzer import TBComplexityAnalyzer

analyzer = TBComplexityAnalyzer(filepath='tb.sv')
print(analyzer.get_report())

[Output]
- Code metrics (LOC, comments, blanks)
- Complexity score (0-100) and grade (A-F)
- Component counts
- Warning issues
