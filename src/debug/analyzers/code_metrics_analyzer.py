"""CodeMetricsAnalyzer - 代码指标分析器。

计算代码的各项度量指标：
- 代码行数 (LOC)
- 注释行数
- 函数/模块数量
- 扇入/扇出

Example:
    >>> from debug.analyzers.code_metrics_analyzer import CodeMetricsAnalyzer
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> analyzer = CodeMetricsAnalyzer(parser)
    >>> metrics = analyzer.calculate()
    >>> print(analyzer.format_report(metrics))
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ModuleMetrics:
    """模块度量数据类。
    
    Attributes:
        name: 模块名
        loc: 代码行数
        sloc: 有效代码行数
        comments: 注释行数
        blank_lines: 空行数
        functions: 函数数量
        always_blocks: always 块数量
        signals: 信号数量
        ports: 端口数量
    """
    name: str
    loc: int = 0
    sloc: int = 0
    comments: int = 0
    blank_lines: int = 0
    functions: int = 0
    always_blocks: int = 0
    signals: int = 0
    ports: int = 0


@dataclass
class ProjectMetrics:
    """项目度量数据类。
    
    Attributes:
        total_loc: 总代码行数
        total_sloc: 总有效代码行数
        total_comments: 总注释行数
        total_modules: 模块数量
        total_functions: 函数数量
        total_signals: 信号数量
        module_metrics: 各模块度量
    """
    total_loc: int = 0
    total_sloc: int = 0
    total_comments: int = 0
    total_modules: int = 0
    total_functions: int = 0
    total_signals: int = 0
    module_metrics: List[ModuleMetrics] = None
    
    def __post_init__(self):
        if self.module_metrics is None:
            self.module_metrics = []


class CodeMetricsAnalyzer:
    """代码指标分析器。
    
    计算和分析代码的各种度量指标。

    Attributes:
        parser: SVParser 实例
        metrics: 计算得到的度量
    
    Example:
        >>> analyzer = CodeMetricsAnalyzer(parser)
        >>> metrics = analyzer.calculate()
    """
    
    def __init__(self, parser):
        """初始化分析器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.metrics: ProjectMetrics = None
    
    def calculate(self) -> ProjectMetrics:
        """计算所有度量。
        
        Returns:
            ProjectMetrics: 项目度量结果
        """
        self.metrics = ProjectMetrics()
        
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            # 读取源码计算行数
            try:
                if os.path.exists(fname):
                    with open(fname, 'r') as f:
                        lines = f.readlines()
                else:
                    continue
            except:
                continue
            
            mod_metrics = self._calculate_file_metrics(fname, lines)
            self.metrics.module_metrics.append(mod_metrics)
            
            # 累加到总计
            self.metrics.total_loc += mod_metrics.loc
            self.metrics.total_sloc += mod_metrics.sloc
            self.metrics.total_comments += mod_metrics.comments
            self.metrics.total_signals += mod_metrics.signals
        
        self.metrics.total_modules = len(self.metrics.module_metrics)
        self.metrics.total_functions = sum(m.functions for m in self.metrics.module_metrics)
        
        return self.metrics
    
    def _calculate_file_metrics(self, fname: str, lines: List[str]) -> ModuleMetrics:
        """计算单个文件的度量。
        
        Args:
            fname: 文件名
            lines: 代码行列表
        
        Returns:
            ModuleMetrics: 模块度量
        """
        import re
        
        metrics = ModuleMetrics(name=fname)
        
        in_block_comment = False
        
        for line in lines:
            metrics.loc += 1
            stripped = line.strip()
            
            # 空行
            if not stripped:
                metrics.blank_lines += 1
                continue
            
            # 块注释
            if '/*' in stripped:
                in_block_comment = True
            if in_block_comment:
                metrics.comments += 1
                if '*/' in stripped:
                    in_block_comment = False
                continue
            
            # 行注释
            if stripped.startswith('//'):
                metrics.comments += 1
                continue
            
            # 有效代码
            metrics.sloc += 1
            
            # 统计关键词
            if 'function' in stripped.lower():
                metrics.functions += 1
            if re.search(r'\balways\s+@', stripped):
                metrics.always_blocks += 1
        
        return metrics
    
    def format_report(self, metrics: ProjectMetrics = None) -> str:
        """格式化报告。
        
        Args:
            metrics: 可选的度量数据
        
        Returns:
            str: 格式化的报告字符串
        """
        if metrics is None:
            metrics = self.metrics
        
        lines = []
        lines.append("=" * 60)
        lines.append("CODE METRICS REPORT")
        lines.append("=" * 60)
        
        lines.append(f"\n📊 Project Summary:")
        lines.append(f"  Total LOC:      {metrics.total_loc}")
        lines.append(f"  Effective SLOC: {metrics.total_sloc}")
        lines.append(f"  Comments:        {metrics.total_comments}")
        lines.append(f"  Modules:         {metrics.total_modules}")
        lines.append(f"  Functions:       {metrics.total_functions}")
        lines.append(f"  Signals:         {metrics.total_signals}")
        
        if metrics.total_loc > 0:
            comment_ratio = metrics.total_comments / metrics.total_loc * 100
            lines.append(f"  Comment Ratio:   {comment_ratio:.1f}%")
        
        lines.append(f"\n📦 Per-Module Metrics:")
        for m in metrics.module_metrics[:10]:
            lines.append(f"  {m.name}:")
            lines.append(f"    LOC={m.loc}, SLOC={m.sloc}, Functions={m.functions}")
        
        return "\n".join(lines)
