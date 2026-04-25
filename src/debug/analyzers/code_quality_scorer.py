"""
CodeQualityScorer - 代码质量评分器
评估设计质量: 可读性、可测试性、可维护性、CDC安全性
"""

import sys
import os
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))


class QualityScore:
    """质量评分"""
    def __init__(self):
        self.readability = 0      # 可读性
        self.testability = 0      # 可测试性
        self.maintainability = 0 # 可维护性
        self.cdc_safety = 0      # CDC安全性
        self.total = 0            # 总分
    
    def to_dict(self) -> Dict:
        return {
            "readability": self.readability,
            "testability": self.testability,
            "maintainability": self.maintainability,
            "cdc_safety": self.cdc_safety,
            "total": self.total
        }


@dataclass
class QualityIssue:
    """质量问题"""
    category: str
    severity: str
    line: int
    message: str
    suggestion: str


class CodeQualityScorer:
    """代码质量评分器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self) -> Tuple[QualityScore, List[QualityIssue]]:
        """分析代码质量"""
        score = QualityScore()
        issues = []
        
        # 分析每个模块
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            # 读取源文件
            try:
                with open(path if path else path, 'r') as f:
                    lines = f.readlines()
            except:
                lines = []
            
            # 评分
            self._check_readability(lines, score, issues)
            self._check_testability(lines, score, issues)
            self._check_maintainability(lines, score, issues)
            self._check_cdc_safety(lines, score, issues)
        
        # 计算总分(加权平均)
        score.total = (
            score.readability * 0.25 +
            score.testability * 0.30 +
            score.maintainability * 0.20 +
            score.cdc_safety * 0.25
        )
        
        return score, issues
    
    def _check_readability(self, lines: List[str], score: QualityScore, issues: List[QualityIssue]):
        """检查可读性"""
        total_lines = len([l for l in lines if l.strip() and not l.strip().startswith('//')])
        if total_lines == 0:
            return
        
        # 检查注释比例
        comment_lines = len([l for l in lines if l.strip().startswith('//')])
        comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
        
        if comment_ratio > 0.2:
            score.readability += 30
        elif comment_ratio > 0.1:
            score.readability += 20
        else:
            issues.append(QualityIssue(
                category="readability",
                severity="medium",
                line=0,
                message=f"Low comment ratio: {comment_ratio:.1%}",
                suggestion="Add comments to explain logic"
            ))
            score.readability += 10
        
        # 检查行长度
        long_lines = len([l for l in lines if len(l) > 120])
        if long_lines < total_lines * 0.1:
            score.readability += 20
        else:
            score.readability += 10
    
    def _check_testability(self, lines: List[str], score: QualityScore, issues: List[QualityIssue]):
        """检查可测试性"""
        total_lines = len([l for l in lines if l.strip()])
        if total_lines == 0:
            return
        
        # 检查是否有测试点(输出信号)
        has_outputs = any('output' in l.lower() for l in lines)
        has_inputs = any('input' in l.lower() for l in lines)
        
        if has_outputs and has_inputs:
            score.testability += 30
        elif has_outputs:
            score.testability += 20
            issues.append(QualityIssue(
                category="testability",
                severity="low",
                line=0,
                message="No input signals found",
                suggestion="Ensure design has clear inputs"
            ))
        else:
            score.testability += 10
        
        # 检查是否有时钟和复位
        has_clk = any('clk' in l.lower() or 'clock' in l.lower() for l in lines)
        has_rst = any('rst' in l.lower() or 'reset' in l.lower() for l in lines)
        
        if has_clk:
            score.testability += 10
        if has_rst:
            score.testability += 10
    
    def _check_maintainability(self, lines: List[str], score: QualityScore, issues: List[QualityIssue]):
        """检查可维护性"""
        total_lines = len([l for l in lines if l.strip()])
        if total_lines == 0:
            return
        
        # 检查模块大小
        if 50 < total_lines < 500:
            score.maintainability += 30
        elif total_lines > 1000:
            score.maintainability += 10
            issues.append(QualityIssue(
                category="maintainability",
                severity="medium",
                line=0,
                message=f"Module too large: {total_lines} lines",
                suggestion="Consider splitting into smaller modules"
            ))
        else:
            score.maintainability += 20
        
        # 检查信号命名
        short_names = len([l for l in lines if re.search(r'\b[a-z]\b', l) and 'logic' in l])
        if short_names > 5:
            issues.append(QualityIssue(
                category="maintainability",
                severity="low",
                line=0,
                message="Many single-letter signal names",
                suggestion="Use descriptive signal names"
            ))
            score.maintainability += 10
        else:
            score.maintainability += 20
    
    def _check_cdc_safety(self, lines: List[str], score: QualityScore, issues: List[QualityIssue]):
        """检查CDC安全性"""
        total_lines = len([l for l in lines if l.strip()])
        if total_lines == 0:
            return
        
        # 检查always_ff使用
        always_ff_count = len([l for l in lines if 'always_ff' in l])
        always_latch_count = len([l for l in lines if 'always_latch' in l])
        always_comb_count = len([l for l in lines if 'always_comb' in l])
        
        # 优先使用always_ff
        if always_ff_count > 0:
            score.cdc_safety += 30
        if always_latch_count == 0:
            score.cdc_safety += 20  # 没有latch是好的
        else:
            issues.append(QualityIssue(
                category="cdc_safety",
                severity="high",
                line=0,
                message=f"Found {always_latch_count} always_latch blocks",
                suggestion="Replace always_latch with always_ff for better timing"
            ))
            score.cdc_safety += 10
        
        # 检查跨时钟域
        always_blocks = [l for l in lines if '@(posedge' in l or '@(negedge' in l]
        if len(set(always_blocks)) > 2:
            issues.append(QualityIssue(
                category="cdc_safety",
                severity="medium",
                line=0,
                message=f"Multiple clock domains: {len(set(always_blocks))}",
                suggestion="Ensure proper CDC protection for cross-clock signals"
            ))
            score.cdc_safety += 10
        else:
            score.cdc_safety += 20
    
    def print_report(self, score: QualityScore, issues: List[QualityIssue]):
        """打印报告"""
        print("\n" + "="*60)
        print("Code Quality Report")
        print("="*60)
        
        print(f"\nScores:")
        for k, v in score.to_dict().items():
            print(f"  {k}: {v}/100")
        
        if issues:
            print(f"\nIssues ({len(issues)}):")
            for issue in issues:
                print(f"  [{issue.severity.upper()}] {issue.category}")
                print(f"    {issue.message}")
                print(f"    Suggestion: {issue.suggestion}")
        
        print("\n" + "="*60)


__all__ = ['CodeQualityScorer', 'QualityScore', 'QualityIssue']
