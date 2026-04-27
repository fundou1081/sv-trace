"""TB Complexity Analyzer

Analyzes UVM testbench complexity:
- LOC (lines of code)
- Nesting depth
- Constraint complexity
- Agent count
- Configuration complexity
- Score calculation
"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class TBMetrics:
    """TB complexity metrics"""
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    max_nesting: int = 0
    avg_nesting: float = 0.0
    
    agent_count: int = 0
    constraint_count: int = 0
    assertion_count: int = 0
    covergroup_count: int = 0
    
    config_params: int = 0
    sequence_count: int = 0
    virtual_seq_count: int = 0
    
    complexity_score: float = 0.0
    complexity_grade: str = "A"
    
    issues: List[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class TBComplexityAnalyzer:
    """Analyze testbench complexity"""
    
    def __init__(self, code: str = None, filepath: str = None):
        self.code = code
        self.filepath = filepath
        self.metrics = TBMetrics()
        
        if code:
            self.analyze(code)
        elif filepath:
            self.analyze_file(filepath)
    
    def analyze(self, code: str) -> TBMetrics:
        """Analyze TB complexity"""
        self.code = code
        
        # Count lines
        self._count_lines()
        
        # Analyze nesting
        self._analyze_nesting()
        
        # Count components
        self._count_components()
        
        # Calculate complexity
        self._calculate_score()
        
        # Check issues
        self._check_issues()
        
        return self.metrics
    
    def analyze_file(self, filepath: str) -> TBMetrics:
        """Analyze TB from file"""
        with open(filepath, 'r') as f:
            code = f.read()
        return self.analyze(code)
    
    def _count_lines(self):
        """Count lines of code"""
        lines = self.code.split('\n')
        self.metrics.total_lines = len(lines)
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                self.metrics.blank_lines += 1
            elif stripped.startswith('//') or stripped.startswith('/*'):
                self.metrics.comment_lines += 1
            else:
                self.metrics.code_lines += 1
    
    def _analyze_nesting(self):
        """Analyze nesting depth"""
        max_depth = 0
        current_depth = 0
        depths = []
        
        for line in self.code.split('\n'):
            stripped = line.strip()
            
            # Count opening braces/brackets
            for c in stripped:
                if c == '{':
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif c == '}':
                    current_depth = max(0, current_depth - 1)
            
            if current_depth > 0:
                depths.append(current_depth)
        
        self.metrics.max_nesting = max_depth
        if depths:
            self.metrics.avg_nesting = sum(depths) / len(depths)
    
    def _count_components(self):
        """Count UVM components"""
        code_lower = self.code.lower()
        
        # Agents
        patterns = {
            'agent_count': r'class\s+\w+_agent\s+extends\s+uvm_agent',
            'constraint_count': r'constraint\s+\w+\s*\{',
            'assertion_count': r'\b(assert|assume|cover)\s*\(',
            'covergroup_count': r'covergroup\s+\w+',
            'config_count': r'uvm_config_db',
            'sequence_count': r'class\s+\w+_seq\s+extends\s+uvm_sequence',
            'virtual_seq': r'class\s+\w+_virt_seq\s+extends\s+uvm_sequence',
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, code_lower)
            setattr(self.metrics, key, len(matches))
    
    def _calculate_score(self):
        """Calculate complexity score"""
        score = 0.0
        
        # Lines factor (max 20)
        score += min(20, self.metrics.code_lines / 10)
        
        # Nesting factor (max 30)
        score += min(30, self.metrics.max_nesting * 3)
        
        # Components factor (max 25)
        total_components = (
            self.metrics.agent_count * 2 +
            self.metrics.constraint_count * 0.5 +
            self.metrics.assertion_count * 0.3 +
            self.metrics.covergroup_count * 1.5
        )
        score += min(25, total_components)
        
        # Configuration factor (max 15)
        score += min(15, self.metrics.config_params * 0.5)
        
        # Sequence factor (max 10)
        score += min(10, self.metrics.sequence_count * 0.5)
        
        self.metrics.complexity_score = round(score, 2)
        
        # Grade
        if score < 20:
            grade = "A (Simple)"
        elif score < 40:
            grade = "B (Moderate)"
        elif score < 60:
            grade = "C (Complex)"
        elif score < 80:
            grade = "D (Very Complex)"
        else:
            grade = "F (Too Complex)"
        
        self.metrics.complexity_grade = grade
    
    def _check_issues(self):
        """Check for complexity issues"""
        issues = []
        
        if self.metrics.max_nesting > 8:
            issues.append(f"Warning: Deep nesting ({self.metrics.max_nesting} levels)")
        
        if self.metrics.code_lines > 5000:
            issues.append(f"Warning: Large TB ({self.metrics.code_lines} LOC)")
        
        if self.metrics.constraint_count > 100:
            issues.append(f"Warning: Many constraints ({self.metrics.constraint_count})")
        
        if self.metrics.covergroup_count < 3 and self.metrics.code_lines > 1000:
            issues.append("Warning: Low coverage points")
        
        if self.metrics.agent_count > 20:
            issues.append(f"Warning: Many agents ({self.metrics.agent_count})")
        
        self.metrics.issues = issues
    
    def get_report(self) -> str:
        """Generate analysis report"""
        m = self.metrics
        
        lines = [
            "=" * 60,
            "TB COMPLEXITY ANALYSIS REPORT",
            "=" * 60,
            "",
            "[Code Metrics]",
            f"  Total lines:   {m.total_lines}",
            f"  Code lines:    {m.code_lines}",
            f"  Comments:      {m.comment_lines}",
            f"  Blank:         {m.blank_lines}",
            "",
            "[Complexity]",
            f"  Max nesting:   {m.max_nesting}",
            f"  Avg nesting:   {m.avg_nesting:.1f}",
            f"  Score:         {m.complexity_score:.1f}",
            f"  Grade:         {m.complexity_grade}",
            "",
            "[Components]",
            f"  Agents:       {m.agent_count}",
            f"  Constraints:  {m.constraint_count}",
            f"  Assertions:   {m.assertion_count}",
            f"  Covergroups:  {m.covergroup_count}",
            f"  Sequences:   {m.sequence_count}",
            f"  Virtual seqs: {m.virtual_seq_count}",
        ]
        
        if m.issues:
            lines.extend(["", "[Issues]"])
            for issue in m.issues:
                lines.append(f"  ⚠️  {issue}")
        
        return "\n".join(lines)



