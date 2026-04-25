"""
MultiDriverDetector - 多驱动检测器
检测设计中所有可能的多驱动问题
"""

import sys
import os
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector


class DriverConflictType(Enum):
    """驱动冲突类型"""
    ALWAYS_FF_MULTI = "always_ff_multi"
    ALWAYS_COMB_MULTI = "always_comb_multi"
    ASSIGN_MULTI = "assign_multi"
    FF_COMB_MIX = "ff_comb_mix"
    LATCH_FF_MIX = "latch_ff_mix"
    UNKNOWN = "unknown"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DriverConflict:
    """驱动冲突"""
    signal: str
    conflict_type: DriverConflictType
    severity: Severity
    drivers: List
    description: str
    suggestion: str


@dataclass
class MultiDriverReport:
    """多驱动检测报告"""
    conflicts: List[DriverConflict]
    statistics: Dict
    module_summary: Dict[str, int]


class MultiDriverDetector:
    """多驱动检测器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._dc = DriverCollector(parser)
        self._conflicts = []
    
    def analyze(self) -> MultiDriverReport:
        """执行多驱动分析"""
        self._conflicts = []
        module_summary = {}
        
        # 获取所有信号
        all_signals = self._dc.get_all_signals()
        
        for sig in all_signals:
            drivers = self._dc.find_driver(sig)
            
            if len(drivers) > 1:
                conflict = self._classify_conflict(sig, drivers)
                if conflict:
                    self._conflicts.append(conflict)
                    module = drivers[0].module.strip()
                    module_summary[module] = module_summary.get(module, 0) + 1
        
        # 统计
        stats = {
            "total_signals": len(all_signals),
            "multi_driver_signals": len(self._conflicts),
            "critical": sum(1 for c in self._conflicts if c.severity == Severity.CRITICAL),
            "high": sum(1 for c in self._conflicts if c.severity == Severity.HIGH),
            "medium": sum(1 for c in self._conflicts if c.severity == Severity.MEDIUM),
        }
        
        return MultiDriverReport(
            conflicts=self._conflicts,
            statistics=stats,
            module_summary=module_summary
        )
    
    def _classify_conflict(self, sig: str, drivers) -> DriverConflict:
        """分类冲突类型"""
        always_ff = [d for d in drivers if d.kind.name == 'AlwaysFF']
        always_comb = [d for d in drivers if d.kind.name == 'AlwaysComb']
        always_latch = [d for d in drivers if d.kind.name == 'AlwaysLatch']
        continuous = [d for d in drivers if d.kind.name == 'Continuous']
        
        lines = [d.lines[0] if d.lines else 0 for d in drivers]
        is_same_block = max(lines) - min(lines) < 100 if len(lines) > 1 else True
        
        # 分类
        if len(always_ff) > 1:
            if not is_same_block:
                return DriverConflict(
                    signal=sig,
                    conflict_type=DriverConflictType.ALWAYS_FF_MULTI,
                    severity=Severity.CRITICAL,
                    drivers=drivers,
                    description=f"Signal '{sig}' driven by {len(always_ff)} always_ff blocks",
                    suggestion="Use MUX or generate logic to combine drivers"
                )
        
        if len(always_comb) > 1:
            if not is_same_block:
                return DriverConflict(
                    signal=sig,
                    conflict_type=DriverConflictType.ALWAYS_COMB_MULTI,
                    severity=Severity.HIGH,
                    drivers=drivers,
                    description=f"Signal '{sig}' driven by {len(always_comb)} always_comb blocks",
                    suggestion="Use single always_comb or ensure mutually exclusive conditions"
                )
        
        if always_latch and always_ff:
            return DriverConflict(
                signal=sig,
                conflict_type=DriverConflictType.LATCH_FF_MIX,
                severity=Severity.CRITICAL,
                drivers=drivers,
                description=f"Signal '{sig}' driven by latch and flip-flop",
                suggestion="Use only always_ff for synchronous logic"
            )
        
        if always_comb and always_ff:
            return DriverConflict(
                signal=sig,
                conflict_type=DriverConflictType.FF_COMB_MIX,
                severity=Severity.HIGH,
                drivers=drivers,
                description=f"Signal '{sig}' driven by always_comb and always_ff",
                suggestion="Ensure proper clock domain isolation"
            )
        
        if len(continuous) > 1:
            return DriverConflict(
                signal=sig,
                conflict_type=DriverConflictType.ASSIGN_MULTI,
                severity=Severity.MEDIUM,
                drivers=drivers,
                description=f"Signal '{sig}' has {len(continuous)} continuous assignments",
                suggestion="Use single assign or proper tri-state bus"
            )
        
        # 默认
        return DriverConflict(
            signal=sig,
            conflict_type=DriverConflictType.UNKNOWN,
            severity=Severity.LOW,
            drivers=drivers,
            description=f"Signal '{sig}' has {len(drivers)} drivers",
            suggestion="Review driver compatibility"
        )
    
    def detect_issues(self) -> List[DriverConflict]:
        """检测冲突"""
        return self.analyze().conflicts
    
    def get_conflicts_by_module(self, module: str) -> List[DriverConflict]:
        """按模块获取冲突"""
        return [c for c in self.analyze().conflicts if module in c.drivers[0].module]
    
    def print_report(self, report: MultiDriverReport):
        """打印报告"""
        print("\n" + "="*60)
        print("Multi-Driver Detection Report")
        print("="*60)
        
        print(f"\nStatistics:")
        for k, v in report.statistics.items():
            print(f"  {k}: {v}")
        
        if report.conflicts:
            print(f"\nConflicts ({len(report.conflicts)}):")
            for c in report.conflicts:
                print(f"  [{c.severity.value.upper()}] {c.signal}")
                print(f"    {c.description}")
                print(f"    Suggestion: {c.suggestion}")
        
        print("\n" + "="*60)


__all__ = ['MultiDriverDetector', 'DriverConflict', 'MultiDriverReport', 'DriverConflictType', 'Severity']
