"""
PowerDomain - 功耗域分析
"""
from typing import List
from dataclasses import dataclass

@dataclass
class PowerDomain:
    name: str
    is_gateable: bool
    modules: List[str]
    estimated_power: float = 0.0

class PowerDomainAnalyzer:
    def analyze(self, parser) -> List[PowerDomain]:
        return []
    
    def suggest_clock_gating(self) -> List[str]:
        return []
