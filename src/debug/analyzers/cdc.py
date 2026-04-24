"""
CDCAnalyzer - 基于信号关系的 CDC 分析器
"""
import sys
import os
import re
from typing import Dict, List
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))


class CDCIssueType(Enum):
    UNPROTECTED_CROSSING = "unprotected_crossing"
    MULTI_BIT_WITHOUT_HANDSHAKE = "multi_bit_without_handshake"


class ProtectionType(Enum):
    NONE = "none"
    TWO_FF_SYNC = "two_ff_synchronizer"
    HANDSHAKE = "handshake"
    FIFO = "fifo"
    GRAY_CODE = "gray_code"


@dataclass
class CDCIssue:
    signal: str
    from_domain: str
    to_domain: str
    issue_type: CDCIssueType
    severity: str
    description: str
    mitigation: str


@dataclass  
class CrossingResult:
    signal: str
    from_clock: str
    to_clock: str
    has_protection: bool
    protection_type: ProtectionType


class SignalCDCAnalyzer:
    """基于信号的 CDC 分析"""
    
    def __init__(self, parser):
        self.parser = parser
        self._clock_map = {}  # always_ff block -> clock
        self._signal_drivers = {}  # signal -> list of clocks
        self._signal_loads = {}  # signal -> list of clocks
        self._collect_clock_info()
    
    def _collect_clock_info(self):
        """收集时钟信息"""
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                if not hasattr(member, 'members'):
                    continue
                
                for j in range(len(member.members)):
                    mm = member.members[j]
                    
                    if 'ProceduralBlock' in str(type(mm)):
                        if hasattr(mm, 'statement'):
                            stmt_str = str(mm.statement)
                            
                            # 提取时钟
                            match = re.search(r'@(posedge|negedge)\s+(\w+)', stmt_str)
                            if match:
                                clock = match.group(1)
                                
                                # 提取被驱动的信号
                                signals = self._extract_signals_from_stmt(mm.statement)
                                for sig in signals:
                                    if sig not in self._signal_drivers:
                                        self._signal_drivers[sig] = []
                                    self._signal_drivers[sig].append(clock)
    
    def _extract_signals_from_stmt(self, stmt) -> List[str]:
        signals = []
        
        if not stmt:
            return signals
        
        stmt_str = str(stmt)
        
        # 简单的正则匹配赋值语句中的左侧
        # 匹配: signal <= expression 或 signal = expression
        for match in re.finditer(r'(\w+(?:\[\d+:\d+\])?)\s*(?:<=|=)', stmt_str):
            signals.append(match.group(1))
        
        return signals
    
    def analyze(self) -> Dict:
        """分析 CDC"""
        # 简化：直接分析跨域信号
        # 跨域 = 一个时钟域的信号被另一个时钟域使用
        
        crossings = []
        issues = []
        
        for signal, clocks in self._signal_drivers.items():
            if not clocks:
                continue
            
            # 简化：假设信号在被驱动的时钟域内使用
            # 实际的跨域需要更复杂的分析
            
            # 这里做一个简化假设：如果信号在不同 always_ff 中被驱动，
            # 则认为是跨域
        
        # 基于实际 always_ff 块来检测跨域
        all_always_ff = self._get_all_always_ff()
        
        for i, (clock1, signals1) in enumerate(all_always_ff):
            for j, (clock2, signals2) in enumerate(all_always_ff):
                if i >= j:
                    continue
                
                # 检查是否有跨域
                for sig in signals1:
                    if sig in signals2:
                        # signal 被两个不同时钟域驱动 -> 多驱动问题
                        # 或者 signal 在 clock1 驱动，被 clock2 使用 -> 跨域
                        
                        # 这里简化：认为是从 clock1 到 clock2 的跨域
                        protection = self._check_protection(sig)
                        
                        if protection == ProtectionType.NONE:
                            is_multi = '[' in sig or len(sig) > 3
                            issues.append(CDCIssue(
                                signal=sig,
                                from_domain=clock1,
                                to_domain=clock2,
                                issue_type=CDCIssueType.MULTI_BIT_WITHOUT_HANDSHAKE if is_multi else CDCIssueType.UNPROTECTED_CROSSING,
                                severity="high",
                                description=f"Signal {sig} crosses from {clock1} to {clock2} without synchronizer",
                                mitigation="Add 2-FF synchronizer"
                            ))
                        
                        crossings.append(CrossingResult(
                            signal=sig,
                            from_clock=clock1,
                            to_clock=clock2,
                            has_protection=protection != ProtectionType.NONE,
                            protection_type=protection
                        ))
        
        return {
            "issues": issues,
            "crossings": crossings,
            "statistics": {
                "total_crossings": len(crossings),
                "protected": sum(1 for c in crossings if c.has_protection),
                "unprotected": sum(1 for c in crossings if not c.has_protection),
                "high_severity": len(issues)
            }
        }
    
    def _get_all_always_ff(self) -> List[tuple]:
        """获取所有 always_ff 块"""
        result = []
        
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                if not hasattr(member, 'members'):
                    continue
                
                for j in range(len(member.members)):
                    mm = member.members[j]
                    
                    if 'ProceduralBlock' in str(type(mm)):
                        if hasattr(mm, 'statement'):
                            stmt_str = str(mm.statement)
                            
                            if '@(posedge' in stmt_str or '@(negedge' in stmt_str:
                                match = re.search(r'@(posedge|negedge)\s+(\w+)', stmt_str)
                                if match:
                                    clock = match.group(1)
                                    signals = self._extract_signals_from_stmt(mm.statement)
                                    if signals:
                                        result.append((clock, signals))
        
        return result
    
    def _check_protection(self, signal) -> ProtectionType:
        sig = signal.lower()
        
        if 'sync' in sig:
            return ProtectionType.TWO_FF_SYNC
        if 'handshake' in sig or ('req' in sig and 'ack' in sig):
            return ProtectionType.HANDSHAKE
        if 'fifo' in sig:
            return ProtectionType.FIFO
        if 'gray' in sig or 'grey' in sig:
            return ProtectionType.GRAY_CODE
        
        return ProtectionType.NONE


class CDCAnalyzer:
    def __init__(self, parser):
        self.parser = parser
        self._analyzer = SignalCDCAnalyzer(parser)
    
    def analyze(self):
        result = self._analyzer.analyze()
        
        @dataclass
        class Report:
            issues: List
            crossings: List  
            statistics: Dict
        
        return Report(result["issues"], result["crossings"], result["statistics"])
    
    def detect_issues(self):
        return self._analyzer.analyze()["issues"]
    
    def check_crossing(self, signal):
        result = self._analyzer.analyze()
        for c in result["crossings"]:
            if c.signal == signal:
                return c
        return None
