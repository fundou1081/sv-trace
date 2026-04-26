"""
ConstraintAnalyzer - Constraint Corner Case检测器
使用Z3进行约束分析，检测潜在的corner case
"""
import re
from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum

Z3_AVAILABLE = False
try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    z3 = None

class IssueType(Enum):
    UNSATISFIABLE = "unsatisfiable"
    VERY_RARE = "very_rare"
    CONFLICT = "conflict"
    EMPTY = "empty"

@dataclass
class CornerCase:
    issue_type: IssueType
    description: str
    probability: float
    examples: List[Dict]
    suggestion: str = ""

class ConstraintAnalyzer:
    def __init__(self):
        self.problem_patterns = {}
    
    def analyze_constraint(self, constraint_code: str) -> List[CornerCase]:
        issues = []
        
        if not Z3_AVAILABLE:
            issues.append(CornerCase(
                issue_type=IssueType.UNSATISFIABLE,
                description="Z3未安装，无法精确分析",
                probability=0.0,
                examples=[],
                suggestion="pip install z3-solver"
            ))
            return issues
        
        issues.extend(self._check_conflicts(constraint_code))
        issues.extend(self._check_range_issues(constraint_code))
        
        return issues
    
    def _check_conflicts(self, code: str) -> List[CornerCase]:
        issues = []
        
        if match := re.search(r'if\s*\((.+?)\)\s*\{.*?else\s+if\s*\((.+?)\)', code, re.DOTALL):
            cond1, cond2 = match.group(1), match.group(2)
            terms1 = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', cond1))
            terms2 = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', cond2))
            
            if terms1 & terms2:
                issues.append(CornerCase(
                    issue_type=IssueType.CONFLICT,
                    description=f"条件可能重叠",
                    probability=0.5,
                    examples=[],
                    suggestion="确认条件互斥"
                ))
        
        return issues
    
    def _check_range_issues(self, code: str) -> List[CornerCase]:
        issues = []
        
        ranges = []
        for match in re.finditer(r'inside\s*\{\[(\d+):(\d+)\]\}', code):
            ranges.append({'min': int(match.group(1)), 'max': int(match.group(2))})
        
        for i, r1 in enumerate(ranges):
            for r2 in ranges[i+1:]:
                if r1['max'] < r2['min'] or r2['max'] < r1['min']:
                    issues.append(CornerCase(
                        issue_type=IssueType.EMPTY,
                        description=f"范围 {r1} 和 {r2} 无交集",
                        probability=0.0,
                        examples=[],
                        suggestion="调整范围"
                    ))
        
        return issues
    
    def check_satisfiability(self, constraints: List[str]) -> Dict:
        if not Z3_AVAILABLE:
            return {'satisfiable': None, 'message': 'Z3未安装'}
        
        solver = z3.Solver()
        
        for c in constraints:
            try:
                expr = self._parse_to_z3(c)
                if expr:
                    solver.add(expr)
            except:
                pass
        
        result = solver.check()
        
        if result == z3.sat:
            model = solver.model()
            return {
                'satisfiable': True,
                'message': '约束可满足',
                'model': {str(d): model[d] for d in model}
            }
        else:
            return {
                'satisfiable': False,
                'message': '约束无解',
                'model': None
            }
    
    def _parse_to_z3(self, expr: str):
        if not Z3_AVAILABLE or not expr:
            return None
        
        if '<=' in expr:
            parts = expr.split('<=')
            try:
                return z3.And(
                    z3.Int(parts[0].strip()) >= 0,
                    z3.Int(parts[0].strip()) <= int(parts[1].strip())
                )
            except:
                pass
        
        return None
    
    def estimate_probability(self, constraint: str) -> float:
        if not constraint:
            return 1.0
        
        ranges = []
        for match in re.finditer(r'inside\s*\{\[(\d+):(\d+)\]\}', constraint):
            ranges.append({'min': int(match.group(1)), 'max': int(match.group(2))})
        
        if not ranges:
            return 0.5
        
        total_options = 2**32
        valid_options = sum(r['max'] - r['min'] + 1 for r in ranges)
        
        return min(valid_options / total_options, 1.0)
    
    def generate_report(self, constraint_code: str) -> str:
        issues = self.analyze_constraint(constraint_code)
        
        lines = ["# Constraint Corner Case分析报告", ""]
        
        if not issues:
            lines.append("✅ 未发现明显问题")
            return '\n'.join(lines)
        
        critical = [i for i in issues if i.issue_type == IssueType.UNSATISFIABLE]
        
        if critical:
            lines.append("## 问题")
            for i in critical:
                lines.append(f"- {i.description}")
                lines.append(f"  建议: {i.suggestion}")
        
        return '\n'.join(lines)

if __name__ == "__main__":
    if Z3_AVAILABLE:
        print("✅ Z3 已安装")
    else:
        print("❌ Z3 未安装, pip install z3-solver")
