"""DesignEvaluator - 综合设计评估入口。

整合模块依赖、圈复杂度等多项指标，生成综合设计质量报告。

Example:
    >>> from debug.design_evaluator import DesignEvaluator
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> evaluator = DesignEvaluator(parser)
    >>> result = evaluator.evaluate()
    >>> print(evaluator.get_summary())
"""
import sys
import os
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from .dependency.analyzer import ModuleDependencyAnalyzer
from .complexity import CyclomaticComplexityAnalyzer


class DesignEvaluator:
    """综合设计评估器。
    
    整合多个分析器，提供完整的设计质量评估。

    Attributes:
        parser: SVParser 实例
        results: 评估结果缓存
    
    Example:
        >>> evaluator = DesignEvaluator(parser)
        >>> evaluator.evaluate()
        >>> print(evaluator.get_summary())
    """
    
    def __init__(self, parser):
        """初始化评估器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.results = {}
    
    def evaluate(self, module_name: str = None) -> Dict:
        """执行完整评估。
        
        Args:
            module_name: 可选的模块名过滤
        
        Returns:
            Dict: 评估结果字典
        """
        # 1. 模块依赖分析
        dep_analyzer = ModuleDependencyAnalyzer(self.parser)
        dep_graph = dep_analyzer.analyze()
        
        # 2. 圈复杂度分析
        complexity_analyzer = CyclomaticComplexityAnalyzer(self.parser)
        complexity_analyzer.analyze()
        
        # 3. 整合结果
        self.results = {
            "dependency": {
                "graph": dep_graph,
                "stats": {
                    "total_modules": len(dep_graph.modules),
                    "root_modules": len(dep_graph.root_modules),
                    "leaf_modules": len(dep_graph.leaf_modules),
                    "cycles": len(dep_graph.cycles)
                },
                "complexity_score": dep_analyzer.get_complexity_score(),
                "fan_in_out": dep_analyzer.get_fan_in_out()
            },
            "complexity": {
                "results": complexity_analyzer.results,
                "quality_report": complexity_analyzer.get_design_quality_report()
            }
        }
        
        return self.results
    
    def get_summary(self) -> str:
        """生成评估摘要。
        
        Returns:
            str: 格式化的评估报告字符串
        """
        if not self.results:
            self.evaluate()
        
        lines = []
        lines.append("=" * 70)
        lines.append("                    DESIGN EVALUATION REPORT")
        lines.append("=" * 70)
        
        # 模块依赖部分
        dep = self.results.get("dependency", {})
        stats = dep.get("stats", {})
        comp_score = dep.get("complexity_score", {})
        
        lines.append("\n📦 MODULE DEPENDENCY")
        lines.append("-" * 50)
        lines.append(f"  Total Modules:      {stats.get('total_modules', 0)}")
        lines.append(f"  Root Modules:       {stats.get('root_modules', 0)}")
        lines.append(f"  Leaf Modules:       {stats.get('leaf_modules', 0)}")
        lines.append(f"  Dependency Score:   {comp_score.get('total_score', 0)} ({comp_score.get('grade', '-')})")
        
        if stats.get('cycles', 0) > 0:
            lines.append(f"  ⚠️  Cycles Detected:   {stats.get('cycles', 0)}")
        
        # 圈复杂度部分
        complex = self.results.get("complexity", {})
        quality = complex.get("quality_report", {})
        
        lines.append("\n📊 CODE COMPLEXITY")
        lines.append("-" * 50)
        
        for mod, q in quality.items():
            lines.append(f"\n  Module: {mod}")
            lines.append(f"    Quality Score: {q.get('score', 0)} ({q.get('grade', '-')} - {q.get('description', '')})")
            lines.append(f"    Total Complexity: {q.get('total_complexity', 0)}")
            lines.append(f"    Procedures: {q.get('procedure_count', 0)}")
            
            issues = q.get('issues', [])
            if issues:
                lines.append(f"    Issues:")
                for issue in issues:
                    lines.append(f"      - {issue}")
        
        # 综合评分
        lines.append("\n" + "=" * 70)
        lines.append("                       OVERALL ASSESSMENT")
        lines.append("=" * 70)
        
        # 计算综合评分
        dep_grade = comp_score.get('grade', 'A')
        quality_grades = [q.get('grade', 'A') for q in quality.values()]
        
        # 转换为分数
        grade_map = {'A': 90, 'B': 75, 'C': 60, 'D': 40}
        dep_score = grade_map.get(dep_grade, 90)
        quality_scores = [grade_map.get(g, 90) for g in quality_grades]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 90
        
        overall_score = int((dep_score + avg_quality) / 2)
        
        if overall_score >= 90:
            overall_grade = "A"
            overall_desc = "优秀 - 设计质量良好"
        elif overall_score >= 75:
            overall_grade = "B"
            overall_desc = "良好 - 有少量改进空间"
        elif overall_score >= 60:
            overall_grade = "C"
            overall_desc = "一般 - 建议优化"
        else:
            overall_grade = "D"
            overall_desc = "需改进 - 存在较多问题"
        
        lines.append(f"\n  🎯 Overall Score: {overall_score}/100 ({overall_grade})")
        lines.append(f"  📝 Assessment: {overall_desc}")
        
        # 风险提示
        if stats.get('cycles', 0) > 0:
            lines.append(f"\n  ⚠️  RISKS:")
            lines.append(f"    - Circular dependencies detected!")
        
        high_complex = any(q.get('score', 100) < 75 for q in quality.values())
        if high_complex:
            lines.append(f"    - High complexity in some modules")
        
        return "\n".join(lines)
    
    def get_mermaid_graph(self) -> str:
        """获取 Mermaid 依赖图。
        
        Returns:
            str: Mermaid 格式的依赖图
        """
        if not self.results:
            self.evaluate()
        
        dep_analyzer = ModuleDependencyAnalyzer(self.parser)
        dep_analyzer.analyze()
        return dep_analyzer.to_mermaid()
    
    def get_full_report(self) -> str:
        """获取完整评估报告。
        
        Returns:
            str: 完整的评估报告
        """
        if not self.results:
            self.evaluate()
        
        lines = [self.get_summary()]
        
        # 添加详细建议
        complex = self.results.get("complexity", {})
        complexity_analyzer = complex.get("results", {})
        
        if complexity_analyzer:
            for mod_name, result in complexity_analyzer.items():
                if hasattr(result, 'procedures') and result.procedures:
                    high = [p for p in result.procedures if p.complexity > 15]
                    if high:
                        lines.append(f"\n💡 Recommendations for {mod_name}:")
                        for p in high:
                            lines.append(f"  - L{p.line}: Complexity {p.complexity} - consider refactoring")
        
        return "\n".join(lines)


def evaluate_design(parser, module_name: str = None) -> Dict:
    """便捷函数：评估设计。
    
    Args:
        parser: SVParser 实例
        module_name: 可选的模块名
    
    Returns:
        Dict: 评估结果
    """
    evaluator = DesignEvaluator(parser)
    return evaluator.evaluate(module_name)


def print_evaluation(parser, module_name: str = None) -> str:
    """便捷函数：打印评估报告。
    
    Args:
        parser: SVParser 实例
        module_name: 可选的模块名
    
    Returns:
        str: 评估报告字符串
    """
    evaluator = DesignEvaluator(parser)
    return evaluator.get_full_report()
