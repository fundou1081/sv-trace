"""
Coverage激励建议器 - 框架
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class CoverageType(Enum):
    LINE = "line"
    BRANCH = "branch"
    FSM = "fsm"
    CONDITION = "condition"

@dataclass
class CoverageTarget:
    coverage_type: CoverageType
    file: str
    line: int
    module: str = ""

@dataclass
class StimulusSuggestion:
    description: str
    input_signals: List[str]
    expected_values: Dict[str, str]
    priority: str
    confidence: float
    reasoning: str = ""

class CoverageStimulusSuggester:
    def __init__(self):
        self.parser = None
        self.driver_collector = None
    
    def load_design(self, filepaths):
        """加载设计"""
        from parse import SVParser
        self.parser = SVParser()
        for fp in filepaths:
            self.parser.parse_file(fp)
        from trace.driver import DriverCollector
        self.driver_collector = DriverCollector(self.parser)
        return True
    
    def analyze_target(self, target: CoverageTarget) -> List[StimulusSuggestion]:
        suggestions = []
        
        # 简单正则提取
        source = self.parser.get_source(target.file) if self.parser else ""
        lines = source.split('\n') if source else []
        
        if target.line <= len(lines):
            line_content = lines[target.line - 1]
            
            # if条件
            if 'if' in line_content:
                match = re.search(r'if\s*\((.+?)\)', line_content)
                if match:
                    cond = match.group(1)
                    signals = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', cond)
                    suggestions.append(StimulusSuggestion(
                        description=f"让条件为真: {cond}",
                        input_signals=signals,
                        expected_values={s: "1" for s in signals},
                        priority="high", confidence=0.6,
                        reasoning="执行if分支"
                    ))
        
        return suggestions
    
    def suggest_stimulus(self, target):
        suggestions = self.analyze_target(target)
        lines = [f"# Coverage激励建议"]
        for s in suggestions:
            lines.append(f"- {s.description}")
        return '\n'.join(lines)

print("✅ OK")
