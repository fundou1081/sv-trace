"""
CodeQualityScorer - 代码质量评分器 v2
基于客观指标评估设计质量
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
        # 可读性 (0-100)
        self.readability = 0
        self.comment_ratio = 0.0      # 注释比例
        self.avg_line_length = 0.0   # 平均行长度
        self.signal_naming_score = 0 # 信号命名评分
        
        # 可测试性 (0-100)
        self.testability = 0
        self.io_ratio = 0.0          # IO比例
        self.controllability = 0     # 可控性
        self.observability = 0      # 可观测性
        
        # 可维护性 (0-100)
        self.maintainability = 0
        self.module_size = 0        # 模块大小评分
        self.nesting_depth = 0      # 嵌套深度
        self.hierarchy_score = 0    # 层次结构
        
        # CDC安全性 (0-100)
        self.cdc_safety = 0
        self.ff_ratio = 0.0         # always_ff比例
        self.latch_count = 0        # latch数量
        self.clock_domain_count = 0 # 时钟域数量
        
        self.total = 0


@dataclass
class QualityIssue:
    """质量问题"""
    category: str
    severity: str  # critical, high, medium, low
    line: int
    metric: str     # 具体的度量指标
    value: float   # 当前值
    threshold: float # 阈值
    message: str
    suggestion: str


@dataclass
class QualityMetric:
    """质量指标"""
    name: str
    value: float
    min_val: float
    max_val: float
    weight: float
    unit: str = ""
    
    def to_score(self) -> float:
        """归一化到0-100"""
        if self.max_val == self.min_val:
            return 50 if self.value > 0 else 0
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return max(0, min(100, ratio * 100))


class CodeQualityScorer:
    """代码质量评分器 v2 - 基于客观指标"""
    
    # 阈值定义
    THRESHOLDS = {
        # 可读性
        "comment_ratio": {"min": 0.05, "max": 0.4, "ideal": 0.15},
        "avg_line_length": {"min": 30, "max": 100, "ideal": 60},
        "max_line_length": 120,
        
        # 可测试性
        "io_ratio": {"min": 0.05, "max": 0.5, "ideal": 0.2},
        "ctrl_points": {"min": 1, "max": 20, "ideal": 5},
        
        # 可维护性
        "module_lines": {"min": 20, "max": 1000, "ideal": 200},
        "max_nesting": {"min": 1, "max": 6, "ideal": 3},
        
        # CDC安全性
        "ff_ratio": {"min": 0.5, "max": 1.0, "ideal": 0.9},
        "latch_count": 0,
        "clock_domains": {"min": 1, "max": 4, "ideal": 1},
    }
    
    def __init__(self, parser):
        self.parser = parser
        self.metrics = []
    
    def analyze(self) -> Tuple[QualityScore, List[QualityIssue]]:
        """分析代码质量"""
        score = QualityScore()
        issues = []
        
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
            except:
                continue
            
            if not lines:
                continue
            
            # 收集原始指标
            metrics = self._collect_metrics(lines)
            self.metrics = metrics
            
            # 计算评分
            self._score_readability(lines, metrics, score, issues)
            self._score_testability(lines, metrics, score, issues)
            self._score_maintainability(lines, metrics, score, issues)
            self._score_cdc_safety(lines, metrics, score, issues)
        
        # 计算总分(加权)
        score.total = (
            score.readability * 0.20 +
            score.testability * 0.25 +
            score.maintainability * 0.20 +
            score.cdc_safety * 0.35  # CDC安全性权重最高
        )
        
        return score, issues
    
    def _collect_metrics(self, lines: List[str]) -> Dict:
        """收集客观指标"""
        content = ''.join(lines)
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('//')]
        
        metrics = {}
        
        # 行数统计
        metrics['total_lines'] = len(lines)
        metrics['code_lines'] = len(code_lines)
        metrics['comment_lines'] = len([l for l in lines if l.strip().startswith('//')])
        
        # 注释比例
        if metrics['code_lines'] > 0:
            metrics['comment_ratio'] = metrics['comment_lines'] / metrics['code_lines']
        else:
            metrics['comment_ratio'] = 0
        
        # 行长度统计
        code_lengths = [len(l) for l in code_lines]
        metrics['avg_line_length'] = sum(code_lengths) / len(code_lengths) if code_lengths else 0
        metrics['max_line_length'] = max(code_lengths) if code_lengths else 0
        metrics['long_lines'] = len([l for l in code_lines if len(l) > 120])
        
        # 信号统计
        signals = re.findall(r'\b(logic|wire|reg)\s*(?:\[[^\]]+\])?\s*([a-zA-Z_]\w*)', content)
        metrics['signal_count'] = len(signals)
        metrics['signal_names'] = [s[1] for s in signals]
        
        # IO统计
        inputs = len(re.findall(r'\binput\b', content, re.IGNORECASE))
        outputs = len(re.findall(r'\boutput\b', content, re.IGNORECASE))
        metrics['inputs'] = inputs
        metrics['outputs'] = outputs
        metrics['io_count'] = inputs + outputs
        
        # always块统计
        metrics['always_ff_count'] = len(re.findall(r'\balways_ff\b', content))
        metrics['always_comb_count'] = len(re.findall(r'\balways_comb\b', content))
        metrics['always_latch_count'] = len(re.findall(r'\balways_latch\b', content))
        metrics['always_total'] = metrics['always_ff_count'] + metrics['always_comb_count'] + metrics['always_latch_count']
        
        # 嵌套深度
        nesting = 0
        max_nesting = 0
        for l in content.split('\n'):
            nesting += l.count('begin') - l.count('end')
            max_nesting = max(max_nesting, nesting)
        metrics['max_nesting'] = max_nesting
        
        # 时钟域
        clocks = re.findall(r'@(posedge|negedge)\s+(\w+)', content)
        metrics['clock_domains'] = len(set([c[1] for c in clocks]))
        
        # 赋值统计
        metrics['non_blocking'] = len(re.findall(r'<=', content))
        metrics['blocking'] = len(re.findall(r'=', content)) - metrics['non_blocking']
        
        return metrics
    
    def _score_readability(self, lines: List[str], m: Dict, score: QualityScore, issues: List[QualityIssue]):
        """评分 - 可读性"""
        # 注释比例 (0-30分)
        comment_ratio = m.get('comment_ratio', 0)
        score.comment_ratio = comment_ratio
        
        if comment_ratio >= 0.15:
            score.readability += 30
        elif comment_ratio >= 0.1:
            score.readability += 20
        elif comment_ratio >= 0.05:
            score.readability += 10
            issues.append(QualityIssue(
                category="readability", severity="medium",
                line=0, metric="comment_ratio",
                value=comment_ratio, threshold=0.1,
                message=f"注释比例偏低: {comment_ratio:.1%}",
                suggestion="建议注释比例 >= 10%"
            ))
        else:
            issues.append(QualityIssue(
                category="readability", severity="high",
                line=0, metric="comment_ratio",
                value=comment_ratio, threshold=0.05,
                message=f"注释比例过低: {comment_ratio:.1%}",
                suggestion="需要添加更多注释"
            ))
        
        # 行长度 (0-30分)
        avg_len = m.get('avg_line_length', 0)
        score.avg_line_length = avg_len
        
        if avg_len <= 80:
            score.readability += 30
        elif avg_len <= 100:
            score.readability += 20
        elif avg_len > 120:
            long_lines = m.get("long_lines", 0)
            issues.append(QualityIssue(
                category="readability", severity="medium",
                line=0, metric="max_line_length",
                value=m.get('max_line_length', 0), threshold=120,
                message=f"存在超长行: {long_lines} 行超过120字符",
                suggestion="拆分超长行"
            ))
            score.readability += 10
        else:
            score.readability += 10
        
        # 信号命名 (0-40分)
        signal_names = m.get('signal_names', [])
        short_names = len([n for n in signal_names if len(n) == 1 or (len(n) <= 3 and n.islower())])
        signal_naming_score = max(0, 40 - short_names * 5)
        score.signal_naming_score = signal_naming_score
        score.readability += signal_naming_score
    
    def _score_testability(self, lines: List[str], m: Dict, score: QualityScore, issues: List[QualityIssue]):
        """评分 - 可测试性"""
        code_lines = m.get('code_lines', 1)
        
        # IO比例 (0-30分)
        io_ratio = m.get('io_count', 0) / code_lines if code_lines > 0 else 0
        score.io_ratio = io_ratio
        
        if 0.1 <= io_ratio <= 0.4:
            score.testability += 30
        elif io_ratio > 0:
            score.testability += 20
        
        # 可控性 - 是否有输入信号 (0-20分)
        if m.get('inputs', 0) > 0:
            score.testability += 20
            score.controllability = 20
        else:
            issues.append(QualityIssue(
                category="testability", severity="high",
                line=0, metric="inputs",
                value=0, threshold=1,
                message="无可控输入信号",
                suggestion="设计应至少有输入信号"
            ))
        
        # 可观测性 - 是否有输出信号 (0-20分)
        if m.get('outputs', 0) > 0:
            score.testability += 20
            score.observability = 20
        else:
            issues.append(QualityIssue(
                category="testability", severity="high",
                line=0, metric="outputs",
                value=0, threshold=1,
                message="无可观测输出信号",
                suggestion="设计应至少有输出信号"
            ))
        
        # 时钟和复位 (0-30分)
        has_clk = m.get('always_ff_count', 0) > 0
        if has_clk:
            score.testability += 15
        # 复位检查
        if any('rst' in l.lower() or 'reset' in l.lower() for l in lines):
            score.testability += 15
    
    def _score_maintainability(self, lines: List[str], m: Dict, score: QualityScore, issues: List[QualityIssue]):
        """评分 - 可维护性"""
        code_lines = m.get('code_lines', 0)
        
        # 模块大小 (0-40分)
        if 50 <= code_lines <= 300:
            score.maintainability += 40
            score.module_size = 40
        elif 20 <= code_lines <= 500:
            score.maintainability += 25
            score.module_size = 25
        else:
            score.module_size = 10
            if code_lines > 500:
                issues.append(QualityIssue(
                    category="maintainability", severity="medium",
                    line=0, metric="module_size",
                    value=code_lines, threshold=500,
                    message=f"模块过大: {code_lines} 行",
                    suggestion="考虑拆分为子模块"
                ))
            score.maintainability += 10
        
        # 嵌套深度 (0-30分)
        nesting = m.get('max_nesting', 0)
        score.nesting_depth = nesting
        
        if nesting <= 3:
            score.maintainability += 30
        elif nesting <= 5:
            score.maintainability += 20
            issues.append(QualityIssue(
                category="maintainability", severity="low",
                line=0, metric="max_nesting",
                value=nesting, threshold=3,
                message=f"嵌套深度较大: {nesting}",
                suggestion="考虑简化逻辑"
            ))
        else:
            score.maintainability += 10
            issues.append(QualityIssue(
                category="maintainability", severity="medium",
                line=0, metric="max_nesting",
                value=nesting, threshold=5,
                message=f"嵌套过深: {nesting}",
                suggestion="重构以减少嵌套"
            ))
        
        # 层次结构 (0-30分) - 简单的模块数量检查
        modules = len(re.findall(r'\bmodule\s+(\w+)', ''.join(lines)))
        if modules == 1:
            score.maintainability += 30
        else:
            score.maintainability += 20
        score.hierarchy_score = score.maintainability
    
    def _score_cdc_safety(self, lines: List[str], m: Dict, score: QualityScore, issues: List[QualityIssue]):
        """评分 - CDC安全性"""
        always_total = max(1, m.get('always_total', 1))
        
        # always_ff比例 (0-40分)
        ff_ratio = m.get('always_ff_count', 0) / always_total
        score.ff_ratio = ff_ratio
        
        if ff_ratio >= 0.8:
            score.cdc_safety += 40
        elif ff_ratio >= 0.5:
            score.cdc_safety += 25
        else:
            score.cdc_safety += 10
            issues.append(QualityIssue(
                category="cdc_safety", severity="medium",
                line=0, metric="ff_ratio",
                value=ff_ratio, threshold=0.5,
                message=f"always_ff使用比例低: {ff_ratio:.1%}",
                suggestion="优先使用always_ff而不是always_comb/latch"
            ))
        
        # Latch检测 (0-30分)
        latch_count = m.get('always_latch_count', 0)
        score.latch_count = latch_count
        
        if latch_count == 0:
            score.cdc_safety += 30
        else:
            score.cdc_safety += 10
            issues.append(QualityIssue(
                category="cdc_safety", severity="high",
                line=0, metric="latch_count",
                value=latch_count, threshold=0,
                message=f"发现 {latch_count} 个always_latch",
                suggestion="Latch可能导致亚稳态,建议替换为always_ff"
            ))
        
        # 时钟域数量 (0-30分)
        clock_domains = m.get('clock_domains', 1)
        score.clock_domain_count = clock_domains
        
        if clock_domains == 1:
            score.cdc_safety += 30
        elif clock_domains <= 3:
            score.cdc_safety += 20
            issues.append(QualityIssue(
                category="cdc_safety", severity="low",
                line=0, metric="clock_domains",
                value=clock_domains, threshold=1,
                message=f"多时钟域设计: {clock_domains} 个时钟",
                suggestion="确保跨时钟域信号有同步器"
            ))
        else:
            score.cdc_safety += 10
            issues.append(QualityIssue(
                category="cdc_safety", severity="medium",
                line=0, metric="clock_domains",
                value=clock_domains, threshold=3,
                message=f"时钟域过多: {clock_domains} 个",
                suggestion="简化时钟架构"
            ))
    
    def get_metrics_report(self) -> str:
        """获取指标报告"""
        if not self.metrics:
            return "No metrics available"
        
        lines = []
        lines.append("\n=== Objective Metrics ===")
        for k, v in sorted(self.metrics.items()):
            if isinstance(v, float):
                lines.append(f"  {k}: {v:.3f}")
            else:
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)
    
    def print_report(self, score: QualityScore, issues: List[QualityIssue]):
        """打印报告"""
        print("\n" + "="*60)
        print("Code Quality Report v2 (Objective Metrics)")
        print("="*60)
        
        print(f"\nScores:")
        print(f"  readability:    {score.readability:.1f}/100")
        print(f"    - comment_ratio:   {score.comment_ratio:.1%}")
        print(f"    - avg_line_length: {score.avg_line_length:.1f}")
        print(f"  testability:   {score.testability:.1f}/100")
        print(f"    - io_ratio:        {score.io_ratio:.2%}")
        print(f"  maintainability: {score.maintainability:.1f}/100")
        print(f"    - module_size:     {score.module_size}")
        print(f"    - nesting_depth:  {score.nesting_depth}")
        print(f"  cdc_safety:    {score.cdc_safety:.1f}/100")
        print(f"    - ff_ratio:        {score.ff_ratio:.1%}")
        print(f"    - latch_count:     {score.latch_count}")
        print(f"    - clock_domains:   {score.clock_domain_count}")
        print(f"\n  TOTAL: {score.total:.1f}/100")
        
        if self.metrics:
            print(self.get_metrics_report())
        
        if issues:
            print(f"\nIssues ({len(issues)}):")
            for issue in issues:
                print(f"  [{issue.severity.upper()}] {issue.category}.{issue.metric}")
                print(f"    Value: {issue.value:.3f}, Threshold: {issue.threshold}")
                print(f"    {issue.message}")
                print(f"    Fix: {issue.suggestion}")
        
        print("\n" + "="*60)


__all__ = ['CodeQualityScorer', 'QualityScore', 'QualityIssue', 'QualityMetric']
