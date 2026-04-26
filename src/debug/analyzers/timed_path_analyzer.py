"""
TimedPathAnalyzer - 跨时钟域Timed Path分析器
分析信号在时钟域之间的传播路径和时序特性
"""
import sys
import os
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


@dataclass
class TimedPath:
    """时序路径"""
    path_id: str
    source_reg: str
    dest_reg: str
    source_domain: str
    dest_domain: str
    
    # 路径特性
    path_type: str  # "same_domain", "slow_to_fast", "fast_to_slow", "async"
    logic_depth: int = 0
    timing_depth: int = 0
    
    # 寄存器链
    registers: List[str] = field(default_factory=list)
    combinational_signals: List[str] = field(default_factory=list)
    
    # 时序分析
    setup_violation: bool = False
    hold_violation: bool = False
    metastability_risk: str = "unknown"
    
    # 建议
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ClockRelationship:
    """时钟关系"""
    domain_a: str
    domain_b: str
    ratio: str  # "1:1", "1:N", "N:1", "async"
    safety: str  # "safe", "caution", "unsafe"


@dataclass
class TimedPathReport:
    """Timed Path分析报告"""
    paths: List[TimedPath] = field(default_factory=list)
    clock_relationships: List[ClockRelationship] = field(default_factory=list)
    
    # 统计
    same_domain_paths: int = 0
    slow_to_fast: int = 0
    fast_to_slow: int = 0
    async_paths: int = 0
    
    # 问题汇总
    setup_violations: List[TimedPath] = field(default_factory=list)
    hold_violations: List[TimedPath] = field(default_factory=list)
    high_risk_paths: List[TimedPath] = field(default_factory=list)


class TimedPathAnalyzer:
    """跨时钟域Timed Path分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._registers: Dict[str, Dict] = {}  # signal -> {clock, domain, reset}
        self._domains: Dict[str, Set[str]] = defaultdict(set)  # clock -> signals
        self._paths: List[TimedPath] = []
        self._clock_relations: List[ClockRelationship] = []
    
    def analyze(self) -> TimedPathReport:
        """执行Timed Path分析"""
        
        # 1. 提取时钟域信息
        self._extract_clock_domains()
        
        # 2. 构建时序路径
        self._build_timed_paths()
        
        # 3. 分析时钟关系
        self._analyze_clock_relationships()
        
        # 4. 检查时序违规
        self._check_timing_violations()
        
        # 5. 生成报告
        return self._generate_report()
    
    def _extract_clock_domains(self):
        """提取时钟域信息"""
        from debug.analyzers.clock_domain import ClockDomainAnalyzer
        
        cda = ClockDomainAnalyzer(self.parser)
        regs = cda.get_all_registers()
        
        for sig, info in regs.items():
            self._registers[sig] = {
                'clock': info.clock,
                'domain': info.clock,
                'edge': info.clock_edge,
                'has_reset': info.has_async_reset
            }
            if info.clock:
                self._domains[info.clock].add(sig)
    
    def _build_timed_paths(self):
        """构建时序路径"""
        from trace.dependency import DependencyAnalyzer
        
        dep_analyzer = DependencyAnalyzer(self.parser)
        
        # 对每个寄存器，追溯其数据源路径
        for reg_sig in self._registers:
            path = self._trace_path(reg_sig, dep_analyzer)
            if path:
                self._paths.append(path)
    
    def _trace_path(self, end_reg: str, dep_analyzer) -> Optional[TimedPath]:
        """追溯从源头到终点的路径"""
        from trace.driver import DriverTracer
        
        tracer = DriverTracer(self.parser)
        drivers = tracer.find_driver(end_reg)
        
        if not drivers:
            return None
        
        # 找源头寄存器
        source_regs = []
        combinational = []
        
        for driver in drivers:
            for src in driver.sources:
                if src in self._registers:
                    source_regs.append(src)
                else:
                    combinational.append(src)
        
        if not source_regs:
            return None
        
        src_reg = source_regs[0]
        
        # 确定路径类型
        src_domain = self._registers[src_reg]['domain']
        dst_domain = self._registers[end_reg]['domain']
        
        if src_domain == dst_domain:
            path_type = "same_domain"
        elif self._is_slow_clock(src_domain) and self._is_fast_clock(dst_domain):
            path_type = "slow_to_fast"
        elif self._is_fast_clock(src_domain) and self._is_slow_clock(dst_domain):
            path_type = "fast_to_slow"
        else:
            path_type = "async"
        
        # 计算路径深度
        timing_depth = self._count_timing_depth(src_reg, end_reg)
        logic_depth = len(combinational)
        
        path = TimedPath(
            path_id=f"path_{len(self._paths)}",
            source_reg=src_reg,
            dest_reg=end_reg,
            source_domain=src_domain,
            dest_domain=dst_domain,
            path_type=path_type,
            logic_depth=logic_depth,
            timing_depth=timing_depth,
            registers=[src_reg, end_reg],
            combinational_signals=combinational[:5]  # 限制数量
        )
        
        # 添加建议
        path.suggestions = self._generate_path_suggestions(path)
        
        # 评估风险
        path.metastability_risk = self._assess_risk(path)
        
        return path
    
    def _is_slow_clock(self, clock: str) -> bool:
        """判断是否为慢时钟"""
        slow_indicators = ['slow', '32k', 'rtc', 'timer', 'ref', 'ext']
        return any(ind in clock.lower() for ind in slow_indicators)
    
    def _is_fast_clock(self, clock: str) -> bool:
        """判断是否为快时钟"""
        fast_indicators = ['clk', 'core', 'cpu', 'high', 'main']
        return any(ind in clock.lower() for ind in fast_indicators) and not self._is_slow_clock(clock)
    
    def _count_timing_depth(self, src_reg: str, dst_reg: str) -> int:
        """计算时序深度（中间寄存器数量）"""
        # 简化：直接从源到目标
        return 1
    
    def _generate_path_suggestions(self, path: TimedPath) -> List[str]:
        """生成路径建议"""
        suggestions = []
        
        if path.path_type == "slow_to_fast":
            suggestions.append("慢到快时钟域: 确保数据在快时钟域正确采样")
            suggestions.append("建议添加2级寄存器同步器")
        
        elif path.path_type == "fast_to_slow":
            suggestions.append("快到慢时钟域: 数据可能变化多次才被采样")
            suggestions.append("建议使用握手协议或保持数据稳定")
            suggestions.append("注意setup/hold时间")
        
        elif path.path_type == "async":
            suggestions.append("异步路径: 必须使用同步器")
            suggestions.append("推荐使用2级FF同步器或握手协议")
        
        if path.logic_depth > 5:
            suggestions.append(f"组合逻辑深度({path.logic_depth})较高，考虑流水线化")
        
        if path.metastability_risk == "high":
            suggestions.append("高亚稳态风险: 必须添加同步器")
        
        return suggestions
    
    def _assess_risk(self, path: TimedPath) -> str:
        """评估路径风险"""
        if path.path_type == "same_domain":
            return "low"
        
        if path.path_type == "slow_to_fast":
            return "medium"
        
        if path.path_type == "fast_to_slow":
            return "high"
        
        return "critical"
    
    def _analyze_clock_relationships(self):
        """分析时钟关系"""
        domains = list(self._domains.keys())
        
        for i, dom_a in enumerate(domains):
            for dom_b in domains[i+1:]:
                # 简单判断比率
                size_a = len(self._domains[dom_a])
                size_b = len(self._domains[dom_b])
                
                if size_a == size_b:
                    ratio = "1:1"
                elif size_a > size_b:
                    ratio = f"1:{size_a//size_b}"
                else:
                    ratio = f"1:{size_b//size_a}"
                
                # 判断安全性
                if self._is_slow_clock(dom_a) and self._is_fast_clock(dom_b):
                    safety = "safe"
                elif self._is_fast_clock(dom_a) and self._is_slow_clock(dom_b):
                    safety = "caution"
                else:
                    safety = "unknown"
                
                self._clock_relations.append(ClockRelationship(
                    domain_a=dom_a,
                    domain_b=dom_b,
                    ratio=ratio,
                    safety=safety
                ))
    
    def _check_timing_violations(self):
        """检查时序违规"""
        for path in self._paths:
            # 简化检查
            if path.logic_depth > 10:
                path.setup_violation = True
            
            if path.path_type == "fast_to_slow" and path.logic_depth > 3:
                path.hold_violation = True
    
    def _generate_report(self) -> TimedPathReport:
        """生成报告"""
        report = TimedPathReport(
            paths=self._paths,
            clock_relationships=self._clock_relations
        )
        
        # 统计
        for path in self._paths:
            if path.path_type == "same_domain":
                report.same_domain_paths += 1
            elif path.path_type == "slow_to_fast":
                report.slow_to_fast += 1
            elif path.path_type == "fast_to_slow":
                report.fast_to_slow += 1
            else:
                report.async_paths += 1
            
            if path.setup_violation:
                report.setup_violations.append(path)
            if path.hold_violation:
                report.hold_violations.append(path)
            if path.metastability_risk == "high" or path.metastability_risk == "critical":
                report.high_risk_paths.append(path)
        
        return report
    
    def print_report(self, report: TimedPathReport):
        """打印报告"""
        print("\n" + "="*60)
        print("Timed Path Analysis Report")
        print("="*60)
        
        print("\n[Summary]")
        print(f"  Same Domain Paths: {report.same_domain_paths}")
        print(f"  Slow-to-Fast: {report.slow_to_fast}")
        print(f"  Fast-to-Slow: {report.fast_to_slow}")
        print(f"  Async Paths: {report.async_paths}")
        
        if report.high_risk_paths:
            print(f"\n[High Risk Paths: {len(report.high_risk_paths)}]")
            for p in report.high_risk_paths[:5]:
                print(f"  {p.path_id}: {p.source_reg} -> {p.dest_reg} ({p.path_type})")
        
        if report.setup_violations:
            print(f"\n[Setup Violations: {len(report.setup_violations)}]")
        
        if report.hold_violations:
            print(f"\n[Hold Violations: {len(report.hold_violations)}]")
        
        print("\n" + "="*60)


def analyze_timed_paths(parser) -> TimedPathReport:
    """便捷函数"""
    analyzer = TimedPathAnalyzer(parser)
    return analyzer.analyze()


__all__ = [
    'TimedPathAnalyzer',
    'TimedPathReport',
    'TimedPath',
    'ClockRelationship',
    'analyze_timed_paths',
]
