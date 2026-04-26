"""
ConstraintAnalyzer - Constraint Corner Case检测器
使用sv-trace已有的解析器 + Z3进行约束分析
"""
import re
import sys
import os
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Z3导入
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
    DEPENDENCY = "dependency"

@dataclass
class CornerCase:
    issue_type: IssueType
    description: str
    probability: float
    examples: List[Dict]
    suggestion: str = ""

class ConstraintAnalyzer:
    """Constraint分析器 - Corner Case检测"""
    
    def __init__(self, parser=None):
        self.parser = parser
        self.constraints = []
        
        # 延迟导入ConstraintExtractor
        self.constraint_extractor = None
        if parser:
            try:
                from parse.constraint import ConstraintExtractor
                self.constraint_extractor = ConstraintExtractor(parser)
            except Exception as e:
                print(f"ConstraintExtractor加载失败: {e}")
    
    def load_constraints(self, filepath: str) -> List[Dict]:
        """从文件加载约束"""
        if not self.constraint_extractor:
            return []
        
        try:
            constraints = self.constraint_extractor.extract_constraints(filepath)
            self.constraints = constraints
            return constraints
        except Exception as e:
            print(f"加载失败: {e}")
            return []
    
    def analyze_constraint(self, constraint_code: str) -> List[CornerCase]:
        """分析约束，检测corner case"""
        issues = []
        
        # 基础分析
        issues.extend(self._check_conflicts(constraint_code))
        issues.extend(self._check_range_issues(constraint_code))
        issues.extend(self._check_dependency_issues(constraint_code))
        
        # Z3分析
        if Z3_AVAILABLE and self.parser:
            issues.extend(self._z3_analysis(constraint_code))
        
        return issues
    
    def _check_conflicts(self, code: str) -> List[CornerCase]:
        """检查逻辑冲突"""
        issues = []
        
        if_matches = list(re.finditer(r'if\s*\((.+?)\)', code))
        
        for i, m1 in enumerate(if_matches):
            for m2 in if_matches[i+1:]:
                cond1 = m1.group(1)
                cond2 = m2.group(1)
                
                terms1 = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', cond1))
                terms2 = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', cond2))
                common = terms1 & terms2
                
                if common:
                    issues.append(CornerCase(
                        issue_type=IssueType.CONFLICT,
                        description=f"条件可能重叠，共享变量: {common}",
                        probability=0.5,
                        examples=[],
                        suggestion="确认条件互斥"
                    ))
        
        return issues
    
    def _check_range_issues(self, code: str) -> List[CornerCase]:
        """检查范围问题"""
        issues = []
        
        # 提取inside���围
        ranges = []
        for match in re.finditer(r'(\w+)\s+inside\s*\{\[(\d+):(\d+)\]\}', code):
            var = match.group(1)
            min_val = int(match.group(2))
            max_val = int(match.group(3))
            ranges.append({'var': var, 'min': min_val, 'max': max_val})
        
        # 检查var < var2 这种比较
        for match in re.finditer(r'(\w+)\s*<\s*(\w+)', code):
            v1, v2 = match.group(1), match.group(2)
            if v1 == v2:
                issues.append(CornerCase(
                    issue_type=IssueType.UNSATISFIABLE,
                    description=f"'{v1} < {v1}' 永远为假",
                    probability=0.0,
                    examples=[],
                    suggestion="修复比较条件"
                ))
        
        return issues
    
    def _check_dependency_issues(self, code: str) -> List[CornerCase]:
        """检查依赖问题"""
        issues = []
        
        # 检查循环依赖: A < B && B < A
        for match in re.finditer(r'(\w+)\s*<\s*(\w+)', code):
            v1, v2 = match.group(1), match.group(2)
            if v2 + ' < ' + v1 in code:
                issues.append(CornerCase(
                    issue_type=IssueType.UNSATISFIABLE,
                    description=f"循环依赖: {v1} < {v2} 但 {v2} < {v1}",
                    probability=0.0,
                    examples=[],
                    suggestion="确保比较方向正确"
                ))
        
        # 检查可能的冲突
        if '!=' in code and '==' in code:
            issues.append(CornerCase(
                issue_type=IssueType.CONFLICT,
                description="注意 '!=' 和 '==' 可能冲突",
                probability=0.3,
                examples=[],
                suggestion="确保不会同时满足"
            ))
        
        return issues
    
    def _z3_analysis(self, code: str) -> List[CornerCase]:
        """使用Z3进行深度分析"""
        if not Z3_AVAILABLE:
            return []
        
        # TODO: 完整的Z3集成
        return []
    
    def check_satisfiability(self, constraints: List[str]) -> Dict:
        """检查约束是否可满足"""
        if not Z3_AVAILABLE:
            return {'satisfiable': None, 'message': 'Z3未安装'}
        
        solver = z3.Solver()
        
        for c in constraints:
            try:
                expr = self._parse_constraint_to_z3(c)
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
                'message': '约束无解 (unsat)',
                'model': None
            }
    
    def _parse_constraint_to_z3(self, constraint: str):
        """将约束转换为Z3表达式"""
        if not Z3_AVAILABLE or not constraint:
            return None
        
        match = re.search(r'(\w+)\s+inside\s*\{\[(\d+):(\d+)\]\}', constraint)
        if match:
            var = match.group(1)
            min_val = int(match.group(2))
            max_val = int(match.group(3))
            
            z3_var = z3.Int(var)
            return z3.And(z3_var >= min_val, z3_var <= max_val)
        
        return None
    
    def estimate_probability(self, constraint: str) -> float:
        """估计约束被满足的概率"""
        if not constraint:
            return 1.0
        
        ranges = []
        for match in re.finditer(r'(\w+)\s+inside\s*\{\[(\d+):(\d+)\]\}', constraint):
            min_val = int(match.group(2))
            max_val = int(match.group(3))
            ranges.append(max_val - min_val + 1)
        
        if not ranges:
            return 0.5
        
        total = 2**32
        valid = 1
        for r in ranges:
            valid *= r
        
        prob = valid / (total ** len(ranges))
        
        return min(prob, 1.0)
    
    def generate_report(self, constraint_code: str) -> str:
        """生成分析报告"""
        issues = self.analyze_constraint(constraint_code)
        
        lines = ["# Constraint Corner Case分析报告", ""]
        
        if not issues:
            lines.append("✅ 未发现明显问题")
            return '\n'.join(lines)
        
        critical = [i for i in issues if i.issue_type == IssueType.UNSATISFIABLE]
        empty = [i for i in issues if i.issue_type == IssueType.EMPTY]
        conflicts = [i for i in issues if i.issue_type == IssueType.CONFLICT]
        
        if critical:
            lines.append("## 🔴 无法满足")
            for i in critical:
                lines.append(f"- {i.description}")
                lines.append(f"  建议: {i.suggestion}")
            lines.append("")
        
        if conflicts:
            lines.append("## 🟡 潜在冲突")
            for i in conflicts:
                lines.append(f"- {i.description}")
                lines.append(f"  概率: {i.probability:.1%}")
        
        return '\n'.join(lines)

if __name__ == "__main__":
    print("依赖检查:")
    print(f"  Z3 solver: {'✅' if Z3_AVAILABLE else '❌'}")
    
    # 测试
    analyzer = ConstraintAnalyzer()
    
    test = """
    class test_data_constraint;
        rand bit[7:0] value;
        constraint value_c { value inside {[10:50]}; }
    endclass
    """
    
    print(analyzer.generate_report(test))
