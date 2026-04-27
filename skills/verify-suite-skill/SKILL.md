# Verification Suite Skill

[Description]
Comprehensive verification suite analyzer for SystemVerilog/UVM testbenches.

[Trigger Phrases]
- "验证分析", "verification suite"
- "综合验证", "suite analysis"

[Capabilities]

### Testbench Analysis
- Component hierarchy extraction
- Agent/Monitor/Driver/Sequencer identification
- TLM connection analysis
- Phase method extraction

### Coverage Analysis
- Covergroup extraction
- Coverpoint identification
- Transition bins analysis

### Configuration
- uvm_config_db tracking
- Virtual sequence analysis
- Test configuration extraction

[Usage]

### CLI
verify-suite <design.sv>

### Python API
from parse import SVParser
from debug.verify_suite import VerifySuiteAnalyzer

parser = SVParser()
parser.parse_file('testbench.sv')

analyzer = VerifySuiteAnalyzer(parser)
report = analyzer.analyze()
print(report)

[Output Format]

Text:
```
VERIFICATION SUITE ANALYSIS
=========================

UVM Components:
  Agents:           5
  Drivers:          4
  Monitors:         5
  Sequencers:        3

Coverage:
  Covergroups:      12
  Coverpoints:      48
```

[Files]
- CLI: bin/verify-suite
- Module: src/debug/verify_suite.py
- Skill: skills/verify-suite-skill/
