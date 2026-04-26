"""
ConstraintAnalyzer - Constraint Corner Case检测器
使用sv-trace已有的解析器 + Z3进行约束分析

⚠️ 当前状态: 框架完成 (50%)
TODO:
- [x] 使用parse/constraint.py解析 ✅
- [x] 范围分析 ✅
- [ ] Z3完整集成
"""
import re
import sys
import os
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# 尝试导入sv-trace的约束解析器
try:
    from parse.constraint import ConstraintExtractor
    PARSE_AVAILABLE = True
except ImportError:
    PARSE_AVAILABLE = False
    ConstraintExtractor = None

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
    probability: float  # 估计触发概率
    examples: List[Dict]
    suggestion: str = ""

class ConstraintAnalyzer:
    """
    Constraint分析器 -Corner Case检测
    
    使用sv-trace的ConstraintExtractor + Z3
    """
    
    def __init__(self):
        self.constraint_extractor = None
        self.constraints = []
        
        if PARSE_AVAILABLE:
            self.constraint_extractor = ConstraintExtractor()
    
    def load_constraints(self, filepath: str) -> List[Dict]:
        """从文件加载约束
        
        使用sv-trace的ConstraintExtractor
        """
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
        
        # 1. 使用regex进行基础分析
        issues.extend(self._check_conflicts(constraint_code))
        issues.extend(self._check_range_issues(constraint_code))
        issues.extend(self._check_dependency_issues(constraint_code))
        
        # 2. 使用Z3进行精确检查 (如果可用)
        if Z3_AVAILABLE:
            issues.extend(self._z3_analysis(constraint_code))
        
        return issues
    
    def _check_conflicts(self, code: str) -> List[CornerCase]:
        """检查逻辑冲突"""
        issues = []
        
        # 检查if/else if条件是否互斥
        if_matches = list(re.finditer(r'if\s*\((.+?)\)', code))
        
        for i, m1 in enumerate(if_matches):
            for m2 in if_matches[i+1:]:
                cond1 = m1.group(1)
                cond2 = m2.group(1)
                
                # 检查是否有重叠条件
                terms1 = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', cond1))
                terms2 = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', cond2))
                common = terms1 & terms2
                
                if common:
                    issues.append(CornerCase(
                        issue_type=IssueType.CONFLICT,
                        description=f"条件 '{cond1}' 和 '{cond2}' 可能重叠，共享变量: {common}",
                        probability=0.5,
                        examples=[],
                        suggestion="确认这些条件确实互斥，或使用 else if"
                    ))
        
        return issues
    
    def _check_range_issues(self, code: str) -> List[CornerCase]:
        """检查范围问题"""
        issues = []
        
        # 提取inside范围
        ranges = []
        for match in re.finditer(r'(\w+)\s+inside\s*\{\[(\d+):(\d+)\]\}', code):
            var = match.group(1)
            min_val = int(match.group(2))
            max_val = int(match.group(3))
            ranges.append({'var': var, 'min': min_val, 'max': max_val})
        
        # 检查范围无交集 (同一变量的不同约束)
        var_ranges = {}
        for r in ranges:
            var = r['var']
            if var not in var_ranges:
                var_ranges[var] = []
            var_ranges[var].append(r)
        
        for var, rngs in var_ranges.items():
            if len(rngs) > 1:
                # 检查是否无交集
                combined_min = max(r['min'] for r in rngs)
                combined_max = min(r['max'] for r in rngs)
                
                if combined_min > combined_max:
                    issues.append(CornerCase(
                        issue_type=IssueType.EMPTY,
                        description=f"变量 '{var}' 的约束范围无交集",
                        probability=0.0,
                        examples=[],
                        suggestion=f"调整 {var} 的约束范围 [{rngs[0]['min']}:{rngs[0]['max']}] 和 [{rngs[1]['min']}:{rngs[1]['max']}]"
                    ))
        
        # 检查反向范围
        for match in re.finditer(r'(\w+)\s*<\s*(\w+)', code):
            v1, v2 = match.group(1), match.group(2)
            # 检查是否有 v < v 这样的错误
            if v1 == v2:
                issues.append(CornerCase(
                    issue_type=IssueType.UNSATISFIABLE,
                    description=f"' {v1} < {v2} ' 永远为假",
                    probability=0.0,
                    examples=[],
                    suggestion="应该是变量范围比较"
                ))
        
        return issues
    
    def _check_dependency_issues(self, code: str) -> List[CornerCase]:
        """检查依赖问题"""
        issues = []
        
        # 检查可能的循环依赖: A < B && B < A
        if match1 := re.search(r'(\w+)\s*<\s*(\w+)', code):
            v1, v2 = match1.group(1), match1.group(2)
            if v2 + ' < ' + v1 in code:
                issues.append(CornerCase(
                    issue_type=IssueType.UNSATISFIABLE,
                    description=f"循环依赖: {v1} < {v2} 但 {v2} < {v1}",
                    probability=0.0,
                    examples=[],
                    suggestion="确保比较方向正确"
                ))
        
        # 检查A != B && A == B冲突
        if '!=' in code and '==' in code:
            # 简单检查
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
        issues = []
        
        if not Z3_AVAILABLE:
            return issues
        
        # 使用sv-trace的解析器
        if not self.constraint_extractor:
            return issues
        
        # 简化的Z3分析
        # TODO: 完整的约束到Z3转换
        
        return issues
    
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
        
        # 简单的: inside {[min:max]} 转换
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
        
        # 提取范围计算概率
        ranges = []
        for match in re.finditer(r'(\w+)\s+inside\s*\{\[(\d+):(\d+)\]\}', constraint):
            min_val = int(match.group(2))
            max_val = int(match.group(3))
            ranges.append(max_val - min_val + 1)
        
        # 简单的概率估计 (不精确但快速)
        if not ranges:
            return 0.5
        
        # 假设32位随机
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
        
        # 按严重程度分组
        critical = [i for i in issues if i.issue_type == IssueType.UNSATISFIABLE]
        empty = [i for i in issues if i.issue_type == IssueType.EMPTY]
        conflicts = [i for i in issues if i.issue_type == IssueType.CONFLICT]
        rare = [i for i in issues if i.issue_type == IssueType.VERY_RARE]
        
        if critical:
            lines.append("## 🔴 无法满足")
            for i in critical:
                lines.append(f"- {i.description}")
                lines.append(f"  建议: {i.suggestion}")
            lines.append("")
        
        if empty:
            lines.append("## 🟠 空范围")
            for i in empty:
                lines.append(f"- {i.description}")
                lines.append(f"  建议: {i.suggestion}")
            lines.append("")
        
        if conflicts:
            lines.append("## 🟡 潜在冲突")
            for i in conflicts:
                lines.append(f"- {i.description}")
                lines.append(f"  概率: {i.probability:.1%}")
            lines.append("")
        
        if rare:
            lines.append("## ℹ️ 低触发概率")
            for i in rare:
                lines.append(f"- {i.description}")
                lines.append(f"  概率: {i.probability:.1%}")
        
        return '\n'.join(lines)

# 使用示例
if __name__ == "__main__":
    # 检查依赖
    print("="*50)
    print("依赖检查:")
    print(f"  sv-trace constraint parser: {'✅' if PARSE_AVAILABLE else '❌'}")
    print(f"  Z3 solver: {'✅' if Z3_AVAILABLE else '❌'}")
    print("="*50)
    
    # 示例约束
    example = """
    class test_constraint;
        rand bit[7:0] data;
        rand bit[7:0] length;
        
        constraint data_c {
            data inside {[10:100]};
        }
        
        constraint length_c {
            length inside {[50:200]};
            length < data;
        }
    endclass
    """
    
    if PARSE_AVAILABLE:
        analyzer = ConstraintAnalyzer()
        print(analyzer.generate_report(example))
