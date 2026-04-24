"""
RootCauseAnalyzer - 根因分析器
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class SymptomType(Enum):
    X_VALUE = "x_value"
    MULTIPLE_DRIVERS = "multiple_drivers"
    UNINITIALIZED = "uninitialized"
    UNUSED_SIGNAL = "unused_signal"
    TIMING_VIOLATION = "timing_violation"


@dataclass
class Cause:
    description: str
    location: str
    severity: str
    evidence: str


@dataclass
class RootCauseResult:
    symptom: str
    signal: str
    causes: List[Cause]
    confidence: float


class RootCauseAnalyzer:
    """根因分析器 - Option D: 规则引擎"""
    
    def __init__(self, parser):
        self.parser = parser
        self._driver_tracer = None
        self.rules = []
        self._init_rules()
    
    def _get_tracer(self):
        if not self._driver_tracer:
            from trace.driver import DriverTracer
            self._driver_tracer = DriverTracer(self.parser)
        return self._driver_tracer
    
    def _init_rules(self):
        """初始化问题检测规则"""
        self.rules = [
            {
                "name": "multiple_driver",
                "symptom": SymptomType.MULTIPLE_DRIVERS,
                "check": self._check_multiple_driver,
                "description": "Multiple drivers detected for signal"
            },
            {
                "name": "uninitialized_register",
                "symptom": SymptomType.UNINITIALIZED,
                "check": self._check_uninitialized,
                "description": "Register may be uninitialized"
            },
            {
                "name": "uncovered_case",
                "symptom": SymptomType.X_VALUE,
                "check": self._check_uncovered_case,
                "description": "Case statement may not cover all values"
            },
            {
                "name": "unused_signal",
                "symptom": SymptomType.UNUSED_SIGNAL,
                "check": self._check_unused_signal,
                "description": "Signal is driven but never used"
            }
        ]
    
    def analyze(self, symptom: str, signal: str) -> RootCauseResult:
        """分析根因"""
        symptom_type = self._parse_symptom(symptom)
        
        causes = []
        confidence = 0.0
        
        # Apply matching rules
        for rule in self.rules:
            if self._matches_symptom(rule["symptom"], symptom_type):
                result = rule["check"](signal)
                if result:
                    causes.extend(result)
                    confidence += 0.25
        
        confidence = min(confidence, 1.0)
        
        return RootCauseResult(
            symptom=symptom,
            signal=signal,
            causes=causes,
            confidence=confidence
        )
    
    def _parse_symptom(self, symptom: str) -> SymptomType:
        """解析症状类型"""
        s = symptom.lower()
        
        if "x" in s or "unknown" in s:
            return SymptomType.X_VALUE
        elif "multiple" in s or "driver" in s:
            return SymptomType.MULTIPLE_DRIVERS
        elif "uninit" in s or "reset" in s:
            return SymptomType.UNINITIALIZED
        elif "unused" in s or "never used" in s:
            return SymptomType.UNUSED_SIGNAL
        else:
            return SymptomType.X_VALUE
    
    def _matches_symptom(self, rule_symptom: SymptomType, input_symptom: SymptomType) -> bool:
        """检查规则是否匹配症状"""
        if rule_symptom == input_symptom:
            return True
        
        # X_VALUE can be caused by multiple drivers or uncovered case
        if input_symptom == SymptomType.X_VALUE:
            return rule_symptom in [SymptomType.MULTIPLE_DRIVERS, SymptomType.UNINITIALIZED, SymptomType.UNCOVERED_CASE]
        
        return False
    
    def _check_multiple_driver(self, signal: str) -> List[Cause]:
        """检查多驱动问题"""
        causes = []
        tracer = self._get_tracer()
        drivers = tracer.find_driver(signal)
        
        if len(drivers) > 1:
            causes.append(Cause(
                description=f"Signal has {len(drivers)} drivers",
                location=drivers[0].source_expr[:50] if drivers[0].source_expr else "N/A",
                severity="high",
                evidence=f"Multiple always blocks or assign statements"
            ))
        
        return causes
    
    def _check_uninitialized(self, signal: str) -> List[Cause]:
        """检查未初始化问题"""
        causes = []
        tracer = self._get_tracer()
        drivers = tracer.find_driver(signal)
        
        # Check for always_ff without reset
        ff_drivers = [d for d in drivers if d.driver_kind.name == "ALWAYS_FF"]
        if ff_drivers:
            has_reset = False
            for d in ff_drivers:
                src = d.source_expr if d.source_expr else ""
                if "if" in src and ("rst" in src.lower() or "reset" in src.lower()):
                    has_reset = True
                    break
            
            if not has_reset:
                causes.append(Cause(
                    description="Register may not have reset initialization",
                    location=ff_drivers[0].source_expr[:50] if ff_drivers[0].source_expr else "N/A",
                    severity="medium",
                    evidence="always_ff without synchronous reset"
                ))
        
        return causes
    
    def _check_uncovered_case(self, signal: str) -> List[Cause]:
        """检查 case 未覆盖问题"""
        causes = []
        # Simplified check - look for case without default
        tracer = self._get_tracer()
        drivers = tracer.find_driver(signal)
        
        for d in drivers:
            src = d.source_expr if d.source_expr else ""
            if "case" in src.lower() and "default" not in src.lower():
                causes.append(Cause(
                    description="Case statement may not cover all values",
                    location=src[:50],
                    severity="medium",
                    evidence="Missing default branch in case statement"
                ))
                break
        
        return causes
    
    def _check_unused_signal(self, signal: str) -> List[Cause]:
        """检查未使用信号"""
        causes = []
        tracer = self._get_tracer()
        
        drivers = tracer.find_driver(signal)
        loads = tracer.find_load(signal)
        
        if drivers and not loads:
            causes.append(Cause(
                description="Signal is driven but never used",
                location="driven but no loads found",
                severity="low",
                evidence="No load found for this signal"
            ))
        
        return causes
    
    def add_rule(self, rule: Dict):
        """添加自定义规则"""
        self.rules.append(rule)
