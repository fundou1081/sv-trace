"""
CDC Analyzer - 跨时钟域分析器
"""
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.models import DomainInfo, Register


@dataclass
class CDCPath:
    """跨时钟域路径"""
    source_domain: str
    dest_domain: str
    start_reg: str
    end_reg: str
    signals: List[str] = field(default_factory=list)
    timing_depth: int = 0
    path_type: str = "unknown"  # CDC, feedback, or safe
    issues: List[str] = field(default_factory=list)


@dataclass
class CDCReport:
    """CDC 分析报告"""
    cdc_paths: List[CDCPath] = field(default_factory=list)
    safe_paths: List[CDCPath] = field(default_factory=list)
    feedback_paths: List[CDCPath] = field(default_factory=list)
    domain_count: int = 0
    risky_paths: int = 0


class CDCAnalyzer:
    """跨时钟域分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._init_from_analyzer()
    
    def _init_from_analyzer(self):
        """从 TimingDepthAnalyzer 初始化"""
        from trace.timing_depth import TimingDepthAnalyzer
        
        self.analyzer = TimingDepthAnalyzer(self.parser)
        self.registers = self.analyzer.registers
        self.domains = self.analyzer.domains
        self.flow_graph = self.analyzer.flow_graph
    
    def analyze(self) -> CDCReport:
        """执行 CDC 分析"""
        report = CDCReport(
            domain_count=len(self.domains)
        )
        
        if len(self.domains) < 2:
            # 只有一个时钟域，没有 CDC 问题
            return report
        
        # 分析每个域间路径
        for src_domain in self.domains:
            for dest_domain in self.domains:
                if src_domain == dest_domain:
                    continue
                
                # 查找从 src_domain 到 dest_domain 的路径
                paths = self._find_cross_domain_paths(src_domain, dest_domain)
                
                for path in paths:
                    # 判断路径类型
                    cdc_path = self._classify_path(path, src_domain, dest_domain)
                    
                    if cdc_path.path_type == "cdc":
                        report.cdc_paths.append(cdc_path)
                        if cdc_path.issues:
                            report.risky_paths += 1
                    elif cdc_path.path_type == "feedback":
                        report.feedback_paths.append(cdc_path)
                    else:
                        report.safe_paths.append(cdc_path)
        
        return report
    
    def _find_cross_domain_paths(self, src_domain: str, dest_domain: str) -> List[List[str]]:
        """查找跨域路径"""
        paths = []
        src_regs = set(self.domains[src_domain].registers)
        dest_regs = set(self.domains[dest_domain].registers)
        
        # 从目标寄存器向上追溯
        for end_reg in dest_regs:
            path_result = self.analyzer._trace_upstream(end_reg, set())
            if not path_result:
                continue
            
            path_signals = path_result[0][::-1]  # 反转，从源头到终点
            
            # 检查路径是否经过源域的寄存器
            path_regs = [s for s in path_signals if s in src_regs]
            if path_regs:
                # 找到了跨域路径
                paths.append(path_signals)
        
        return paths
    
    def _classify_path(self, path_signals: List[str], src_domain: str, dest_domain: str) -> CDCPath:
        """分类路径"""
        cdc_path = CDCPath(
            source_domain=src_domain,
            dest_domain=dest_domain,
            start_reg=path_signals[0] if path_signals else "",
            end_reg=path_signals[-1] if path_signals else "",
            signals=path_signals,
            timing_depth=len([s for s in path_signals if s in self.registers]) - 1
        )
        
        # 检查路径类型
        if self._is_feedback_path(path_signals):
            cdc_path.path_type = "feedback"
            cdc_path.issues.append("Feedback path crosses clock domains")
        else:
            cdc_path.path_type = "cdc"
            
            # 检查风险
            if cdc_path.timing_depth > 1:
                cdc_path.issues.append(f"Multi-cycle path (depth={cdc_path.timing_depth})")
            
            if self._has_combinational_logic(path_signals):
                cdc_path.issues.append("Combinational logic in CDC path")
        
        return cdc_path
    
    def _is_feedback_path(self, path_signals: List[str]) -> bool:
        """检查是否是反馈路径"""
        if len(path_signals) < 3:
            return False
        
        # 检查是否有信号同时作为源和目的
        start = path_signals[0]
        end = path_signals[-1]
        
        # 检查中间是否有反馈（同一个寄存器既是起点又出现在路径中间）
        for i in range(1, len(path_signals) - 1):
            if path_signals[i] == start or path_signals[i] == end:
                if path_signals[i] in self.registers:
                    return True
        
        return False
    
    def _has_combinational_logic(self, path_signals: List[str]) -> bool:
        """检查路径中是否有组合逻辑"""
        # 如果路径中间有非寄存器信号，可能是组合逻辑
        for sig in path_signals[1:-1]:
            if sig not in self.registers:
                return True
        return False
    
    def generate_cdc_report_text(self) -> str:
        """生成文本格式的 CDC 报告"""
        report = self.analyze()
        
        lines = []
        lines.append("=" * 60)
        lines.append("CDC Analysis Report")
        lines.append("=" * 60)
        lines.append(f"\nClock Domains: {report.domain_count}")
        lines.append(f"CDC Paths: {len(report.cdc_paths)}")
        lines.append(f"Risky Paths: {report.risky_paths}")
        lines.append(f"Feedback Paths: {len(report.feedback_paths)}")
        
        if report.cdc_paths:
            lines.append("\n" + "-" * 60)
            lines.append("Cross-Clock Domain Paths:")
            lines.append("-" * 60)
            
            for i, path in enumerate(report.cdc_paths, 1):
                lines.append(f"\n[{i}] {path.source_domain} → {path.dest_domain}")
                lines.append(f"    Path: {' → '.join(path.signals)}")
                lines.append(f"    Timing Depth: {path.timing_depth}")
                
                if path.issues:
                    lines.append(f"    ⚠️  Issues:")
                    for issue in path.issues:
                        lines.append(f"       - {issue}")
        
        if report.feedback_paths:
            lines.append("\n" + "-" * 60)
            lines.append("Feedback Paths:")
            lines.append("-" * 60)
            
            for i, path in enumerate(report.feedback_paths, 1):
                lines.append(f"\n[{i}] {path.source_domain} → {path.dest_domain}")
                lines.append(f"    Path: {' → '.join(path.signals)}")
        
        return "\n".join(lines)


def analyze_cdc(parser) -> CDCReport:
    """便捷函数：执行 CDC 分析"""
    analyzer = CDCAnalyzer(parser)
    return analyzer.analyze()
