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
                # assign 可以是 (target, expr) 或 (target, expr, ptype)
                if len(assign) == 3:
                    target, expr, ptype = assign
                else:
                    target, expr = assign
                    ptype = 'add' if '+' in expr else 'sub'
                # 检查是否有溢出风险
                risk = self._check_overflow(target, expr, ptype)
                if risk:
                    result.risks.append(risk)
        
        return result
    
    def _find_add_sub_assignments(self, code: str) -> List:
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
    
    def _check_overflow(self, signal: str, expr: str, ptype: str = 'add') -> OverflowRisk:
        """检查溢出风险
        
        Args:
            signal: 信号名
            expr: 表达式
            ptype: 类型 ('add', 'sub', 'mul', 'shl')
        """
        
        signal = signal
        
        # 检查是否是溢出风险类型
        
        # 1. data = data + 1 (无检查的累加)
        if re.search(r'[\w]+\s*\+\s*1\b', expr) and 'if' not in expr:
            return OverflowRisk(
                signal=signal,
                expression=expr,
                risk_level='HIGH',
                description='Unchecked increment (data+1), may overflow',
                suggestion='Add overflow check or use saturating counter'
            )
        
        # 2. data = data + addend (无边界检查)
        if re.search(r'[\w]+\s*\+\s*\w+', expr) and 'if' not in expr and '{' not in expr:
            return OverflowRisk(
                signal=signal,
                expression=expr,
                risk_level='MEDIUM',
                description='Unchecked addition, may overflow at boundary',
                suggestion='Add boundary check or condition for overflow'
            )
        
        # 3. data = data - 1 (无检查的递减)
        if re.search(r'[\w]+\s*-\s*1\b', expr) and 'if' not in expr:
            return OverflowRisk(
                signal=signal,
                expression=expr,
                risk_level='HIGH',
                description='Unchecked decrement, may underflow',
                suggestion='Add underflow check'
            )
        
        return None
    
    def _get_code(self, fname: str) -> str:
        # Try to read from file path
        try:
            # 尝试原始路径
            if os.path.exists(fname):
                with open(fname) as f:
                    return f.read()
            # 尝试 basename
            basename = os.path.basename(fname)
            if os.path.exists(basename):
                with open(basename) as f:
                    return f.read()
            # 尝试 /tmp 目录
            if fname.startswith('/tmp') or fname.startswith('/var'):
                # 这是临时文件，需要在解析后立即读取
                pass
        except Exception as e:
            print(f'Error reading {fname}: {e}')
        
        # 最后尝试: 从 tree 获取文本
        if fname in self.parser.trees:
            tree = self.parser.trees[fname]
            # 尝试通过 str() 获取
            try:
                return str(tree)
            except:
                pass
        
        return ""


def detect_overflow(parser) -> OverflowResult:
    detector = OverflowRiskDetector(parser)
    return detector.detect()
