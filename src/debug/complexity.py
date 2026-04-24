"""
CyclomaticComplexity - 圈复杂度分析
"""
import sys
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


@dataclass
class ComplexityResult:
    module_name: str
    total_complexity: int = 0
    grade: str = "A"
    grade_desc: str = ""
    procedures: List['ProcedureComplexity'] = field(default_factory=list)


@dataclass
class ProcedureComplexity:
    name: str
    complexity: int
    line: int
    stmt_type: str
    grade: str = "A"
    code: str = ""


class CyclomaticComplexityAnalyzer:
    def __init__(self, parser):
        self.parser = parser
        self.results: Dict[str, ComplexityResult] = {}
    
    def analyze(self, module_name: str = None) -> Dict[str, ComplexityResult]:
        # 遍历所有解析的 tree
        for tree_key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            # 尝试读取文件内容用于行号计算
            content = ""
            if isinstance(tree_key, str) and os.path.exists(tree_key):
                try:
                    with open(tree_key, 'r') as f:
                        content = f.read()
                except:
                    pass
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                
                if 'ModuleDeclaration' in str(type(member)):
                    mod_name = self._get_module_name(member)
                    
                    if module_name and mod_name != module_name:
                        continue
                    
                    result = self._analyze_module(member, mod_name, content)
                    self.results[mod_name] = result
        
        return self.results
    
    def _get_module_name(self, module) -> str:
        if hasattr(module, 'header') and module.header:
            if hasattr(module.header, 'name'):
                name = module.header.name
                if hasattr(name, 'value'):
                    return name.value
                return str(name)
        return ""
    
    def _analyze_module(self, module, module_name: str, content: str = "") -> ComplexityResult:
        result = ComplexityResult(module_name=module_name)
        
        members = []
        if hasattr(module, 'members'):
            members = module.members
        elif hasattr(module, 'body'):
            members = module.body
        
        for i in range(len(members)):
            stmt = members[i]
            proc = self._extract_procedure_complexity(stmt, i, content)
            if proc:
                result.procedures.append(proc)
                result.total_complexity += proc.complexity
        
        result.grade = self._get_grade(result.total_complexity)
        result.grade_desc = self._get_grade_desc(result.total_complexity)
        
        for proc in result.procedures:
            proc.grade = self._get_grade(proc.complexity)
        
        return result
    
    def _get_line_number(self, stmt, content: str = "") -> int:
        try:
            token = stmt.getFirstToken()
            if token:
                loc = token.location
                offset = loc.offset
                if content:
                    return content[:offset].count('\n') + 1
                # 如果没有内容，估算行号
                return (offset // 50) + 1
        except:
            pass
        return 1
    
    def _extract_procedure_complexity(self, stmt, index: int, content: str = "") -> Optional[ProcedureComplexity]:
        stmt_type = str(type(stmt))
        
        if 'ProceduralBlock' not in stmt_type:
            return None
        
        code = ""
        if hasattr(stmt, 'statement') and stmt.statement:
            code = str(stmt.statement)
        
        if not code:
            return None
        
        proc_type = "always"
        if '@(posedge' in code or '@(negedge' in code:
            proc_type = "always_ff"
        elif '@(*)' in code or '@(*' in code:
            proc_type = "always_comb"
        
        line = self._get_line_number(stmt, content)
        complexity = self._calculate_complexity(code)
        
        return ProcedureComplexity(
            name=f"{proc_type}_{index}",
            complexity=complexity,
            line=line,
            stmt_type=proc_type,
            code=code[:60].replace('\n', ' ')
        )
    
    def _calculate_complexity(self, code: str) -> int:
        complexity = 1
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        complexity += len(re.findall(r'\bif\s*\(', code))
        complexity += len(re.findall(r'\bcase\s*\(', code))
        complexity += len(re.findall(r'\bfor\s*\(', code))
        complexity += len(re.findall(r'\bwhile\s*\(', code))
        complexity += len(re.findall(r'\bdo\s*\{', code))
        complexity += len(re.findall(r'\brepeat\s*\(', code))
        complexity += len(re.findall(r'\?[^?]+:', code))
        
        return complexity
    
    def _get_grade(self, complexity: int) -> str:
        if complexity <= 10:
            return "A"
        elif complexity <= 20:
            return "B"
        elif complexity <= 50:
            return "C"
        else:
            return "D"
    
    def _get_grade_desc(self, complexity: int) -> str:
        if complexity <= 10:
            return "低风险"
        elif complexity <= 20:
            return "中等"
        elif complexity <= 50:
            return "较高"
        else:
            return "高风险"
    
    def visualize(self, module_name: str = None) -> str:
        if not self.results:
            self.analyze()
        
        lines = ["=" * 60, "CYCLOMATIC COMPLEXITY ANALYSIS", "=" * 60]
        
        for mod_name, result in self.results.items():
            if module_name and mod_name != module_name:
                continue
            
            lines.append(f"\n📦 Module: {mod_name}")
            lines.append(f"   Total: {result.total_complexity} ({result.grade} - {result.grade_desc})")
            
            if result.procedures:
                lines.append(f"   Procedures ({len(result.procedures)}):")
                for proc in sorted(result.procedures, key=lambda x: x.complexity, reverse=True):
                    risk = "🟢" if proc.grade == "A" else "🟡" if proc.grade == "B" else "🟠" if proc.grade == "C" else "🔴"
                    lines.append(f"     {risk} [{proc.grade}] {proc.stmt_type} @L{proc.line}: {proc.complexity}")
            
            high_complex = [p for p in result.procedures if p.complexity > 20]
            if high_complex:
                lines.append(f"\n   ⚠️  High Complexity:")
                for proc in high_complex:
                    lines.append(f"     - {proc.stmt_type} (L{proc.line}): {proc.complexity}")
        
        return "\n".join(lines)
    
    def get_module_score(self, module_name: str) -> Dict:
        if module_name not in self.results:
            self.analyze(module_name)
        
        result = self.results.get(module_name)
        if not result:
            return {}
        
        return {
            "module": module_name,
            "total_complexity": result.total_complexity,
            "grade": result.grade,
            "grade_desc": result.grade_desc,
            "procedure_count": len(result.procedures),
            "avg_complexity": result.total_complexity / len(result.procedures) if result.procedures else 0,
            "high_risk_count": len([p for p in result.procedures if p.complexity > 20])
        }
    
    def suggest_refactoring(self, module_name: str = None, threshold: int = 20) -> str:
        if not self.results:
            self.analyze()
        
        lines = ["=" * 60, "REFACTORING SUGGESTIONS", "=" * 60]
        
        for mod_name, result in self.results.items():
            if module_name and mod_name != module_name:
                continue
            
            if not result.procedures:
                continue
            
            lines.append(f"\n📦 Module: {mod_name}")
            
            if result.total_complexity > threshold * 2:
                lines.append(f"  ⚠️  Total complexity {result.total_complexity} exceeds {threshold*2}")
                lines.append(f"  💡 Consider splitting this module into smaller sub-modules")
            
            high_proc = [p for p in result.procedures if p.complexity > threshold]
            if high_proc:
                lines.append(f"\n  High complexity procedures (>{threshold}):")
                for proc in high_proc:
                    lines.append(f"    - {proc.stmt_type} @L{proc.line}: complexity={proc.complexity}")
            
            always_ff_count = len([p for p in result.procedures if p.stmt_type == "always_ff"])
            always_comb_count = len([p for p in result.procedures if p.stmt_type == "always_comb"])
            
            if always_ff_count > 5:
                lines.append(f"\n  💡 {always_ff_count} always_ff blocks - group related registers")
            if always_comb_count > 5:
                lines.append(f"\n  💡 {always_comb_count} always_comb blocks - extract datapath logic")
            
            if result.total_complexity > 30:
                lines.append(f"\n  📋 Suggested split:")
                lines.append(f"     1. Extract control logic (state machines) to ctrl_{mod_name}")
                lines.append(f"     2. Extract datapath logic to dp_{mod_name}")
                lines.append(f"     3. Keep top-level for interconnection only")
            
            if not any([result.total_complexity > threshold * 2, high_proc, 
                       always_ff_count > 5, always_comb_count > 5]):
                lines.append(f"  ✅ Complexity is within acceptable range")
        
        return "\n".join(lines)
    
    def get_design_quality_report(self, module_name: str = None) -> Dict:
        if not self.results:
            self.analyze()
        
        report = {}
        
        for mod_name, result in self.results.items():
            if module_name and mod_name != module_name:
                continue
            
            issues = []
            score = 100
            
            if result.total_complexity > 50:
                score -= 30
                issues.append(f"High total complexity: {result.total_complexity}")
            elif result.total_complexity > 30:
                score -= 15
                issues.append(f"Medium total complexity: {result.total_complexity}")
            
            high_risk = len([p for p in result.procedures if p.complexity > 20])
            if high_risk > 0:
                score -= high_risk * 10
                issues.append(f"{high_risk} high-risk procedures")
            
            always_ff = len([p for p in result.procedures if p.stmt_type == "always_ff"])
            if always_ff > 8:
                score -= 10
                issues.append(f"Too many always_ff: {always_ff}")
            
            if score >= 90:
                grade, desc = "A", "优秀"
            elif score >= 75:
                grade, desc = "B", "良好"
            elif score >= 60:
                grade, desc = "C", "一般"
            else:
                grade, desc = "D", "需改进"
            
            report[mod_name] = {
                "score": score,
                "grade": grade,
                "description": desc,
                "total_complexity": result.total_complexity,
                "procedure_count": len(result.procedures),
                "issues": issues,
                "recommendations": [f"L{p.line}: Consider refactoring" for p in result.procedures if p.complexity > 20][:5]
            }
        
        return report


def analyze_complexity(parser, module_name: str = None) -> Dict:
    analyzer = CyclomaticComplexityAnalyzer(parser)
    return analyzer.analyze(module_name)
