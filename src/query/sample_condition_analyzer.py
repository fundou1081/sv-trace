"""
SampleConditionAnalyzer - 采样条件智能识别
用户在写coverage时需要知道信号什么时候稳定，根据什么条件进行sample
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SampleCondition:
    """采样条件"""
    signal: str
    clock_edge: str = "posedge"      # posedge/negedge
    condition: str = ""              # 额外条件 e.g. valid==1
    is_valid_ready: bool = False
    is_conditional: bool = False
    
    def to_string(self) -> str:
        if self.condition:
            return f"@({self.clock_edge} {self.signal}) iff ({self.condition})"
        return f"@({self.clock_edge} {self.signal})"


@dataclass
class SampleResult:
    """采样分析结果"""
    signal: str
    sample_conditions: List[SampleCondition] = field(default_factory=list)
    recommended: Optional[SampleCondition] = None
    alternatives: List[SampleCondition] = field(default_factory=list)
    
    def visualize(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"SAMPLE ANALYSIS: {self.signal}")
        lines.append("=" * 60)
        
        lines.append(f"\n📋 Found {len(self.sample_conditions)} conditions:")
        
        for i, sc in enumerate(self.sample_conditions, 1):
            rec = "★" if sc == self.recommended else " "
            lines.append(f"\n{rec} {i}. {sc.to_string()}")
        
        if self.recommended:
            lines.append(f"\n✅ Recommended: {self.recommended.to_string()}")
        
        if self.alternatives:
            lines.append(f"\n📋 Alternatives:")
            for alt in self.alternatives:
                lines.append(f"  - {alt.to_string()}")
        
        lines.append("=" * 60)
        return '\n'.join(lines)


class SampleConditionAnalyzer:
    """采样条件分析器"""
    
    # 常见valid/ready关键字
    VALID_KW = ['valid', 'vld', 'v', 'data_valid']
    READY_KW = ['ready', 'rdy', 'r', 'data_ready']
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self, signal: str, module: str = None) -> SampleResult:
        """分析信号的采样条件"""
        
        result = SampleResult(signal=signal)
        
        # 从代码中查找相关信号及采样条件
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            if not code:
                continue
            
            # 1. 找always_ff块
            for line in code.split('\n'):
                stripped = line.strip()
                
                # 检测 @(posedge signal) 或 @(negedge signal)
                edge_match = re.search(r'@\(pos?edge\s+(\w+)', stripped)
                if edge_match:
                    clock_sig = edge_match.group(1)
                    
                    # 检测always_ff块中的赋值
                    if 'always_ff' in stripped:
                        result.sample_conditions.append(SampleCondition(
                            signal=signal,
                            clock_edge='posedge',
                            condition=''
                        ))
                
                # 2. 检测valid/ready握手采样
                pattern = rf'(\w*{signal}\w*)\s*(?:<=|<)\s*\w*.*?(?:@\(|\bif\b)'
                if re.search(pattern, line):
                    # 检查有没有valid条件
                    for kw in self.VALID_KW:
                        if kw in line.lower():
                            result.sample_conditions.append(SampleCondition(
                                signal=signal,
                                clock_edge='posedge',
                                condition=f'{kw}==1',
                                is_valid_ready=True
                            ))
                    
                    # 检查有没有ready条件
                    for kw in self.READY_KW:
                        if kw in line.lower():
                            result.sample_conditions.append(SampleCondition(
                                signal=signal,
                                condition=f'{kw}==1',
                                is_conditional=True
                            ))
        
        # 3. 如果没有找到，添加默认
        if not result.sample_conditions:
            result.sample_conditions.append(SampleCondition(
                signal=signal,
                clock_edge='posedge'
            ))
        
        # 4. 设置推荐
        result.recommended = self._select_recommended(result.sample_conditions)
        
        # 5. 设置备选
        if len(result.sample_conditions) > 1:
            result.alternatives = [c for c in result.sample_conditions 
                               if c != result.recommended][:3]
        
        return result
    
    def _select_recommended(self, conditions: List[SampleCondition]) -> SampleCondition:
        """选择最合适的采样条件"""
        
        # 优先级:
        # 1. valid_ready 条件
        # 2. 有额外条件
        # 3. 默认
        
        for c in conditions:
            if c.is_valid_ready:
                return c
        
        for c in conditions:
            if c.condition:
                return c
        
        return conditions[0] if conditions else SampleCondition(signal="")
    
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


def analyze_sample_condition(parser, signal: str) -> SampleResult:
    analyzer = SampleConditionAnalyzer(parser)
    return analyzer.analyze(signal)
