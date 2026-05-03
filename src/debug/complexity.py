"""CyclomaticComplexity - SystemVerilog 圈复杂度分析。

计算模块和过程的圈复杂度，评估代码可维护性。

Example:
    >>> from debug.complexity import CyclomaticComplexityAnalyzer
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> analyzer = CyclomaticComplexityAnalyzer(parser)
    >>> results = analyzer.analyze()
    >>> for name, result in results.items():
    ...     print(f"{name}: {result.total_complexity} (Grade {result.grade})")
"""
import sys
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


@dataclass
class ComplexityResult:
    """复杂度分析结果数据类。
    
    Attributes:
        module_name: 模块名
        total_complexity: 总复杂度
        grade: 等级 (A/B/C/D)
        grade_desc: 等级描述
        procedures: 过程复杂度列表
    """
    module_name: str
    total_complexity: int = 0
    grade: str = "A"
    grade_desc: str = ""
    procedures: List['ProcedureComplexity'] = field(default_factory=list)


@dataclass
class ProcedureComplexity:
    """过程复杂度数据类。
    
    Attributes:
        name: 过程名
        complexity: 复杂度值
        line: 行号
        stmt_type: 语句类型
        grade: 等级
        code: 代码片段
    """
    name: str
    complexity: int
    line: int
    stmt_type: str
    grade: str = "A"
    code: str = ""


class CyclomaticComplexityAnalyzer:
    """圈复杂度分析器。
    
    计算 SystemVerilog 代码的圈复杂度，支持模块级和过程级分析。

    Attributes:
        parser: SVParser 实例
        results: 分析结果字典
    
    Example:
        >>> analyzer = CyclomaticComplexityAnalyzer(parser)
        >>> results = analyzer.analyze()
    """
    
    def __init__(self, parser):
        """初始化分析器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.results: Dict[str, ComplexityResult] = {}
    
    @staticmethod
    def extract_from_text(source: str, module_name: str = "top"):
        """从源码文本提取复杂度分析。
        
        Args:
            source: SystemVerilog 源代码字符串
            module_name: 模块名
        
        Returns:
            CyclomaticComplexityAnalyzer: 分析器实例
        """
        import pyslang
        
        try:
            tree = pyslang.SyntaxTree.fromText(source)
            
            class TextParser:
                def __init__(self, tree):
                    self.trees = {"input.sv": tree}
                    self.compilation = tree
            
            analyzer = CyclomaticComplexityAnalyzer(TextParser(tree))
            return analyzer
        except Exception as e:
            print(f"Complexity analyze error: {e}")
            return None
    
    def analyze(self, module_name: str = None) -> Dict[str, ComplexityResult]:
        """分析模块复杂度。
        
        Args:
            module_name: 可选的模块名过滤
        
        Returns:
            Dict[str, ComplexityResult]: 模块名到结果的映射
        """
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
        """获取模块名。
        
        Args:
            module: 模块节点
        
        Returns:
            str: 模块名
        """
        if hasattr(module, 'header') and module.header:
            if hasattr(module.header, 'name'):
                name = module.header.name
                if hasattr(name, 'value'):
                    return name.value
                return str(name)
        return ""
    
    def _analyze_module(self, module, module_name: str, content: str = "") -> ComplexityResult:
        """分析单个模块的复杂度。
        
        Args:
            module: 模块节点
            module_name: 模块名
            content: 源码内容
        
        Returns:
            ComplexityResult: 模块复杂度结果
        """
        result = ComplexityResult(module_name=module_name)
        
        members = getattr(module, 'members', [])
        if not members:
            return result
        
        procedure_count = 0
        total_complexity = 0
        
        for j in range(len(members)):
            member = members[j]
            if not member:
                continue
            
            member_type = str(type(member).__name__)
            
            # 检查是否是过程块 (always_ff, always_comb, always block, etc)
            is_procedure = False
            stmt_type = ""
            proc_name = ""
            base_complexity = 1
            
            if 'AlwaysBlock' in member_type or 'AlwaysFf' in member_type or 'AlwaysComb' in member_type:
                is_procedure = True
                stmt_type = member_type
                proc_name = f"always_{j}"
                base_complexity = 1
            
            elif 'ProcessStatement' in member_type or 'ProceduralTiming' in member_type:
                is_procedure = True
                stmt_type = member_type
                proc_name = f"process_{j}"
                base_complexity = 1
            
            elif 'FunctionDeclaration' in member_type:
                is_procedure = True
                stmt_type = "function"
                if hasattr(member, 'name') and member.name:
                    proc_name = str(member.name)
                else:
                    proc_name = f"func_{j}"
                base_complexity = 1
            
            elif 'TaskDeclaration' in member_type:
                is_procedure = True
                stmt_type = "task"
                if hasattr(member, 'name') and member.name:
                    proc_name = str(member.name)
                else:
                    proc_name = f"task_{j}"
                base_complexity = 1
            
            if is_procedure:
                procedure_count += 1
                complexity = base_complexity
                
                # 遍历节点计算复杂度增量
                complexity += self._count_decision_points(member)
                
                # 评估等级
                grade = self._grade_complexity(complexity)
                
                # 获取代码片段
                code = ""
                if hasattr(member, 'stmt') and member.stmt:
                    code = str(member.stmt)[:80]
                
                proc = ProcedureComplexity(
                    name=proc_name,
                    complexity=complexity,
                    line=0,  # TODO: 计算行号
                    stmt_type=stmt_type,
                    grade=grade,
                    code=code
                )
                
                result.procedures.append(proc)
                total_complexity += complexity
        
        result.total_complexity = total_complexity
        result.grade = self._grade_complexity(total_complexity)
        result.grade_desc = self._get_grade_description(result.grade)
        
        return result
    
    def _count_decision_points(self, node) -> int:
        """计算决策点数量。
        
        Args:
            node: 语法树节点
        
        Returns:
            int: 增量复杂度
        """
        complexity = 0
        
        # 这些节点类型会增加复杂度
        decision_kinds = {
            'IfStatement',
            'CaseStatement', 
            'CaseGenerateStatement',
            'LoopStatement',
            'ForeverStatement',
            'RepeatStatement',
            'WhileStatement',
            'DoWhileStatement',
            'ForStatement',
        }
        
        def visit(n):
            nonlocal complexity
            node_type = type(n).__name__
            
            # 检查决策点
            if any(k in node_type for k in decision_kinds):
                complexity += 1
            
            # 检查逻辑运算符
            if hasattr(n, 'kind') and n.kind:
                kind_name = str(n.kind.name) if hasattr(n.kind, 'name') else ""
                if any(op in kind_name for op in ['And', 'Or', 'Binary']):
                    complexity += 0.5
            
            # 递归遍历子节点
            if hasattr(n, '__iter__'):
                try:
                    for child in n:
                        visit(child)
                except TypeError:
                    pass
            
            # 尝试访问子节点属性
            for attr_name in ['consequent', 'alternate', 'body', 'statements', 'statement']:
                if hasattr(n, attr_name):
                    child = getattr(n, attr_name)
                    if child:
                        visit(child)
        
        visit(node)
        return int(complexity)
    
    def _grade_complexity(self, complexity: int) -> str:
        """评估复杂度等级。
        
        Args:
            complexity: 复杂度值
        
        Returns:
            str: 等级 (A/B/C/D)
        """
        if complexity <= 10:
            return "A"
        elif complexity <= 20:
            return "B"
        elif complexity <= 50:
            return "C"
        else:
            return "D"
    
    def _get_grade_description(self, grade: str) -> str:
        """获取等级描述。
        
        Args:
            grade: 等级字母
        
        Returns:
            str: 等级描述
        """
        descriptions = {
            "A": "Low risk - Simple, well-structured",
            "B": "Moderate risk - Maintainable",
            "C": "High risk - Complex, needs refactoring",
            "D": "Very high risk - Untestable, urgent refactor"
        }
        return descriptions.get(grade, "")
    
    def get_design_quality_report(self) -> Dict[str, Dict]:
        """获取设计质量报告。
        
        Returns:
            Dict: 设计质量评估报告
        """
        report = {}
        
        for mod_name, result in self.results.items():
            high_complex = [p for p in result.procedures if p.grade in ['C', 'D']]
            
            issues = []
            if result.grade == 'D':
                issues.append("Module has very high complexity")
            if len(high_complex) > 3:
                issues.append(f"{len(high_complex)} high-complexity procedures")
            
            report[mod_name] = {
                'score': self._grade_to_score(result.grade),
                'grade': result.grade,
                'description': result.grade_desc,
                'total_complexity': result.total_complexity,
                'procedure_count': len(result.procedures),
                'issues': issues
            }
        
        return report
    
    def _grade_to_score(self, grade: str) -> int:
        """等级转分数。
        
        Args:
            grade: 等级字母
        
        Returns:
            int: 分数 (0-100)
        """
        scores = {"A": 100, "B": 75, "C": 50, "D": 25}
        return scores.get(grade, 50)
    
    def visualize(self, module_name: str = None) -> str:
        """可视化复杂度报告。
        
        Args:
            module_name: 可选的模块名
        
        Returns:
            str: 格式化的报告字符串
        """
        if module_name:
            if module_name not in self.results:
                return f"Module '{module_name}' not found"
            results = {module_name: self.results[module_name]}
        else:
            results = self.results
        
        lines = []
        lines.append("=" * 70)
        lines.append("              CODE COMPLEXITY ANALYSIS")
        lines.append("=" * 70)
        
        for mod_name, result in sorted(results.items()):
            lines.append(f"\n📦 {mod_name}")
            lines.append("-" * 50)
            lines.append(f"  Total Complexity: {result.total_complexity}")
            lines.append(f"  Grade: {result.grade} - {result.grade_desc}")
            lines.append(f"  Procedures: {len(result.procedures)}")
            
            # 显示高复杂度过程
            high = [p for p in result.procedures if p.grade in ['C', 'D']]
            if high:
                lines.append(f"\n  ⚠️  High Complexity Procedures:")
                for p in high[:5]:
                    lines.append(f"    - {p.name}: {p.complexity} ({p.grade})")
        
        lines.append("=" * 70)
        return "\n".join(lines)
