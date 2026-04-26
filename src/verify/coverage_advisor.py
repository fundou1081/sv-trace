"""
CoverageAdvisor - 遗漏测试识别
基于覆盖率分析识别遗漏的测试场景
"""
from typing import List, Dict, Set
from dataclasses import dataclass

@dataclass
class CoverageGap:
    """覆盖缺口"""
    item: str
    coverage: float
    suggested_tests: List[str]
    priority: str  # high/medium/low

class CoverageAdvisor:
    """覆盖率建议器"""
    
    def __init__(self):
        self.known_patterns = {
            'fifo': ['test_fifo_empty', 'test_fifo_full', 'test_fifo_overflow'],
            'uart': ['test_baud_9600', 'test_baud_115200', 'test_parity_error'],
            'cdc': ['test_cdc_single', 'test_cdc_multi'],
            'reset': ['test_async_reset', 'test_sync_reset'],
        }
    
    def analyze_gaps(self, coverage_data: Dict) -> List[CoverageGap]:
        """分析覆盖缺口"""
        gaps = []
        
        for item, coverage in coverage_data.items():
            if coverage < 90:  # 假设90%是目标
                # 生成建议测试
                suggestions = self._suggest_tests(item)
                
                gaps.append(CoverageGap(
                    item=item,
                    coverage=coverage,
                    suggested_tests=suggestions,
                    priority='high' if coverage < 70 else 'medium'
                ))
        
        return gaps
    
    def _suggest_tests(self, item: str) -> List[str]:
        """建议测试场景"""
        suggestions = []
        
        item_lower = item.lower()
        
        for pattern, tests in self.known_patterns.items():
            if pattern in item_lower:
                suggestions.extend(tests)
        
        if not suggestions:
            suggestions = [f"test_{item}_basic", f"test_{item}_corner"]
        
        return suggestions[:5]  # 最多5个建议
    
    def generate_test_plan(self, gaps: List[CoverageGap]) -> str:
        """生成测试计划"""
        lines = []
        lines.append("# 覆盖率改进测试计划")
        lines.append("")
        
        for gap in gaps:
            lines.append(f"## {gap.item}")
            lines.append(f"- 当前覆盖率: {gap.coverage:.1f}%")
            lines.append(f"- 优先级: {gap.priority}")
            lines.append("- 建议测试:")
            for test in gap.suggested_tests:
                lines.append(f"  - [ ] {test}")
            lines.append("")
        
        return '\n'.join(lines)
