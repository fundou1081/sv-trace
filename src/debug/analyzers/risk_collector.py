"""
RiskCollector - 风险识别收集器 (Phase 1)
集成现有工具，统一收集各类验证风险
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class RiskItem:
    """单个风险项"""
    id: int = 0
    category: str = ""
    severity: str = ""
    title: str = ""
    description: str = ""
    location: str = ""
    line_number: int = 0
    suggestion: str = ""


@dataclass
class RiskSummary:
    """风险汇总"""
    total: int = 0
    P1: int = 0
    P2: int = 0
    P3: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)


@dataclass
class RiskResult:
    """RiskCollector结果"""
    risks: List[RiskItem] = field(default_factory=list)
    summary: RiskSummary = field(default_factory=RiskSummary)
    
    def add(self, risk):
        risk.id = len(self.risks) + 1
        self.risks.append(risk)
        
        self.summary.total += 1
        if risk.severity == 'P1':
            self.summary.P1 += 1
        elif risk.severity == 'P2':
            self.summary.P2 += 1
        else:
            self.summary.P3 += 1
        
        cat = risk.category
        self.summary.by_category[cat] = self.summary.by_category.get(cat, 0) + 1
    
    def visualize(self) -> str:
        lines = ["=" * 70, "RISK IDENTIFICATION REPORT", "=" * 70]
        
        lines.append(f"\n📊 Summary:")
        lines.append(f"  Total: {self.summary.total}")
        lines.append(f"  P1 (Critical): {self.summary.P1}")
        lines.append(f"  P2 (Warning): {self.summary.P2}")
        lines.append(f"  P3 (Info): {self.summary.P3}")
        
        lines.append(f"\n📁 By Category:")
        for cat, count in sorted(self.summary.by_category.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {cat}: {count}")
        
        severity_order = {'P1': 0, 'P2': 1, 'P3': 2}
        sorted_risks = sorted(self.risks, key=lambda r: severity_order.get(r.severity, 3))
        
        lines.append(f"\n📝 Risk Details:")
        for r in sorted_risks[:15]:
            lines.append(f"\n  [{r.severity}] {r.category}")
            lines.append(f"    {r.title}")
            if r.suggestion:
                lines.append(f"    fix: {r.suggestion}")
        
        lines.append("=" * 70)
        return '\n'.join(lines)


class RiskCollector:
    """风险识别收集器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.result = RiskResult()
    
    def collect(self) -> RiskResult:
        """收集所有风险"""
        
        # CDC
        self._collect_cdc()
        
        # Multi-Driver
        self._collect_multi_driver()
        
        # Uninitialized  
        self._collect_uninitialized()
        
        # Clock
        self._collect_clock()
        
        # Reset
        self._collect_reset()
        
        return self.result
    
    def _collect_cdc(self):
        try:
            from debug.analyzers.cdc import CDCAnalyzer
            cdc = CDCAnalyzer(self.parser)
            result = cdc.analyze()
            
            if hasattr(result, 'crossings'):
                for cr in result.crossings[:3]:
                    self.result.add(RiskItem(
                        category='CDC',
                        severity='P1',
                        title=f"CDC: {cr.signal}",
                        description='Async crossing',
                        suggestion='Add sync FIFO'
                    ))
        except:
            pass
    
    def _collect_multi_driver(self):
        try:
            from debug.analyzers.multi_driver import MultiDriverDetector
            md = MultiDriverDetector(self.parser)
            issues = md.detect()
            
            for issue in issues[:3]:
                self.result.add(RiskItem(
                    category='MultiDriver',
                    severity='P1',
                    title=f"Multi-driver: {issue.signal}",
                    description='Multiple drivers',
                    suggestion='Fix driver conflict'
                ))
        except:
            pass
    
    def _collect_uninitialized(self):
        try:
            from debug.analyzers.uninitialized import UninitializedDetector
            ud = UninitializedDetector(self.parser)
            issues = ud.detect()
            
            for issue in issues[:3]:
                self.result.add(RiskItem(
                    category='Uninitialized',
                    severity='P2',
                    title=f"Uninit: {issue.signal}",
                    description='No reset value',
                    suggestion='Add reset'
                ))
        except:
            pass
    
    def _collect_clock(self):
        try:
            from debug.analyzers.clock_tree_analyzer import ClockTreeAnalyzer
            cta = ClockTreeAnalyzer(self.parser)
            domains = cta.get_all_domains()
            
            if len(domains) > 4:
                self.result.add(RiskItem(
                    category='ClockDomain',
                    severity='P2',
                    title=f"Multiple clocks: {len(domains)}",
                    description=f'{len(domains)} clock domains',
                    suggestion='Review architecture'
                ))
        except:
            pass
    
    def _collect_reset(self):
        try:
            from debug.analyzers.reset_domain_analyzer import ResetDomainAnalyzer
            rda = ResetDomainAnalyzer(self.parser)
            async_rsts = rda.get_async_resets()
            sync_rsts = rda.get_sync_resets()
            
            if len(async_rsts) > 5:
                self.result.add(RiskItem(
                    category='ResetDomain',
                    severity='P2',
                    title=f"Async resets: {len(async_rsts)}",
                    description='Many async resets',
                    suggestion='Review'
                ))
        except:
            pass


def collect_risks(parser):
    collector = RiskCollector(parser)
    return collector.collect()
