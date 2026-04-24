"""
OverflowRiskDetector - 饱和/溢出风险自动检测
自动检测data path上的饱和及溢出风险
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List


# 风险等级
RISK_LEVEL = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}


@dataclass
class OverflowRisk:
    """溢出风险"""
    signal: str
    expression: str
    risk_level: str
    description: str
    suggestion: str
    
    def to_string(self) -> str:
        return f"[{self.risk_level}] {self.signal}: {self.description}"


@dataclass
class OverflowResult:
    """检测结果"""
    risks: List[OverflowRisk] = field(default_factory=list)
    
    def visualize(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("OVERFLOW RISK DETECTION")
        lines.append("=" * 60)
        
        if not self.risks:
            lines.append("\n✅ No overflow risks detected")
        else:
            lines.append(f"\n📋 Found {len(self.risks)} risks:")
            
            for r in self.risks:
                lines.append(f"\n{r.to_string()}")
                lines.append(f"  → {r.suggestion}")
        
        lines.append("=" * 60)
        return '\n'.join(lines)


class OverflowRiskDetector:
    """溢出风险检测器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def detect(self, signal: str = None) -> OverflowResult:
        """检测溢出风险"""
        
        result = OverflowResult()
        
        # 扫描所有赋值语句
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            if not code:
                continue
            
            # 查找有风险的表达式
            assignments = self._find_add_sub_assignments(code)
            
            for assign in assignments:
                # 检查是否有溢出风险
                risk = self._check_overflow(assign)
                if risk:
                    result.risks.append(risk)
        
        return result
    
    def _find_add_sub_assignments(self, code: str) -> List[str]:
        """查找加法和减法赋值"""
        
        assignments = []
        
        # 匹配 data <= data + xxx 或 data = data + xxx
        patterns = [
            r'(\w+)\s*<=\s*\1\s*\+\s*(\w+)',
            r'(\w+)\s*=\s*\1\s*\+\s*(\w+)',
            r'(\w+)\s*<=\s*\1\s*-\s*(\w+)',
            r'(\w+)\s*=\s*\1\s*-\s*(\w+)',
        ]
        
        for line in code.split('\n'):
            for p in patterns:
                if re.search(p, line):
                    # 提取基本表达式
                    match = re.search(r'(\w+)\s*(?:<=|=)\s*(.+)', line)
                    if match:
                        target = match.group(1)
                        expr = match.group(2)
                        assignments.append((target, expr))
        
        return assignments
    
    def _check_overflow(self, assign: tuple) -> OverflowRisk:
        """检查溢出风险"""
        
        signal, expr = assign
        
        # 检查是否是溢出风险类型
        
        # 1. data = data + 1 (无检查的累加)
        if re.search(r'\1\s*\+\s*1\b', expr) and 'if' not in expr:
            return OverflowRisk(
                signal=signal,
                expression=expr,
                risk_level='HIGH',
                description='Unchecked increment (data+1), may overflow',
                suggestion='Add overflow check or use saturating counter'
            )
        
        # 2. data = data + addend (无边界检查)
        if re.search(r'\1\s*\+\s*\w+', expr) and 'if' not in expr and '{' not in expr:
            return OverflowRisk(
                signal=signal,
                expression=expr,
                risk_level='MEDIUM',
                description='Unchecked addition, may overflow at boundary',
                suggestion='Add boundary check or condition for overflow'
            )
        
        # 3. data = data - 1 (无检查的递减)
        if re.search(r'\1\s*-\s*1\b', expr) and 'if' not in expr:
            return OverflowRisk(
                signal=signal,
                expression=expr,
                risk_level='HIGH',
                description='Unchecked decrement, may underflow',
                suggestion='Add underflow check'
            )
        
        return None
    
    def _get_code(self, fname: str) -> str:
        if fname in self.parser.trees:
            t = self.parser.trees[fname]
            if hasattr(t, 'source'):
                return t.source
        try:
            with open(fname) as f:
                return f.read()
        except:
            return ""


def detect_overflow(parser) -> OverflowResult:
    detector = OverflowRiskDetector(parser)
    return detector.detect()
